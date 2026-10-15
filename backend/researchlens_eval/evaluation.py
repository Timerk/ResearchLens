"""Offline-first evaluation: python -m researchlens.evaluation --help."""

import argparse
import json
from pathlib import Path
from time import perf_counter

from researchlens.answers import (
    LocalPreview,
)
from researchlens.artifacts import (
    load_artifact,
)
from researchlens.ingest import ROOT, TECHNICAL_CORPUS
from researchlens.retrieval import HYBRID_DEFAULTS, load_retriever

from researchlens_eval.answer_evaluation import add_answer_commands, answer_command
from researchlens_eval.context_evaluation import (
    STANDARD_BUDGETS,
)
from researchlens_eval.evaluation_core import code_state as code_state
from researchlens_eval.evaluation_core import digest as digest
from researchlens_eval.evaluation_core import encoded as encoded
from researchlens_eval.evaluation_core import load_dataset as load_dataset
from researchlens_eval.evaluation_core import validate_artifact as validate_artifact
from researchlens_eval.evaluation_core import (
    validate_dataset_references as validate_dataset_references,
)
from researchlens_eval.evaluation_core import validate_splits as validate_splits
from researchlens_eval.evaluation_evidence import (
    EncodingDiagnostics,
    EvidenceLabels,
)
from researchlens_eval.evaluation_metrics import (
    exact_mcnemar,
    paired_changes,
)
from researchlens_eval.evaluation_reporting import comparison_report as comparison_report
from researchlens_eval.evaluation_reporting import review_template as review_template
from researchlens_eval.evaluation_reporting import summarize as summarize
from researchlens_eval.evaluation_runner import Search as Search
from researchlens_eval.evaluation_runner import default_retrieval_config as default_retrieval_config
from researchlens_eval.evaluation_runner import encoding_settings as encoding_settings
from researchlens_eval.evaluation_runner import installed_versions as installed_versions
from researchlens_eval.evaluation_runner import run_evaluation as run_evaluation
from researchlens_eval.evaluation_runner import (
    validate_retrieval_config as validate_retrieval_config,
)
from researchlens_eval.evaluation_schema import (
    ExecutionConfig,
    GenerationConfig,
    RetrievalConfig,
    Review,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    add_answer_commands(commands)
    run = commands.add_parser("run", help="Free retrieval or local-preview evaluation")
    run.add_argument("--dataset", type=Path, required=True)
    run.add_argument("--other-split", type=Path, required=True)
    run.add_argument("--index", type=Path, default=ROOT / "data/index.json")
    run.add_argument("--source", type=Path, default=TECHNICAL_CORPUS)
    run.add_argument("--retriever", choices=["tfidf", "embeddings", "hybrid"], default="tfidf")
    run.add_argument(
        "--retrieval-config",
        type=Path,
        help="Strict RetrievalConfig JSON for settings missing from artifact metadata",
    )
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--limit", type=int)
    run.add_argument("--context-budgets", type=int, nargs="+", choices=STANDARD_BUDGETS)
    run.add_argument("--cutoffs", type=int, nargs="+", help="Ranking prefixes; use 1 4 10")
    run.add_argument(
        "--evidence-labels", type=Path, help="Pinned alternative/complete-evidence labels"
    )
    run.add_argument(
        "--encoding-diagnostics", type=Path, help="Measured encoder token/range sidecar"
    )
    run.add_argument("--repeats", type=int, default=1)
    run.add_argument("--warmups", type=int, default=0)
    run.add_argument("--measure-memory", action="store_true")
    run.add_argument(
        "--ingestion-time-ms",
        type=float,
        help="Externally measured ingestion duration; omitted means unknown",
    )
    run.add_argument(
        "--mode", choices=["retrieval-only", "local-preview"], default="retrieval-only"
    )
    report = commands.add_parser("report")
    report.add_argument("runs", type=Path, nargs="+")
    report.add_argument("--output", type=Path, required=True)
    report.add_argument(
        "--paired-output", type=Path, help="Optional machine-readable paired changes"
    )
    args = parser.parse_args()
    try:
        if args.command.startswith("answer-"):
            answer_command(args)
        elif args.command == "run":
            dataset, other = load_dataset(args.dataset), load_dataset(args.other_split)
            validate_splits(
                *((dataset, other) if dataset.split == "development" else (other, dataset))
            )
            if args.output.exists():
                raise ValueError("Output already exists")
            load_started = perf_counter()
            artifact, _ = load_artifact(args.index, source=args.source)
            validate_artifact(dataset, artifact)
            declared = (
                RetrievalConfig.model_validate_json(args.retrieval_config.read_bytes())
                if args.retrieval_config
                else None
            )
            hybrid = (
                {
                    key: getattr(declared, key) if getattr(declared, key) is not None else default
                    for key, default in HYBRID_DEFAULTS.items()
                }
                if declared is not None and args.retriever == "hybrid"
                else None
            )
            factory_options = {"hybrid_settings": hybrid} if hybrid is not None else {}
            if declared is not None and declared.reranker is not None:
                factory_options["reranker_settings"] = declared.reranker.model_dump()
            retriever = load_retriever(
                args.retriever, args.index, source=args.source, **factory_options
            )
            load_time = (perf_counter() - load_started) * 1000
            implementation = f"{type(retriever).__module__}.{type(retriever).__qualname__}"
            retrieval = (
                declared
                if declared is not None
                else default_retrieval_config(args.retriever, artifact, implementation, retriever)
            )
            if retrieval.backend != args.retriever or retrieval.implementation != implementation:
                raise ValueError("Retrieval config does not match selected factory adapter")
            if args.limit is not None:
                retrieval = RetrievalConfig.model_validate(
                    {**retrieval.model_dump(), "limit": args.limit}
                )
            elif args.cutoffs:
                retrieval = RetrievalConfig.model_validate(
                    {
                        **retrieval.model_dump(),
                        "limit": max(retrieval.limit, max(args.cutoffs)),
                    }
                )
            execution = ExecutionConfig(
                repeats=args.repeats,
                warmups=args.warmups,
                measure_memory=args.measure_memory,
                ingestion_time_ms=args.ingestion_time_ms,
                index_load_time_ms=load_time,
            )
            provider = LocalPreview() if args.mode == "local-preview" else None
            result = run_evaluation(
                dataset,
                artifact,
                retriever,
                retrieval,
                provider=provider,
                generation=GenerationConfig(provider="local-preview" if provider else "none"),
                execution=execution,
                cutoffs=args.cutoffs,
                context_budgets=args.context_budgets,
                evidence_labels=EvidenceLabels.model_validate_json(
                    args.evidence_labels.read_bytes()
                )
                if args.evidence_labels
                else None,
                encoding_diagnostics=EncodingDiagnostics.model_validate_json(
                    args.encoding_diagnostics.read_bytes()
                )
                if args.encoding_diagnostics
                else None,
            )
            args.output.mkdir(parents=True, exist_ok=False)
            (args.output / "run.json").write_bytes(encoded(result))
            (args.output / "review.json").write_bytes(
                encoded(review_template(result).model_dump(mode="json"))
            )
            (args.output / "report.md").write_text(
                comparison_report([result], [None]), encoding="utf-8"
            )
            print(f"Saved {len(result['results'])} cases to {args.output}")
            if any(row["error"] for row in result["results"]):
                parser.exit(1, "Run saved with case errors; inspect run.json.\n")
        else:
            runs = [json.loads((path / "run.json").read_bytes()) for path in args.runs]
            reviews = [
                Review.model_validate_json((path / "review.json").read_bytes())
                if (path / "review.json").exists()
                else None
                for path in args.runs
            ]
            if args.output.exists() or (
                args.paired_output
                and (
                    args.paired_output.exists()
                    or args.paired_output.resolve() == args.output.resolve()
                )
            ):
                raise ValueError("Report output already exists")
            body = comparison_report(runs, reviews)
            paired = [
                {
                    "baseline_run_id": runs[0]["run_id"],
                    "candidate_run_id": candidate["run_id"],
                    "changes": {str(k): paired_changes(runs[0], candidate, k) for k in (1, 4, 10)},
                    "complete_evidence_statistics": {
                        str(k): exact_mcnemar(
                            {
                                r["case_id"]: r.get("metrics_at_k", {})
                                .get(str(k), {})
                                .get("complete_evidence")
                                for r in runs[0]["results"]
                            },
                            {
                                r["case_id"]: r.get("metrics_at_k", {})
                                .get(str(k), {})
                                .get("complete_evidence")
                                for r in candidate["results"]
                            },
                        )
                        for k in (1, 4, 10)
                    },
                }
                for candidate in runs[1:]
            ]
            with args.output.open("x", encoding="utf-8") as output:
                output.write(body)
            if args.paired_output:
                with args.paired_output.open("xb") as output:
                    output.write(
                        encoded({"schema_version": 1, "primary_k": 4, "comparisons": paired})
                    )
    except (ValueError, OSError, KeyError):
        # Avoid dumping user-controlled values, paths or provider credentials.
        parser.exit(2, "Evaluation failed: check dataset, artifact, split and output contracts.\n")


if __name__ == "__main__":
    main()
