"""Offline-first evaluation: python -m researchlens.evaluation --help."""

import argparse
import hashlib
import json
import math
import platform
import subprocess
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from researchlens.answers import (
    INSTRUCTIONS,
    AnswerProvider,
    LocalPreview,
    OpenAIProvider,
    prepare_answer_context,
)
from researchlens.artifacts import (
    EncodingMetadata,
    canonical_hash,
    load_artifact,
    passage_identity,
    validate_passage_artifact,
)
from researchlens.evaluation_evidence import (
    EncodingDiagnostics,
    EvidenceLabels,
    TextRange,
    coverage_loss,
    evidence_coverage,
    ranking_metrics,
    validate_encoding_diagnostics,
    validate_labels,
    validate_pair_diagnostics,
)
from researchlens.evaluation_memory import process_peak_rss_bytes
from researchlens.evaluation_metrics import (
    comparison_details,
    cutoff_summary,
    paired_changes,
    percentile_nearest_rank,
)
from researchlens.evaluation_schema import (
    CaseReview,
    ClaimReview,
    Dataset,
    ExecutionConfig,
    GenerationConfig,
    RetrievalConfig,
    Review,
)
from researchlens.ingest import ROOT, TECHNICAL_CORPUS
from researchlens.models import Passage, SearchHit
from researchlens.retrieval import HYBRID_DEFAULTS, load_retriever


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
        raise ValueError("No cases: question creation and source review are pending")
    if dataset.split == "held-out" and dataset.status != "frozen":
        raise ValueError("Held-out runs require a frozen, approved dataset")
    return validate_dataset_references(dataset, artifact)


def validate_dataset_references(dataset: Dataset, artifact: dict) -> list[Passage]:
    """Check pinned sources/locations without executing retrieval or approving drafts.

    This permits offline authoring checks for held-out candidates. Execution must
    still go through validate_artifact, which enforces the held-out freeze guard.
    Valid locations do not establish that the referenced text supports a claim.
    """
    if dataset.corpus_sha256 != artifact.get("source_sha256"):
        raise ValueError("Dataset corpus hash differs from the passage artifact; review references")
    passages = validate_passage_artifact(artifact)
    by_id = {p.id: p for p in passages}
    if not passages or len(by_id) != len(passages):
        raise ValueError("Passage artifact must contain unique passages")
    if dataset.material == "real-corpus" and any(p.kind != "technical" for p in passages):
        raise ValueError("Real-corpus evaluation cannot use synthetic passages")
    if dataset.source_versions:
        sources = {s.source_id: s for s in dataset.source_versions}
        if set(sources) != {p.document_id for p in passages}:
            raise ValueError("Dataset source versions do not cover the full corpus")
        for passage in passages:
            expected = sources[passage.document_id]
            actual = passage.attribution
            if not actual or (expected.source_sha256, expected.doi, expected.publication_date) != (
                actual.source_sha256,
                actual.doi,
                actual.publication_date,
            ):
                raise ValueError("Original source version differs from dataset")
    for case in dataset.cases:
        for ref in case.references:
            passage = by_id.get(ref.passage_id)
            if not passage or (passage.document_id, passage.paragraph) != (
                ref.source_id,
                ref.paragraph,
            ):
                raise ValueError("Expected passage/source/paragraph reference is stale")
            if (
                ref.source_section is not None and ref.source_section != passage.source_section
            ) or (ref.source_locator is not None and ref.source_locator != passage.source_locator):
                raise ValueError("Expected source location is stale")
    return passages


# PR #9's encoding contract maps to these explicit evaluation fields.
ENCODING_FIELDS = {
    "model": "model",
    "revision": "revision",
    "dimensions": "dimensions",
    "max_tokens": "max_tokens",
    "pooling": "pooling",
    "normalization": "normalization",
    "query_prefix": "query_instruction",
    "document_prefix": "document_instruction",
    "text": "text_representation",
    "encoding_version": "encoding_version",
    "weights": "weights",
    "tokenizer": "tokenizer",
    "runtime": "runtime",
    "runtime_version": "runtime_version",
    "backend": "runtime_backend",
    "device": "device",
    "precision": "precision",
    "quantization": "quantization",
    "truncation": "truncation",
    "batch_size": "batch_size",
    "intra_op_threads": "intra_op_threads",
    "inter_op_threads": "inter_op_threads",
}


def encoding_settings(artifact: dict) -> dict:
    if "embeddings" not in artifact:
        return {}
    encoding = EncodingMetadata.model_validate(artifact["embeddings"]["encoding"])
    return {
        target: getattr(encoding, source)
        for source, target in ENCODING_FIELDS.items()
        if getattr(encoding, source) is not None
    }


def validate_retrieval_config(config: RetrievalConfig, artifact: dict) -> RetrievalConfig:
    artifact_hash = canonical_hash(artifact)
    if config.artifact_sha256 is not None and config.artifact_sha256 != artifact_hash:
        raise ValueError("Declared retrieval artifact hash differs from loaded artifact")
    if config.backend in ("embeddings", "hybrid"):
        if "embeddings" not in artifact:
            raise ValueError("Selected retrieval requires an embedding artifact")
        for field, value in encoding_settings(artifact).items():
            if getattr(config, field) != value:
                raise ValueError("Declared encoding settings differ from artifact")
    return config.model_copy(update={"artifact_sha256": artifact_hash})


def default_retrieval_config(
    backend: str,
    artifact: dict,
    implementation: str,
    adapter=None,
) -> RetrievalConfig:
    settings = encoding_settings(artifact) if backend != "tfidf" else {}
    if backend == "hybrid":
        settings.update(HYBRID_DEFAULTS)
        if adapter is not None:
            settings.update(adapter.retrieval_settings)
    if adapter is not None and hasattr(adapter, "reranking_settings"):
        settings["reranker"] = adapter.reranking_settings
    if adapter is not None and hasattr(adapter, "selection_settings"):
        settings["passage_selection"] = adapter.selection_settings
    return RetrievalConfig(
        implementation=implementation,
        version="tfidf-word-unigram-bigram-english-stopwords-v1"
        if backend == "tfidf"
        else f"encoding-v{settings.get('encoding_version', 'unknown')}",
        backend=backend,
        **settings,
    )


def installed_versions() -> dict:
    packages = {}
    for name in (
        "numpy",
        "scikit-learn",
        "pydantic",
        "openai",
        "onnxruntime",
        "tokenizers",
        "huggingface-hub",
        "torch",
        "transformers",
        "safetensors",
        "sentence-transformers",
    ):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return packages


def code_state() -> dict:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

    try:
        # Paths/diff contents are not saved, only identity and a dirty flag/hash.
        return {
            "commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
            "evaluation_code_sha256": canonical_hash(
                {
                    name: digest(
                        Path(__file__).with_name(name).read_bytes().replace(b"\r\n", b"\n")
                    )
                    for name in (
                        "evaluation.py",
                        "evaluation_schema.py",
                        "artifacts.py",
                        "evaluation_memory.py",
                        "evaluation_evidence.py",
                        "evaluation_metrics.py",
                        "answers.py",
                        "models.py",
                    )
                }
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
    execution: ExecutionConfig | None = None,
    evidence_labels: EvidenceLabels | None = None,
    encoding_diagnostics: EncodingDiagnostics | None = None,
    cutoffs: list[int] | None = None,
) -> dict:
    """Injected implementations own their resources; never serialize clients/settings.

    Retrieval implementations must be local for an offline run. Live providers require
    reviewed cases and an explicit prior estimate; the CLI never constructs one.
    """
    passages = validate_artifact(dataset, artifact)
    retrieval = validate_retrieval_config(retrieval, artifact)
    cutoffs = (
        cutoffs
        if cutoffs is not None
        else [k for k in (1, 4, 10, retrieval.limit) if k <= retrieval.limit]
    )
    if not cutoffs or any(type(k) is not int or k < 1 or k > retrieval.limit for k in cutoffs):
        raise ValueError("Cutoffs must be positive integers within the actual retrieval limit")
    cutoffs = sorted(set(cutoffs))
    labels = (
        validate_labels(evidence_labels, dataset, artifact, passages) if evidence_labels else {}
    )
    if encoding_diagnostics is None and retrieval.backend in ("embeddings", "hybrid"):
        diagnostics_hook = getattr(retriever, "get_encoding_diagnostics", None)
        if callable(diagnostics_hook):
            supplied_diagnostics = diagnostics_hook()
            if supplied_diagnostics is not None:
                encoding_diagnostics = EncodingDiagnostics.model_validate(supplied_diagnostics)
    encoded_passages = (
        validate_encoding_diagnostics(encoding_diagnostics, artifact, passages)
        if encoding_diagnostics
        else {}
    )
    execution = execution or ExecutionConfig()
    memory_before = process_peak_rss_bytes() if execution.measure_memory else None
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
            "first_relevant_passage_rank": None,
            "reciprocal_rank_at_k": None,
            "retrieval_attempts": [],
            "ranking_stable_across_repeats": None,
            "warmup_latency_ms": None,
            "retrieval_latency_ms": None,
            "generation_latency_ms": None,
            "input_tokens": 0 if generation.provider != "openai" else None,
            "output_tokens": 0 if generation.provider != "openai" else None,
            "estimated_api_cost_usd": 0 if generation.provider != "openai" else None,
            "error": None,
            "metrics_at_k": {},
            "embedding_coverage_at_k": {},
            "embedding_truncation_loss_at_k": {},
            "answer_context_preview": None,
            "answer_context_coverage": None,
            "answer_context_selection_loss": None,
            "answer_context_truncation_loss": None,
            "encoder_truncated_passage_ids": [],
            "encoder_unmeasured_passage_ids": [],
            "reranker_passage_diagnostics": None,
        }
        stage = "retrieval"
        hits = None
        try:
            if execution.warmups:
                warmup_started = perf_counter()
                for _ in range(execution.warmups):
                    retriever.search(case.question, limit=retrieval.limit)
                row["warmup_latency_ms"] = round((perf_counter() - warmup_started) * 1000, 3)
            for _ in range(execution.repeats):
                query_started = perf_counter()
                attempt = {"latency_ms": None, "retrieved_passage_ids": [], "error": None}
                row["retrieval_attempts"].append(attempt)
                try:
                    current = retriever.search(case.question, limit=retrieval.limit)
                    attempt["latency_ms"] = round((perf_counter() - query_started) * 1000, 3)
                    if len(current) > retrieval.limit or len({p.id for p in current}) != len(
                        current
                    ):
                        raise ValueError("Retriever returned too many or duplicate hits")
                    if any(
                        p.id not in by_id
                        or Passage.model_validate(p.model_dump()) != by_id[p.id]
                        or not math.isfinite(p.score)
                        for p in current
                    ):
                        raise ValueError("Retriever returned invalid or unpinned passages")
                    attempt["retrieved_passage_ids"] = [p.id for p in current]
                    if hits is None:
                        hits = current
                        # Preserve the primary ranking even if a later timing repeat fails.
                        row["retrieved_passage_ids"] = [p.id for p in hits]
                        row["retrieved_passages"] = [p.model_dump() for p in hits]
                except Exception:
                    attempt["latency_ms"] = round((perf_counter() - query_started) * 1000, 3)
                    attempt["error"] = "retrieval_failed"
                    raise
            row["retrieval_latency_ms"] = median(a["latency_ms"] for a in row["retrieval_attempts"])
            row["ranking_stable_across_repeats"] = all(
                a["retrieved_passage_ids"] == row["retrieved_passage_ids"]
                for a in row["retrieval_attempts"]
            )
            row["retrieved_passage_ids"] = [p.id for p in hits]
            row["retrieved_passages"] = [p.model_dump() for p in hits]
            if retrieval.reranker is not None:
                hook = getattr(retriever, "get_reranking_diagnostics", None)
                if callable(hook):
                    measurements = validate_pair_diagnostics(
                        hook(case.question),
                        passages,
                        retrieval.reranker.max_tokens,
                    )
                    if not {p.id for p in hits} <= {p["passage_id"] for p in measurements}:
                        raise ValueError("Reranker diagnostics omit returned passages")
                    row["reranker_passage_diagnostics"] = measurements
            # Related references for unanswerable cases are context, not answer evidence.
            if not case.expected_abstention:
                metrics = ranking_metrics(case, hits, labels.get(case.id))
                row["source_recall_at_k"] = metrics["source_recall"]
                row["passage_recall_at_k"] = metrics["passage_recall"]
                row["all_expected_sources_retrieved"] = metrics["all_sources"]
                row["first_relevant_passage_rank"] = metrics["first_relevant_rank"]
                row["reciprocal_rank_at_k"] = metrics["reciprocal_rank"]
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
        # Failed retrievals score zero even if an earlier timing repeat preserved hits.
        scored_hits = [] if row["error"] and row["error"]["stage"] == "retrieval" else hits or []
        entry = labels.get(case.id)
        for k in cutoffs:
            prefix = scored_hits[:k]
            row["metrics_at_k"][str(k)] = ranking_metrics(case, prefix, entry)
            if retrieval.backend in ("embeddings", "hybrid") and not case.expected_abstention:
                visibility = {
                    p.id: encoded_passages[p.id].retained_ranges
                    if p.id in encoded_passages
                    else None
                    for p in prefix
                }
                row["embedding_coverage_at_k"][str(k)] = evidence_coverage(entry, visibility)
                row["embedding_truncation_loss_at_k"][str(k)] = coverage_loss(
                    row["metrics_at_k"][str(k)], row["embedding_coverage_at_k"][str(k)]
                )
        if hits is not None:
            budget = (
                {
                    "max_passages": provider.MAX_PASSAGES,
                    "max_passage_chars": provider.MAX_PASSAGE_CHARS,
                    "max_context_chars": provider.MAX_CONTEXT_CHARS,
                }
                if isinstance(provider, OpenAIProvider)
                else {}
            )
            prepared = prepare_answer_context(hits, **budget)
            row["answer_context_preview"] = prepared.diagnostics.model_dump()
            row["answer_context_coverage"] = evidence_coverage(
                entry,
                {
                    pid: [TextRange(start=0, end=length)]
                    for pid, length in prepared.diagnostics.visible_chars.items()
                    if length
                },
            )
            full_context = ranking_metrics(case, prepared.supplied, entry)
            row["answer_context_selection_loss"] = coverage_loss(
                ranking_metrics(case, hits, entry), full_context
            )
            row["answer_context_truncation_loss"] = coverage_loss(
                full_context, row["answer_context_coverage"]
            )
            row["encoder_truncated_passage_ids"] = [
                p.id for p in hits if p.id in encoded_passages and encoded_passages[p.id].truncated
            ]
            if retrieval.backend in ("embeddings", "hybrid"):
                row["encoder_unmeasured_passage_ids"] = [
                    p.id for p in hits if p.id not in encoded_passages
                ]
        row["latency_ms"] = round((perf_counter() - started) * 1000, 3)
        row["process_peak_rss_bytes"] = (
            process_peak_rss_bytes() if execution.measure_memory else None
        )
        rows.append(row)
    return {
        "schema_version": 2,
        "evaluation_contract": {
            "metrics_version": 2,
            "primary_k": 4,
            "evidence_labels_sha256": canonical_hash(evidence_labels.model_dump(mode="json"))
            if evidence_labels
            else None,
            "percentile_method": "nearest-rank",
        },
        "cutoffs": cutoffs,
        "evidence_labels": evidence_labels.model_dump(mode="json") if evidence_labels else None,
        "encoding_diagnostics": encoding_diagnostics.model_dump(mode="json")
        if encoding_diagnostics
        else None,
        "encoding_measurement_summary": {
            "measured_passages": len(encoded_passages),
            "unmeasured_passages": len(passages) - len(encoded_passages),
            "truncated_passages": sum(p.truncated for p in encoded_passages.values()),
            "truncation_rate_measured": sum(p.truncated for p in encoded_passages.values())
            / len(encoded_passages)
            if encoded_passages
            else None,
            "applicable": retrieval.backend in ("embeddings", "hybrid"),
        },
        "run_id": str(uuid4()),
        "created_at": datetime.now(UTC).isoformat(),
        "code": code_state(),
        "runtime": {
            "python": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
            "lockfile_sha256": digest((ROOT / "uv.lock").read_bytes()),
            "packages": installed_versions(),
        },
        "dataset": dataset.model_dump(mode="json"),
        "dataset_sha256": digest(encoded(dataset.model_dump(mode="json"))),
        "corpus": {
            "source_sha256": artifact["source_sha256"],
            "artifact_sha256": canonical_hash(artifact),
            "shared_passage_sha256": passage_identity(artifact, passages),
            "embedding_artifact_sha256": canonical_hash(artifact)
            if "embeddings" in artifact
            else None,
            "encoding_sha256": canonical_hash(artifact["embeddings"]["encoding"])
            if "embeddings" in artifact
            else None,
            "chunking": artifact["chunking"],
            "passage_count": len(passages),
        },
        "retrieval": retrieval.model_dump(),
        "generation": generation.model_dump(),
        "execution": execution.model_dump(),
        "memory": {
            "method": "process-lifetime-high-water-rss" if execution.measure_memory else None,
            "before_queries_peak_rss_bytes": memory_before,
            "peak_rss_bytes": process_peak_rss_bytes() if execution.measure_memory else None,
        },
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
                status="pending"
                if (row["answer"] or {}).get("status") in ("answered", "insufficient_evidence")
                else "not-applicable",
                notes=""
                if (row["answer"] or {}).get("status") in ("answered", "insufficient_evidence")
                else "No generated answer: answer correctness/support/abstention do not apply.",
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
    answerable = [r for r in rows if not cases[r["case_id"]]["expected_abstention"]]
    query_samples = [
        a["latency_ms"] for r in rows for a in r.get("retrieval_attempts", []) if a["error"] is None
    ]
    reciprocal_ranks = [r.get("reciprocal_rank_at_k") for r in answerable]
    generated = [
        r
        for r in rows
        if (r["answer"] or {}).get("status") in ("answered", "insufficient_evidence")
    ]
    primary = cutoff_summary(run, 4) if run.get("evaluation_contract") else {}
    return {
        "cases": len(rows),
        "errors": sum(r["error"] is not None for r in rows),
        "recall_scored": len(recalls),
        "mean_source_recall_at_k": sum(recalls) / len(recalls) if recalls else None,
        "answerable_cases": len(answerable),
        "mean_source_recall_with_failures": (
            sum(r["source_recall_at_k"] or 0 for r in answerable) / len(answerable)
            if answerable
            else None
        ),
        "mean_passage_recall_with_failures": (
            sum(r["passage_recall_at_k"] or 0 for r in answerable) / len(answerable)
            if answerable
            else None
        ),
        "mrr_at_k_with_failures": (
            sum(value or 0 for value in reciprocal_ranks) / len(answerable)
            if answerable and run.get("schema_version") == 2
            else None
        ),
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
        "query_timing_samples": len(query_samples),
        "query_failed_attempts": sum(
            a["error"] is not None for r in rows for a in r.get("retrieval_attempts", [])
        ),
        "query_median_ms": median(query_samples) if query_samples else None,
        "query_p95_ms": percentile_nearest_rank(query_samples, 0.95),
        "query_max_ms": max(query_samples) if query_samples else None,
        "primary_k4_mrr": primary.get("mrr"),
        "primary_k4_group_coverage": primary.get("mean_group_coverage"),
        "primary_k4_complete_evidence_rate": primary.get("complete_evidence_rate"),
        "evidence_labels_review_status": (run.get("evidence_labels") or {}).get("review_status"),
        "encoder_measured_passages": (run.get("encoding_measurement_summary") or {}).get(
            "measured_passages"
        ),
        "encoder_unmeasured_passages": (run.get("encoding_measurement_summary") or {}).get(
            "unmeasured_passages"
        ),
        "encoder_truncation_rate_measured": (run.get("encoding_measurement_summary") or {}).get(
            "truncation_rate_measured"
        ),
        "encoder_k4_evidence_loss_cases": sum(
            bool(r.get("embedding_truncation_loss_at_k", {}).get("4", {}).get("lost_group_ids"))
            for r in rows
        ),
        "encoder_k4_evidence_unknown_cases": sum(
            bool(r.get("embedding_truncation_loss_at_k", {}).get("4", {}).get("unknown_group_ids"))
            for r in rows
        ),
        "context_selection_evidence_loss_cases": sum(
            bool((r.get("answer_context_selection_loss") or {}).get("lost_group_ids")) for r in rows
        ),
        "context_truncation_evidence_loss_cases": sum(
            bool((r.get("answer_context_truncation_loss") or {}).get("lost_group_ids"))
            for r in rows
        ),
        "context_preview_truncated_passages": sum(
            len((r.get("answer_context_preview") or {}).get("truncated_passage_ids", []))
            for r in rows
        ),
        "context_preview_omitted_passages": sum(
            len((r.get("answer_context_preview") or {}).get("omitted_passage_ids", []))
            for r in rows
        ),
        "unstable_ranking_cases": sum(
            r.get("ranking_stable_across_repeats") is False for r in rows
        ),
        "ingestion_time_ms": run.get("execution", {}).get("ingestion_time_ms"),
        "index_load_time_ms": run.get("execution", {}).get("index_load_time_ms"),
        "process_peak_rss_bytes": run.get("memory", {}).get("peak_rss_bytes"),
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
    if len({r["schema_version"] for r in runs}) != 1:
        raise ValueError("Regenerate legacy runs before comparing shared passage identities")
    identity_field = (
        "shared_passage_sha256" if runs[0]["schema_version"] == 2 else "artifact_sha256"
    )
    if (
        len(
            {
                (
                    r["dataset_sha256"],
                    r["corpus"]["source_sha256"],
                    canonical_hash(r["corpus"]["chunking"]),
                    r["corpus"][identity_field],
                    canonical_hash(r.get("evaluation_contract")),
                )
                for r in runs
            }
        )
        != 1
    ):
        raise ValueError(
            "Compare only the same dataset, corpus, chunking, passage/source metadata "
            "and evidence/scoring contract"
        )
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
        "MRR uses labeled evidence passage IDs when provided, otherwise expected passage IDs, "
        "with misses/retrieval errors zero "
        "over all answerable cases. "
        "Unanswerable cases receive no relevance score; nearest neighbors do not prove support.",
        "Query timings exclude setup/warmups; setup is recorded separately. Peak RSS is a "
        "process-lifetime high-water mark: use a fresh process per model. "
        "Small unreviewed samples do not establish model superiority.",
        "",
        f"Dataset SHA-256: {runs[0]['dataset_sha256']}",
        f"Shared passage identity SHA-256: {runs[0]['corpus'][identity_field]}",
        "",
        "| Metric | " + " | ".join(r["run_id"] for r in runs) + " |",
        "| --- | " + " | ".join("---" for _ in runs) + " |",
    ]
    for key in summaries[0]:
        lines.append("| " + key + " | " + " | ".join(str(s[key]) for s in summaries) + " |")
    lines.extend(comparison_details(runs))
    lines.extend(
        [
            "",
            "Evidence coverage follows the supplied labels, including OR alternatives and AND "
            "combinations. Unreviewed labels produce development diagnostics. Full source presence "
            "and one relevant passage do not establish complete support. Encoder visibility is "
            "unknown without measured character ranges. Application context preview is offline. "
            "Actual OpenAI answers record the supplied context. Neither is answer correctness.",
        ]
    )
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
                        "execution": run.get("execution"),
                        "evaluation_contract": run.get("evaluation_contract"),
                        "encoding_measurement_summary": run.get("encoding_measurement_summary"),
                        "embedding_artifact_sha256": run["corpus"].get("embedding_artifact_sha256"),
                        "unknown_embedding_runtime_settings": [
                            field
                            for field in (
                                "runtime",
                                "runtime_version",
                                "runtime_backend",
                                "device",
                                "precision",
                                "quantization",
                                "truncation",
                                "batch_size",
                            )
                            if run["retrieval"].get(field) is None
                        ]
                        if run["retrieval"].get("backend") in ("embeddings", "hybrid")
                        else [],
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
            primary = (row.get("metrics_at_k", {}).get("4") or {}).get("complete_evidence")
            lines.append(
                f"- {run['run_id']} / {row['case_id']}: recall={row['source_recall_at_k']}, "
                f"first relevant rank={row.get('first_relevant_passage_rank')}, "
                f"status={status}, error={row['error']}"
                f", k4 complete={primary}, "
                f"encoder lost/unknown={row.get('embedding_truncation_loss_at_k', {}).get('4')}, "
                f"context selection loss={row.get('answer_context_selection_loss')}, "
                f"context truncation loss={row.get('answer_context_truncation_loss')}"
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
    run.add_argument("--source", type=Path, default=TECHNICAL_CORPUS)
    run.add_argument("--retriever", choices=["tfidf", "embeddings", "hybrid"], default="tfidf")
    run.add_argument(
        "--retrieval-config",
        type=Path,
        help="Strict RetrievalConfig JSON for settings missing from artifact metadata",
    )
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--limit", type=int)
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
        if args.command == "run":
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
