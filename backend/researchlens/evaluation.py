"""Offline-first evaluation: python -m researchlens.evaluation --help."""

import argparse
import hashlib
import json
import math
import platform
import subprocess
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from pydantic import TypeAdapter

from researchlens.answers import INSTRUCTIONS, AnswerProvider, LocalPreview, OpenAIProvider
from researchlens.evaluation_schema import (
    CaseReview,
    ClaimReview,
    Dataset,
    GenerationConfig,
    RetrievalConfig,
    Review,
)
from researchlens.ingest import ROOT
from researchlens.models import Passage, SearchHit
from researchlens.retrieval import Retriever


class Search(Protocol):
    def search(self, question: str, limit: int = 4) -> list[SearchHit]: ...


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encoded(value: dict) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def load_dataset(path: Path) -> Dataset:
    return Dataset.model_validate_json(path.read_bytes())


def validate_splits(development: Dataset, held_out: Dataset) -> None:
    if development.split != "development" or held_out.split != "held-out":
        raise ValueError("Expected separate development and held-out datasets")
    ids = {c.id for c in development.cases}
    questions = {" ".join(c.question.casefold().split()) for c in development.cases}
    if any(
        c.id in ids or " ".join(c.question.casefold().split()) in questions for c in held_out.cases
    ):
        raise ValueError("Development and held-out cases overlap")


def validate_artifact(dataset: Dataset, artifact: dict) -> list[Passage]:
    if not dataset.cases:
        raise ValueError("No cases: real-corpus question creation is pending")
    if dataset.split == "held-out" and dataset.status != "frozen":
        raise ValueError("Held-out runs require a frozen, human-approved dataset")
    if artifact.get("schema_version") != 1:
        raise ValueError("Unsupported passage artifact schema")
    if dataset.corpus_sha256 != artifact.get("source_sha256"):
        raise ValueError("Dataset corpus hash differs from the passage artifact; review references")
    passages = TypeAdapter(list[Passage]).validate_python(artifact["passages"])
    by_id = {p.id: p for p in passages}
    if not passages or len(by_id) != len(passages):
        raise ValueError("Passage artifact must contain unique passages")
    if dataset.material == "real-corpus" and any(p.kind != "technical" for p in passages):
        raise ValueError("Real-corpus evaluation cannot use synthetic passages")
    for case in dataset.cases:
        for ref in case.references:
            passage = by_id.get(ref.passage_id)
            if not passage or (passage.document_id, passage.paragraph) != (
                ref.source_id,
                ref.paragraph,
            ):
                raise ValueError("Expected passage/source/paragraph reference is stale")
    return passages


def code_state() -> dict:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

    try:
        # Paths/diff contents are not saved, only identity and a dirty flag/hash.
        return {
            "commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
            "evaluation_code_sha256": digest(
                Path(__file__).read_bytes()
                + Path(__file__).with_name("evaluation_schema.py").read_bytes()
            ),
        }
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}


def run_evaluation(
    dataset: Dataset,
    artifact: dict,
    retriever: Search,
    retrieval: RetrievalConfig,
    *,
    provider: AnswerProvider | None = None,
    generation: GenerationConfig | None = None,
    estimated_run_cost_usd: float | None = None,
    pricing_date: str | None = None,
) -> dict:
    """Injected implementations own their resources; never serialize clients/settings.

    Retrieval implementations must be local for an offline run. Live providers require
    reviewed cases and an explicit prior estimate; the CLI never constructs one.
    """
    passages = validate_artifact(dataset, artifact)
    generation = generation or GenerationConfig()
    if (provider is None) != (generation.provider == "none"):
        raise ValueError("Provider and generation metadata disagree")
    if isinstance(provider, OpenAIProvider) or generation.provider == "openai":
        if not isinstance(provider, OpenAIProvider) or generation.provider != "openai":
            raise ValueError("OpenAI provider must be declared accurately")
        if (
            provider.model != "gpt-6-luna"
            or provider.MAX_OUTPUT_TOKENS != generation.max_output_tokens
            or provider.client.max_retries != 0
            or generation.prompt_sha256 != digest(INSTRUCTIONS.encode())
        ):
            raise ValueError("Live provider does not match the bounded Luna configuration")
        if any(c.review_status != "approved" for c in dataset.cases):
            raise ValueError("Review all questions before paid evaluation")
        if (
            estimated_run_cost_usd is None
            or not math.isfinite(estimated_run_cost_usd)
            or estimated_run_cost_usd <= 0
            or not pricing_date
        ):
            raise ValueError("Record a dated cost estimate before paid evaluation")
    by_id = {p.id: p for p in passages}
    rows = []
    for case in dataset.cases:
        started = perf_counter()
        row = {
            "case_id": case.id,
            "category": case.category,
            "retrieved_passage_ids": [],
            "retrieved_passages": [],
            "answer": None,
            "source_recall_at_k": None,
            "passage_recall_at_k": None,
            "all_expected_sources_retrieved": None,
            "retrieval_latency_ms": None,
            "generation_latency_ms": None,
            "input_tokens": 0 if generation.provider != "openai" else None,
            "output_tokens": 0 if generation.provider != "openai" else None,
            "estimated_api_cost_usd": 0 if generation.provider != "openai" else None,
            "error": None,
        }
        stage = "retrieval"
        try:
            hits = retriever.search(case.question, limit=retrieval.limit)
            if len(hits) > retrieval.limit or len({p.id for p in hits}) != len(hits):
                raise ValueError("Retriever returned too many or duplicate hits")
            if any(
                p.id not in by_id or Passage.model_validate(p.model_dump()) != by_id[p.id]
                for p in hits
            ):
                raise ValueError("Retriever returned passages outside the pinned artifact")
            row["retrieval_latency_ms"] = round((perf_counter() - started) * 1000, 3)
            row["retrieved_passage_ids"] = [p.id for p in hits]
            row["retrieved_passages"] = [p.model_dump() for p in hits]
            # Related references for unanswerable cases are context, not answer evidence.
            if not case.expected_abstention:
                expected = set(case.expected_source_ids)
                found = {p.document_id for p in hits}
                expected_passages = {r.passage_id for r in case.references}
                row["source_recall_at_k"] = len(expected & found) / len(expected)
                row["passage_recall_at_k"] = len(expected_passages & {p.id for p in hits}) / len(
                    expected_passages
                )
                row["all_expected_sources_retrieved"] = expected <= found
            if provider is not None:
                stage = "generation"
                answer_started = perf_counter()
                answer = provider.answer(case.question, hits)
                row["generation_latency_ms"] = round((perf_counter() - answer_started) * 1000, 3)
                row["answer"] = answer.model_dump()
                if generation.provider == "openai":
                    row["input_tokens"] = answer.input_tokens
                    row["output_tokens"] = answer.output_tokens
                    row["estimated_api_cost_usd"] = answer.estimated_api_cost_usd
        except Exception:
            # Exception messages/tracebacks can contain authorization headers or request bodies.
            row["error"] = {"stage": stage, "code": f"{stage}_failed"}
        row["latency_ms"] = round((perf_counter() - started) * 1000, 3)
        rows.append(row)
    return {
        "schema_version": 1,
        "run_id": str(uuid4()),
        "created_at": datetime.now(UTC).isoformat(),
        "code": code_state(),
        "runtime": {
            "python": platform.python_version(),
            "lockfile_sha256": digest((ROOT / "uv.lock").read_bytes()),
            "packages": {name: version(name) for name in ("scikit-learn", "pydantic", "openai")},
        },
        "dataset": dataset.model_dump(mode="json"),
        "dataset_sha256": digest(encoded(dataset.model_dump(mode="json"))),
        "corpus": {
            "source_sha256": artifact["source_sha256"],
            "artifact_sha256": digest(encoded(artifact)),
            "chunking": artifact["chunking"],
            "passage_count": len(passages),
        },
        "retrieval": retrieval.model_dump(),
        "generation": generation.model_dump(),
        "preflight_cost_estimate_usd": estimated_run_cost_usd,
        "pricing_date": pricing_date,
        "results": rows,
    }


def review_template(run: dict) -> Review:
    return Review(
        run_id=run["run_id"],
        run_sha256=digest(encoded(run)),
        cases=[
            CaseReview(
                case_id=row["case_id"],
                claims=[
                    ClaimReview(section_index=i)
                    for i, _ in enumerate((row["answer"] or {}).get("sections", []))
                ],
            )
            for row in run["results"]
        ],
    )


def summarize(run: dict, review: Review | None = None) -> dict:
    rows = run["results"]
    completed = []
    if review:
        if review.run_id != run["run_id"] or review.run_sha256 != digest(encoded(run)):
            raise ValueError("Review does not match this run")
        if sorted(c.case_id for c in review.cases) != sorted(r["case_id"] for r in rows):
            raise ValueError("Review must contain exactly one entry per result")
        by_id = {r["case_id"]: r for r in rows}
        for case in review.cases:
            row = by_id[case.case_id]
            if sorted(c.section_index for c in case.claims) != list(
                range(len((row["answer"] or {}).get("sections", [])))
            ):
                raise ValueError("Review sections differ from generated sections")
            if (
                case.status == "complete"
                and (row["answer"] or {}).get("status") not in ("answered", "insufficient_evidence")
                and (case.correctness, case.citation_support, case.abstention)
                != ("not-applicable", "not-applicable", "not-applicable")
            ):
                raise ValueError("Retrieval, preview and error cases have no answer-quality scores")
        completed = [c for c in review.cases if c.status == "complete"]
    recalls = [r["source_recall_at_k"] for r in rows if r["source_recall_at_k"] is not None]
    comparisons = [r for r in rows if r["category"] == "comparison"]
    latencies = [r["latency_ms"] for r in rows]
    cases = {c["id"]: c for c in run["dataset"]["cases"]}
    generated = [
        r
        for r in rows
        if (r["answer"] or {}).get("status") in ("answered", "insufficient_evidence")
    ]
    return {
        "cases": len(rows),
        "errors": sum(r["error"] is not None for r in rows),
        "recall_scored": len(recalls),
        "mean_source_recall_at_k": sum(recalls) / len(recalls) if recalls else None,
        "comparison_full_coverage": sum(
            r["all_expected_sources_retrieved"] is True for r in comparisons
        ),
        "comparison_cases": len(comparisons),
        "comparison_mean_source_recall_at_k": (
            sum(r["source_recall_at_k"] or 0 for r in comparisons) / len(comparisons)
            if comparisons
            else None
        ),
        "generated_answers": len(generated),
        "generated_unanswerable_cases": sum(
            cases[r["case_id"]]["expected_abstention"] for r in generated
        ),
        "generated_answerable_cases": sum(
            not cases[r["case_id"]]["expected_abstention"] for r in generated
        ),
        "automatic_abstentions_unanswerable": sum(
            r["answer"]["status"] == "insufficient_evidence"
            and cases[r["case_id"]]["expected_abstention"]
            for r in generated
        ),
        "automatic_full_abstentions": sum(
            r["answer"]["status"] == "insufficient_evidence" for r in generated
        ),
        "automatic_false_abstentions": sum(
            r["answer"]["status"] == "insufficient_evidence"
            and not cases[r["case_id"]]["expected_abstention"]
            for r in generated
        ),
        "no_match_cases": sum(
            r["retrieval_latency_ms"] is not None and not r["retrieved_passage_ids"] for r in rows
        ),
        "human_reviews_complete": len(completed),
        "human_correct": sum(c.correctness == "correct" for c in completed),
        "human_supported": sum(c.citation_support == "supported" for c in completed),
        "human_full_abstention_unanswerable": sum(
            c.abstention == "full" and cases[c.case_id]["expected_abstention"] for c in completed
        ),
        "human_false_abstention": sum(
            c.abstention == "full" and not cases[c.case_id]["expected_abstention"]
            for c in completed
        ),
        "median_latency_ms": median(latencies) if latencies else None,
        "max_latency_ms": max(latencies) if latencies else None,
        "input_tokens_known": sum(r["input_tokens"] or 0 for r in rows),
        "output_tokens_known": sum(r["output_tokens"] or 0 for r in rows),
        "unknown_usage_cases": sum(
            r["input_tokens"] is None or r["output_tokens"] is None for r in rows
        ),
        "estimated_cost_usd_known": sum(r["estimated_api_cost_usd"] or 0 for r in rows),
        "unknown_cost_cases": sum(r["estimated_api_cost_usd"] is None for r in rows),
    }


def comparison_report(runs: list[dict], reviews: list[Review | None]) -> str:
    if not runs or len(runs) != len(reviews):
        raise ValueError("Supply one review slot per run")
    if len({(r["dataset_sha256"], r["corpus"]["artifact_sha256"]) for r in runs}) != 1:
        raise ValueError("Compare only the same dataset and passage artifact")
    summaries = [summarize(r, review) for r, review in zip(runs, reviews, strict=True)]
    lines = [
        "# Evaluation comparison",
        "",
        f"Material: {runs[0]['dataset']['material']}; split: {runs[0]['dataset']['split']}.",
        "Valid citation IDs do not establish factual support. Unreviewed results are development "
        "diagnostics, not quality evidence. Missing usage is not zero cost.",
        "The recall mean uses scored retrievals; inspect errors and recall_scored alongside it. "
        "Comparison coverage includes failed retrievals in its denominator. "
        "No-match and preview statuses are not generated abstentions.",
        "Latency excludes index construction and includes per-case failures; the first case may "
        "include cold-start effects. Small samples do not establish statistical superiority.",
        "",
        f"Dataset SHA-256: {runs[0]['dataset_sha256']}",
        f"Passage artifact SHA-256: {runs[0]['corpus']['artifact_sha256']}",
        "",
        "| Metric | " + " | ".join(r["run_id"] for r in runs) + " |",
        "| --- | " + " | ".join("---" for _ in runs) + " |",
    ]
    for key in summaries[0]:
        lines.append("| " + key + " | " + " | ".join(str(s[key]) for s in summaries) + " |")
    for run in runs:
        lines.extend(
            [
                "",
                f"Run {run['run_id']} configuration:",
                "```json",
                json.dumps(
                    {
                        "code": run["code"],
                        "retrieval": run["retrieval"],
                        "generation": run["generation"],
                    },
                    indent=2,
                ),
                "```",
            ]
        )
    lines.extend(["", "Case diagnostics (inspect full run and human review for evidence):"])
    for run, review in zip(runs, reviews, strict=True):
        for row in run["results"]:
            status = (row["answer"] or {}).get("status", "retrieval-only")
            lines.append(
                f"- {run['run_id']} / {row['case_id']}: recall={row['source_recall_at_k']}, "
                f"status={status}, error={row['error']}"
            )
        if review:
            for case in review.cases:
                if case.status == "complete":
                    lines.append(
                        f"- Review {case.case_id}: correctness={case.correctness}, "
                        f"support={case.citation_support}, abstention={case.abstention}. "
                        f"Notes: {case.notes}"
                    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Free retrieval or local-preview evaluation")
    run.add_argument("--dataset", type=Path, required=True)
    run.add_argument("--other-split", type=Path, required=True)
    run.add_argument("--index", type=Path, default=ROOT / "data/index.json")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--limit", type=int, default=4)
    run.add_argument(
        "--mode", choices=["retrieval-only", "local-preview"], default="retrieval-only"
    )
    report = commands.add_parser("report")
    report.add_argument("runs", type=Path, nargs="+")
    report.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            dataset, other = load_dataset(args.dataset), load_dataset(args.other_split)
            validate_splits(
                *((dataset, other) if dataset.split == "development" else (other, dataset))
            )
            artifact = json.loads(args.index.read_bytes())
            passages = validate_artifact(dataset, artifact)
            retrieval = RetrievalConfig(
                implementation="researchlens.retrieval.Retriever",
                version="tfidf-word-unigram-bigram-english-stopwords-v1",
                limit=args.limit,
            )
            provider = LocalPreview() if args.mode == "local-preview" else None
            result = run_evaluation(
                dataset,
                artifact,
                Retriever(passages),
                retrieval,
                provider=provider,
                generation=GenerationConfig(provider="local-preview" if provider else "none"),
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
            with args.output.open("x", encoding="utf-8") as output:
                output.write(comparison_report(runs, reviews))
    except (ValueError, OSError, KeyError):
        # Avoid dumping user-controlled values, paths or provider credentials.
        parser.exit(2, "Evaluation failed: check dataset, artifact, split and output contracts.\n")


if __name__ == "__main__":
    main()
