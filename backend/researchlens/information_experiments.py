"""Fixed-pool development ablations using frozen local-model outputs and the shared scorer."""

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

import httpx
import numpy as np

from researchlens.artifacts import canonical_hash, load_artifact
from researchlens.evaluation import (
    comparison_report,
    default_retrieval_config,
    encoded,
    review_template,
    run_evaluation,
)
from researchlens.evaluation_schema import ExecutionConfig
from researchlens.evidence_selection import QuestionDecomposer
from researchlens.information_selection import POLICIES, FixedPoolSelector
from researchlens.ingest import ROOT, TECHNICAL_CORPUS
from researchlens.local_needs import LocalNeeds
from researchlens.models import SearchHit
from researchlens.vulkan_experiments import inputs
from researchlens.vulkan_reranking import VulkanReranker


def source_hashes():
    return {
        name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
        for name in (
            "information_experiments.py",
            "information_selection.py",
            "local_needs.py",
            "evaluation.py",
            "evaluation_schema.py",
            "vulkan_reranking.py",
            "representation_experiments.py",
        )
    }


def baseline_cases(path, dataset, artifact, passages):
    run = json.loads(path.read_bytes())
    if (
        run["dataset"] != dataset.model_dump(mode="json")
        or run["corpus"]["artifact_sha256"] != canonical_hash(artifact)
        or run["retrieval"]["limit"] != 40
    ):
        raise ValueError("Use the unchanged approved Qwen3-4B top-40 development run")
    by_id = {p.id: p for p in passages}
    cases = {}
    for row in run["results"]:
        hits = [SearchHit.model_validate(p) for p in row["retrieved_passages"]]
        if (
            row["error"]
            or len(hits) != 40
            or len({h.id for h in hits}) != 40
            or row["ranking_stable_across_repeats"] is not True
        ):
            raise ValueError("Fixed pool requires 40 successful stable canonical candidates")
        if any(h.model_dump(exclude={"score"}) != by_id[h.id].model_dump() for h in hits):
            raise ValueError("Fixed candidates differ from canonical passages")
        cases[row["case_id"]] = hits
    if set(cases) != {c.id for c in dataset.cases}:
        raise ValueError("Fixed candidate cases differ from development dataset")
    return run, cases


def measure(args):
    dataset, labels, artifacts = inputs(args)
    artifact, passages = load_artifact(args.indexes / "qwen3-4b.json", source=TECHNICAL_CORPUS)
    run, candidates = baseline_cases(args.baseline, dataset, artifact, passages)
    args.output.mkdir(parents=True, exist_ok=False)
    decomposer = QuestionDecomposer(passages)
    # Both owned servers are checked and loaded once; no CPU embedding model is needed.
    with LocalNeeds(args.runtime, args.assets, args.output / "needs-server.log") as needs:
        with VulkanReranker(args.runtime, "bge", args.output / "reranker-server.log") as reranker:
            manifest = {
                "plan": list(POLICIES),
                "source_hashes": source_hashes(),
                "dataset_sha256": canonical_hash(dataset.model_dump(mode="json")),
                "evidence_labels_sha256": canonical_hash(labels.model_dump(mode="json")),
                "artifact_sha256": canonical_hash(artifacts["qwen3-4b"]),
                "fixed_pool_run_sha256": hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
                "needs_model": needs.metadata,
                "reranker": reranker.metadata,
                "rules_profile_sha256": decomposer.profile_sha256,
                "selection": {
                    "max_rank_original_weight": 0.5,
                    "rank_constant": 10,
                    "saturation_original_weight": 0.25,
                    "cosine_penalty": 0.1,
                },
                "candidate_count": 40,
                "output_limit": 4,
                "held_out_searches": False,
                "api_calls": 0,
                "timing_scope": "staged inference plus replay-selection-only",
                "representation_plan": [
                    "passage-text-only",
                    "title-section-text-v1",
                    "title-section-current-neighbors60-v1",
                ],
            }
            (args.output / "manifest.json").write_bytes(encoded(manifest))
            bundle = {
                "manifest": manifest,
                "encoding_diagnostics": run["encoding_diagnostics"],
                "cases": [],
            }
            for number, case in enumerate(dataset.cases, 1):
                hits = candidates[case.id]
                row = {
                    "case_id": case.id,
                    "question_sha256": hashlib.sha256(case.question.encode()).hexdigest(),
                    "candidate_ids": [h.id for h in hits],
                    "dense_scores": [h.score for h in hits],
                    "error": None,
                    "need_queries": [],
                    "need_scores": [],
                    "rule_scores": [],
                }
                started = perf_counter()
                try:
                    row["need_queries"] = needs.extract(case.question)
                    row["needs_output"] = needs.last_record
                except (ValueError, httpx.HTTPError, KeyError, TypeError):
                    row["error"] = "invalid_or_failed_local_decomposition"
                row["decomposition_ms"] = 1000 * (perf_counter() - started)
                rules = [f.query for f in decomposer.split(case.question)[1:]]
                row["rule_queries"] = rules
                query_scores = {}
                query_times = {}
                pair_diagnostics = {}
                # Shared queries are measured once, explicitly outside replay timing.
                for query in dict.fromkeys([case.question, *rules, *row["need_queries"]]):
                    started = perf_counter()
                    query_scores[query] = reranker.score(query, hits).tolist()
                    query_times[query] = 1000 * (perf_counter() - started)
                    pair_diagnostics[query] = reranker.last_diagnostics
                row["original_scores"] = query_scores[case.question]
                row["original_pair_diagnostics"] = pair_diagnostics[case.question]
                row["rule_scores"] = [query_scores[q] for q in rules]
                row["need_scores"] = [query_scores[q] for q in row["need_queries"]]
                row["query_times_ms"] = query_times
                row["pair_diagnostics"] = pair_diagnostics
                bundle["cases"].append(row)
                (args.output / "measurements.json").write_bytes(encoded(bundle))
                print(
                    f"Measured {number}/{len(dataset.cases)}: {case.id}, "
                    f"needs={len(row['need_queries'])}, error={row['error']}",
                    flush=True,
                )
            (args.output / "server-memory.json").write_bytes(
                encoded(
                    {
                        "needs": needs.memory_samples,
                        "reranker": reranker.memory_samples,
                        "scope": "separate native server counters, excluding Python and VRAM",
                    }
                )
            )


def evaluate(args):
    dataset, labels, artifacts = inputs(args)
    artifact, passages = load_artifact(args.indexes / "qwen3-4b.json", source=TECHNICAL_CORPUS)
    bundle = json.loads((args.output / "measurements.json").read_bytes())
    manifest = bundle["manifest"]
    if (
        manifest["artifact_sha256"] != canonical_hash(artifact)
        or manifest["dataset_sha256"] != canonical_hash(dataset.model_dump(mode="json"))
        or manifest["evidence_labels_sha256"] != canonical_hash(labels.model_dump(mode="json"))
        or manifest["source_hashes"] != source_hashes()
    ):
        raise ValueError("Frozen measurements have stale source or input provenance")
    bundle_hash = canonical_hash(bundle)
    runs = []
    for policy in POLICIES:
        directory = args.output / policy
        directory.mkdir(exist_ok=False)
        adapter = FixedPoolSelector(
            bundle, passages, np.asarray(artifact["embeddings"]["vectors"]), policy, bundle_hash
        )
        config = default_retrieval_config(
            "embeddings",
            artifacts["qwen3-4b"],
            "researchlens.information_selection.FixedPoolSelector",
            adapter,
        )
        run = run_evaluation(
            dataset,
            artifact,
            adapter,
            config,
            execution=ExecutionConfig(repeats=3, warmups=1),
            evidence_labels=labels,
            cutoffs=[1, 4],
        )
        (directory / "run.json").write_bytes(encoded(run))
        (directory / "review.json").write_bytes(
            encoded(review_template(run).model_dump(mode="json"))
        )
        (directory / "report.md").write_text(comparison_report([run], [None]), encoding="utf-8")
        runs.append(run)
        print(f"Evaluated fixed-pool policy: {policy}", flush=True)
    (args.output / "comparison.md").write_text(
        comparison_report(runs, [None] * len(runs)), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("measure", "evaluate"))
    parser.add_argument("--runtime", type=Path, default=ROOT / ".venv/vulkan")
    parser.add_argument("--assets", type=Path, default=ROOT / ".venv/needs-model")
    parser.add_argument(
        "--indexes",
        type=Path,
        default=ROOT / "evaluation/runs/approved-models-2026-10-01-k4/indexes",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=ROOT / "evaluation/runs/retrieval-improvements-2026-10-02/qwen3-4b-dense/run.json",
    )
    parser.add_argument("--output", type=Path, required=True)
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
    for key in (
        "runtime",
        "assets",
        "indexes",
        "baseline",
        "output",
        "dataset",
        "other_split",
        "evidence_labels",
    ):
        setattr(args, key, getattr(args, key).resolve())
    measure(args) if args.stage == "measure" else evaluate(args)


if __name__ == "__main__":
    main()
