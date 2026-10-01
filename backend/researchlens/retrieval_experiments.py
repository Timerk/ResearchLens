"""Predefined development-only experiments delegated to the existing evaluation runner."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter

from researchlens.artifacts import canonical_hash, load_artifact
from researchlens.evaluation import (
    default_retrieval_config,
    load_dataset,
    validate_artifact,
    validate_splits,
)
from researchlens.evaluation_evidence import EvidenceLabels, validate_labels
from researchlens.evaluation_schema import ExecutionConfig, RetrievalConfig
from researchlens.ingest import ROOT, TECHNICAL_CORPUS
from researchlens.reranking import reranker_metadata
from researchlens.retrieval import HYBRID_DEFAULTS


def experiment_plan() -> list[dict]:
    configurations = [{"name": "tfidf", "model": "tfidf", "backend": "tfidf"}]
    configurations += [
        {"name": f"{model}-dense", "model": model, "backend": "embeddings"}
        for model in ("minilm", "qwen3-0.6b")
    ]
    for model in ("bge-m3", "qwen3-4b"):
        configurations.append({"name": f"{model}-dense", "model": model, "backend": "embeddings"})
        for count, lexical in ((20, 0.5), (40, 0.5), (40, 0.25), (40, 0.75)):
            configurations.append(
                {
                    "name": f"{model}-hybrid{count}-lex{int(100 * lexical)}",
                    "model": model,
                    "backend": "hybrid",
                    "hybrid": {
                        **HYBRID_DEFAULTS,
                        "lexical_candidates": count,
                        "embedding_candidates": count,
                        "lexical_weight": lexical,
                        "embedding_weight": 1 - lexical,
                    },
                }
            )
        for candidates, diversity in ((20, 0.0), (40, 0.0), (40, 0.2)):
            configurations.append(
                {
                    "name": f"{model}-dense-rerank{candidates}-div{int(100 * diversity)}",
                    "model": model,
                    "backend": "embeddings",
                    "reranker": {
                        **reranker_metadata(),
                        "candidates": candidates,
                        "diversity": diversity,
                    },
                }
            )
        configurations.append(
            {
                "name": f"{model}-hybrid40-lex25-rerank40",
                "model": model,
                "backend": "hybrid",
                "hybrid": {
                    **HYBRID_DEFAULTS,
                    "lexical_candidates": 40,
                    "embedding_candidates": 40,
                    "lexical_weight": 0.25,
                    "embedding_weight": 0.75,
                },
                "reranker": {**reranker_metadata(), "candidates": 40, "diversity": 0.0},
            }
        )
    return configurations


def compare(
    output: Path,
    indexes: Path,
    *,
    dataset: Path,
    other_split: Path,
    evidence_labels: Path,
    source: Path = TECHNICAL_CORPUS,
    repeats: int = 5,
    warmups: int = 1,
    stage_timeout: int = 3600,
) -> dict:
    development, held_out = load_dataset(dataset), load_dataset(other_split)
    if development.split != "development" or any(
        case.review_status != "approved" for case in development.cases
    ):
        raise ValueError("Experiments require approved development questions")
    validate_splits(development, held_out)
    execution = ExecutionConfig(repeats=repeats, warmups=warmups, measure_memory=True)
    if stage_timeout < 1:
        raise ValueError("Stage timeout must be positive")
    labels = EvidenceLabels.model_validate_json(evidence_labels.read_bytes())
    if labels.review_status != "approved":
        raise ValueError("Experiments require approved evidence labels")
    plan = experiment_plan()
    artifacts = {}
    configs = {}
    # Validate every shared input before starting a model or writing a result directory.
    for model in {entry["model"] for entry in plan}:
        artifact, passages = load_artifact(indexes / f"{model}.json", source=source)
        validate_artifact(development, artifact)
        validate_labels(labels, development, artifact, passages)
        artifacts[model] = artifact
    for entry in plan:
        implementation = (
            "researchlens.reranking.RerankedRetriever"
            if entry.get("reranker")
            else (
                "researchlens.retrieval.HybridRetriever"
                if entry["backend"] == "hybrid"
                else "researchlens.retrieval.EmbeddingRetriever"
                if entry["backend"] == "embeddings"
                else "researchlens.retrieval.TfidfRetriever"
            )
        )
        config = default_retrieval_config(
            entry["backend"], artifacts[entry["model"]], implementation
        ).model_dump()
        config.update(entry.get("hybrid", {}))
        config["reranker"] = entry.get("reranker")
        config["limit"] = min(40, (entry.get("reranker") or {}).get("candidates", 40))
        configs[entry["name"]] = RetrievalConfig.model_validate(config)
    output.mkdir(parents=True, exist_ok=False)
    (output / "configs").mkdir()
    manifest = {
        "schema_version": 1,
        "plan": plan,
        "plan_sha256": canonical_hash(plan),
        "execution": execution.model_dump(),
        "context_budgets": [4, 6, 8],
        "context_max_passage_chars": 3000,
        "context_max_serialized_chars": 16000,
        "dataset_path": str(dataset),
        "dataset_sha256": labels.dataset_sha256,
        "evidence_labels_sha256": canonical_hash(labels.model_dump(mode="json")),
        "stages": [],
        "api_calls": 0,
        "generation": "none",
        "selection": "predefined development grid; no held-out retrieval",
    }

    def execute(label: str, module: str, arguments: list[str]) -> bool:
        print(f"Starting {label}", flush=True)
        started = perf_counter()
        try:
            process = subprocess.run(
                [sys.executable, "-m", module, *arguments],
                cwd=ROOT / "backend",
                capture_output=True,
                timeout=stage_timeout,
                check=False,
            )
            status = "completed" if process.returncode == 0 else "process_failed"
        except subprocess.TimeoutExpired:
            status = "timeout"
        manifest["stages"].append(
            {
                "label": label,
                "status": status,
                "duration_ms": round((perf_counter() - started) * 1000, 3),
            }
        )
        (output / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{label}: {status}", flush=True)
        return status == "completed"

    # Save the complete planned grid before executing the first question.
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    successful = []
    for entry in plan:
        name, config = entry["name"], configs[entry["name"]]
        config_path = output / "configs" / f"{name}.json"
        config_path.write_text(config.model_dump_json(indent=2) + "\n", encoding="utf-8")
        run_dir = output / name
        cutoffs = sorted({1, 4, 10, 20, config.limit})
        if execute(
            name,
            "researchlens.evaluation",
            [
                "run",
                "--dataset",
                str(dataset.resolve()),
                "--other-split",
                str(other_split.resolve()),
                "--source",
                str(source.resolve()),
                "--index",
                str((indexes / f"{entry['model']}.json").resolve()),
                "--retriever",
                entry["backend"],
                "--retrieval-config",
                str(config_path.resolve()),
                "--evidence-labels",
                str(evidence_labels.resolve()),
                "--limit",
                str(config.limit),
                "--cutoffs",
                *map(str, cutoffs),
                "--repeats",
                str(repeats),
                "--warmups",
                str(warmups),
                "--measure-memory",
                "--output",
                str(run_dir.resolve()),
            ],
        ):
            successful.append(run_dir)
            execute(
                f"{name}/analysis",
                "researchlens.retrieval_analysis",
                [
                    str((run_dir / "run.json").resolve()),
                    "--output",
                    str((run_dir / "analysis.json").resolve()),
                ],
            )
    if successful:
        execute(
            "comparison/report",
            "researchlens.evaluation",
            [
                "report",
                *(str(path.resolve()) for path in successful),
                "--output",
                str((output / "comparison.md").resolve()),
                "--paired-output",
                str((output / "paired.json").resolve()),
            ],
        )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--indexes", type=Path, required=True, help="Existing five pinned model artifacts"
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
    parser.add_argument("--source", type=Path, default=TECHNICAL_CORPUS)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    args = parser.parse_args()
    try:
        manifest = compare(
            args.output,
            args.indexes,
            dataset=args.dataset,
            other_split=args.other_split,
            evidence_labels=args.evidence_labels,
            source=args.source,
            repeats=args.repeats,
            warmups=args.warmups,
        )
    except (OSError, ValueError):
        parser.exit(
            2,
            "Experiment inputs are invalid; check approved development labels "
            "and existing artifacts.\n",
        )
    if any(stage["status"] != "completed" for stage in manifest["stages"]):
        parser.exit(1, "Experiments contain failed stages; inspect manifest.json.\n")


if __name__ == "__main__":
    main()
