"""A fixed Vulkan development comparison using the existing evaluation scorer and reports."""

import argparse
import json
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path
from time import perf_counter

from researchlens.artifacts import canonical_hash, load_artifact
from researchlens.evaluation import (
    comparison_report,
    default_retrieval_config,
    encoded,
    load_dataset,
    review_template,
    run_evaluation,
    validate_artifact,
    validate_splits,
)
from researchlens.evaluation_evidence import EvidenceLabels, validate_labels
from researchlens.evaluation_schema import ExecutionConfig
from researchlens.ingest import ROOT, TECHNICAL_CORPUS
from researchlens.reranking import RerankedRetriever
from researchlens.retrieval import load_retriever
from researchlens.vulkan_reranking import VulkanReranker, metadata


def plan() -> list[dict]:
    return [
        {"name": f"{model}-dense", "model": model, "reranker": None, "candidates": None}
        for model in ("qwen3-4b", "bge-m3")
    ] + [
        {
            "name": f"{model}-{reranker}-rerank{count}",
            "model": model,
            "reranker": reranker,
            "candidates": count,
        }
        for model in ("qwen3-4b", "bge-m3")
        for reranker in ("bge", "qwen")
        for count in (20, 40)
    ]


def inputs(args):
    dataset = load_dataset(args.dataset)
    other = load_dataset(args.other_split)
    if dataset.split != "development" or any(c.review_status != "approved" for c in dataset.cases):
        raise ValueError("Use approved development questions only")
    validate_splits(dataset, other)
    labels = EvidenceLabels.model_validate_json(args.evidence_labels.read_bytes())
    if labels.review_status != "approved":
        raise ValueError("Use separately approved development evidence labels")
    artifacts = {}
    for model in ("qwen3-4b", "bge-m3"):
        artifact, passages = load_artifact(args.indexes / f"{model}.json", source=TECHNICAL_CORPUS)
        validate_artifact(dataset, artifact)
        validate_labels(labels, dataset, artifact, passages)
        artifacts[model] = artifact
    return dataset, labels, artifacts


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
        retriever = base
        if entry["reranker"]:
            reranker = resources.enter_context(
                VulkanReranker(args.runtime, entry["reranker"], output / "server.log")
            )
            retriever = RerankedRetriever(base, reranker, candidates=entry["candidates"])
        config = default_retrieval_config(
            "embeddings",
            artifacts[entry["model"]],
            f"{type(retriever).__module__}.{type(retriever).__name__}",
            retriever,
        )
        execution = ExecutionConfig(
            repeats=args.repeats,
            warmups=1,
            measure_memory=True,
            index_load_time_ms=1000 * (perf_counter() - started),
        )
        result = run_evaluation(
            dataset,
            artifacts[entry["model"]],
            retriever,
            config,
            execution=execution,
            evidence_labels=labels,
            cutoffs=[1, 4],
        )
        if entry["reranker"]:
            (output / "server-memory.json").write_text(
                json.dumps({
                    "scope": "owned llama-server Windows counters; excludes Python and VRAM",
                    "sampling": (
                        "startup and before/after each HTTP request; native high-water counters"
                    ),
                    "samples": reranker.memory_samples,
                }, indent=2) + "\n", encoding="utf-8",
            )
        (output / "run.json").write_bytes(encoded(result))
        (output / "review.json").write_bytes(
            encoded(review_template(result).model_dump(mode="json"))
        )
        (output / "report.md").write_text(comparison_report([result], [None]), encoding="utf-8")
        print(f"Saved {len(result['results'])} development cases: {entry['name']}", flush=True)
        if any(row["error"] for row in result["results"]):
            raise ValueError("Run contains case errors; inspect run.json")


def compare(args):
    dataset, labels, artifacts = inputs(args)
    runtime = {alias: metadata(args.runtime, alias) for alias in ("bge", "qwen")}
    execution = ExecutionConfig(repeats=args.repeats, warmups=1, measure_memory=True)
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "plan": plan(),
        "plan_sha256": canonical_hash(plan()),
        "dataset_sha256": canonical_hash(dataset.model_dump(mode="json")),
        "evidence_labels_sha256": canonical_hash(labels.model_dump(mode="json")),
        "artifact_hashes": {k: canonical_hash(v) for k, v in artifacts.items()},
        "runtime": runtime,
        "execution": execution.model_dump(),
        "limit": 4,
        "cutoffs": [1, 4],
        "stages": [],
        "api_calls": 0,
        "selection_rule": "Complete evidence@4, cohort regressions, then latency; development only",
        "held_out_retrieval": False,
    }

    def save():
        (args.output / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    save()  # Immutable settings and inputs are recorded before any question executes.
    for entry in plan():
        print(f"Starting {entry['name']}", flush=True)
        started = perf_counter()
        with (args.output / f"{entry['name']}-process.log").open("w", encoding="utf-8") as log:
            try:
                child = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "researchlens.vulkan_experiments",
                        "--single",
                        entry["name"],
                        "--runtime",
                        str(args.runtime.resolve()),
                        "--indexes",
                        str(args.indexes.resolve()),
                        "--output",
                        str(args.output.resolve()),
                        "--dataset",
                        str(args.dataset.resolve()),
                        "--other-split",
                        str(args.other_split.resolve()),
                        "--evidence-labels",
                        str(args.evidence_labels.resolve()),
                        "--repeats",
                        str(args.repeats),
                    ],
                    cwd=ROOT / "backend",
                    stdout=log,
                    stderr=log,
                    timeout=1800,
                    check=False,
                )
                status = "completed" if child.returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                status = "timeout"
        manifest["stages"].append(
            {
                "name": entry["name"],
                "status": status,
                "duration_ms": 1000 * (perf_counter() - started),
            }
        )
        save()
        print(f"{entry['name']}: {status}", flush=True)
    successful = [args.output / e["name"] for e in manifest["stages"] if e["status"] == "completed"]
    if successful:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "researchlens.evaluation",
                "report",
                *map(str, successful),
                "--output",
                str(args.output / "comparison.md"),
                "--paired-output",
                str(args.output / "paired.json"),
            ],
            check=True,
        )
    if len(successful) != len(plan()):
        raise ValueError("Some predefined configurations failed; no automatic retries")


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
    # Resolve once; child processes have a different working directory.
    for key in ("runtime", "indexes", "output", "dataset", "other_split", "evidence_labels"):
        setattr(args, key, getattr(args, key).resolve())
    try:
        single(args) if args.single else compare(args)
    except (OSError, ValueError, subprocess.CalledProcessError):
        parser.exit(1, "Vulkan experiment failed; inspect input bindings and local logs.\n")


if __name__ == "__main__":
    main()
