"""Predefined development-only selection study using the shared evaluation runner."""

import argparse
import hashlib
import subprocess
from contextlib import ExitStack
from pathlib import Path
from time import perf_counter

from researchlens.artifacts import canonical_hash, load_artifact
from researchlens.evaluation import (
    comparison_report,
    default_retrieval_config,
    encoded,
    review_template,
    run_evaluation,
)
from researchlens.evaluation_evidence import ranking_metrics
from researchlens.evaluation_schema import ExecutionConfig
from researchlens.evidence_selection import EvidenceSelector, QuestionDecomposer
from researchlens.ingest import ROOT, TECHNICAL_CORPUS
from researchlens.reranking import RerankedRetriever
from researchlens.retrieval import load_retriever
from researchlens.vulkan_experiments import compare, inputs
from researchlens.vulkan_reranking import VulkanReranker


def plan():
    return [
        {"name": "qwen3-4b-dense", "model": "qwen3-4b", "selector": False, "reranker": False},
        {"name": "bge-m3-dense", "model": "bge-m3", "selector": False, "reranker": False},
        {"name": "bge-m3-bge20", "model": "bge-m3", "selector": False, "reranker": True},
        *[
            {
                "name": f"{model}-facets-dense",
                "model": model,
                "selector": True,
                "reranker": False,
                "decompose": True,
                "representation": "passage-text-only",
            }
            for model in ("qwen3-4b", "bge-m3")
        ],
        {
            "name": "bge-m3-bge20-metadata",
            "model": "bge-m3",
            "selector": True,
            "reranker": True,
            "decompose": False,
            "representation": "title-section-text-v1",
        },
        *[
            {
                "name": f"bge-m3-facets-bge40-{name}",
                "model": "bge-m3",
                "selector": True,
                "reranker": True,
                "decompose": True,
                "representation": representation,
            }
            for name, representation in (
                ("plain", "passage-text-only"),
                ("metadata", "title-section-text-v1"),
            )
        ],
    ]


class RecordingSearch:
    """Transparent observer; records searches without caching inference or using labels."""

    def __init__(self, adapter):
        self.adapter = adapter
        self.records = {}

    def __getattr__(self, name):
        return getattr(self.adapter, name)

    def search(self, question, limit):
        hits = self.adapter.search(question, limit)
        self.records[hashlib.sha256(question.encode()).hexdigest()] = self.adapter.last_selection
        return hits


def single(args):
    dataset, labels, artifacts = inputs(args)
    entry = next(e for e in plan() if e["name"] == args.single)
    output = args.output / entry["name"]
    output.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    with ExitStack() as resources:
        base = load_retriever(
            "embeddings", args.indexes / f"{entry['model']}.json", source=TECHNICAL_CORPUS
        )
        reranker = None
        if entry["reranker"]:
            reranker = resources.enter_context(
                VulkanReranker(args.runtime, "bge", output / "server.log")
            )
        if entry["selector"]:
            adapter = EvidenceSelector(
                base,
                reranker,
                decompose=entry["decompose"],
                complementary=entry["decompose"],
                representation=entry["representation"],
                candidates=40 if entry["decompose"] else 20,
                per_query=20,
            )
            retriever = RecordingSearch(adapter)
        else:
            adapter = RerankedRetriever(base, reranker, candidates=20) if reranker else base
            retriever = adapter
        config = default_retrieval_config(
            "embeddings",
            artifacts[entry["model"]],
            f"{type(adapter).__module__}.{type(adapter).__name__}",
            adapter,
        )
        result = run_evaluation(
            dataset,
            artifacts[entry["model"]],
            retriever,
            config,
            execution=ExecutionConfig(
                repeats=args.repeats,
                warmups=1,
                measure_memory=True,
                index_load_time_ms=1000 * (perf_counter() - started),
            ),
            evidence_labels=labels,
            cutoffs=[1, 4],
        )
        if entry["selector"]:
            by_id = {p.id: p for p in base.passages}
            by_case = {c.case_id: c for c in labels.cases}
            diagnostics = []
            for case in dataset.cases:
                record = retriever.records.get(hashlib.sha256(case.question.encode()).hexdigest())
                if record is None:
                    diagnostics.append({"case_id": case.id, "error": "search_not_completed"})
                    continue
                candidates = [by_id[i] for i in record["candidate_ids"]]
                diagnostics.append(
                    {
                        "case_id": case.id,
                        **record,
                        "actual_candidate_count": len(candidates),
                        "candidate_metrics": {
                            str(k): ranking_metrics(case, candidates[:k], by_case.get(case.id))
                            for k in (20, 40)
                        },
                    }
                )
            (output / "selection.json").write_bytes(encoded({"cases": diagnostics}))
        if reranker:
            (output / "server-memory.json").write_bytes(
                encoded(
                    {
                        "scope": "owned llama-server Windows counters; excludes Python and VRAM",
                        "sampling": (
                            "startup and before/after each request; native high-water counters"
                        ),
                        "samples": reranker.memory_samples,
                    }
                )
            )
        (output / "run.json").write_bytes(encoded(result))
        (output / "review.json").write_bytes(
            encoded(review_template(result).model_dump(mode="json"))
        )
        (output / "report.md").write_text(comparison_report([result], [None]), encoding="utf-8")
        print(f"Saved {len(result['results'])} development cases: {entry['name']}", flush=True)
        if any(row["error"] for row in result["results"]):
            raise ValueError("Run contains case errors; inspect run.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--indexes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--single", choices=[e["name"] for e in plan()])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--dataset", type=Path, default=ROOT / "evaluation/datasets/technical-development.json"
    )
    parser.add_argument(
        "--other-split", type=Path, default=ROOT / "evaluation/datasets/held-out.json"
    )
    parser.add_argument(
        "--evidence-labels",
        type=Path,
        default=ROOT / "evaluation/labels/technical-development.json",
    )
    args = parser.parse_args()
    for key in ("runtime", "indexes", "output", "dataset", "other_split", "evidence_labels"):
        setattr(args, key, getattr(args, key).resolve())
    try:
        if args.single:
            single(args)
        else:
            _, passages = load_artifact(args.indexes / "bge-m3.json", source=TECHNICAL_CORPUS)
            provenance = {
                "document_profile_sha256": QuestionDecomposer(passages).profile_sha256,
                "source_sha256": {
                    name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                    for name in (
                        "selection_experiments.py",
                        "evidence_selection.py",
                        "vulkan_experiments.py",
                        "evaluation_schema.py",
                        "evaluation.py",
                    )
                },
                "selector": {
                    "original_weight": 0.5,
                    "rank_constant": 10,
                    "max_queries": 3,
                    "per_query": 20,
                    "max_candidates": 40,
                },
                "provenance_sha256": canonical_hash(plan()),
                "embedding_representation": "unchanged canonical passage text",
            }
            compare(args, plan(), "researchlens.selection_experiments", provenance)
    except (OSError, ValueError, subprocess.CalledProcessError):
        parser.exit(1, "Selection experiment failed; inspect local logs and input bindings.\n")


if __name__ == "__main__":
    main()
