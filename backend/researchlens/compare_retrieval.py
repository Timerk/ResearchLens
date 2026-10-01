"""Run local model/mode comparisons through the existing evaluation CLI, in fresh processes."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter

from researchlens.embedding_models import MODELS
from researchlens.evaluation import load_dataset, validate_splits
from researchlens.ingest import ROOT, TECHNICAL_CORPUS


def compare(
    output: Path,
    *,
    models: list[str],
    source: Path,
    dataset: Path,
    other_split: Path,
    repeats: int = 5,
    warmups: int = 1,
    limit: int = 4,
    stage_timeout: int = 3600,
) -> dict:
    if not models or len(set(models)) != len(models) or any(name not in MODELS for name in models):
        raise ValueError("Select unique supported embedding model aliases")
    if repeats < 1 or warmups < 0 or limit < 1 or stage_timeout < 1:
        raise ValueError("Invalid comparison limits")
    development, other = load_dataset(dataset), load_dataset(other_split)
    if development.split != "development":
        raise ValueError("Model comparison/tuning must use development questions")
    validate_splits(development, other)
    output.mkdir(parents=True, exist_ok=False)
    indexes = output / "indexes"
    indexes.mkdir()
    manifest = {
        "schema_version": 1,
        "models": models,
        "repeats": repeats,
        "warmups": warmups,
        "limit": limit,
        "stage_timeout_seconds": stage_timeout,
        "stages": [],
        "api_calls": 0,
        "generation": "none",
    }

    def save() -> None:
        (output / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    def execute(label: str, module: str, arguments: list[str]) -> float | None:
        print(f"Starting {label}", flush=True)
        started = perf_counter()
        code = "completed"
        try:
            result = subprocess.run(
                [sys.executable, "-m", module, *arguments],
                cwd=ROOT / "backend",
                capture_output=True,
                timeout=stage_timeout,
                check=False,
            )
            if result.returncode != 0:
                code = "process_failed"
        except subprocess.TimeoutExpired:
            code = "timeout"
        elapsed = round((perf_counter() - started) * 1000, 3)
        # Never save child output/exception strings: upstream details may contain secrets.
        manifest["stages"].append({"label": label, "status": code, "duration_ms": elapsed})
        save()
        print(f"{label}: {code} ({elapsed / 1000:.2f}s)", flush=True)
        return elapsed if code == "completed" else None

    successful = []
    for alias in ["tfidf", *models]:
        index = indexes / f"{alias}.json"
        args = ["--source", str(source.resolve()), "--destination", str(index.resolve())]
        if alias != "tfidf":
            args += ["--retrieval", "embeddings", "--embedding-model", alias]
        else:
            args += ["--retrieval", "tfidf"]
        duration = execute(f"{alias}/ingestion", "researchlens.ingest", args)
        if duration is None:
            continue
        for mode in ["tfidf"] if alias == "tfidf" else ["embeddings", "hybrid"]:
            run_dir = output / f"{alias}-{mode}"
            arguments = [
                "run",
                "--dataset",
                str(dataset.resolve()),
                "--other-split",
                str(other_split.resolve()),
                "--source",
                str(source.resolve()),
                "--index",
                str(index.resolve()),
                "--retriever",
                mode,
                "--output",
                str(run_dir.resolve()),
                "--limit",
                str(limit),
                "--repeats",
                str(repeats),
                "--warmups",
                str(warmups),
                "--measure-memory",
                "--ingestion-time-ms",
                str(duration),
            ]
            completed = execute(f"{alias}/{mode}", "researchlens.evaluation", arguments)
            if completed is not None:
                successful.append(run_dir)
    if successful:
        execute(
            "comparison/report",
            "researchlens.evaluation",
            [
                "report",
                *(str(path.resolve()) for path in successful),
                "--output",
                str((output / "comparison.md").resolve()),
            ],
        )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--models", nargs="+", choices=list(MODELS), default=list(MODELS))
    parser.add_argument("--source", type=Path, default=TECHNICAL_CORPUS)
    parser.add_argument(
        "--dataset", type=Path, default=ROOT / "evaluation/datasets/technical-development.json"
    )
    parser.add_argument(
        "--other-split", type=Path, default=ROOT / "evaluation/datasets/held-out.json"
    )
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--stage-timeout-seconds", type=int, default=3600)
    args = parser.parse_args()
    try:
        manifest = compare(
            args.output,
            models=args.models,
            source=args.source,
            dataset=args.dataset,
            other_split=args.other_split,
            repeats=args.repeats,
            warmups=args.warmups,
            limit=args.limit,
            stage_timeout=args.stage_timeout_seconds,
        )
    except (OSError, ValueError):
        parser.exit(2, "Comparison failed: check input paths, splits and fresh output directory.\n")
    if any(stage["status"] != "completed" for stage in manifest["stages"]):
        parser.exit(1, "Comparison saved with failed stages; inspect manifest.json.\n")


if __name__ == "__main__":
    main()
