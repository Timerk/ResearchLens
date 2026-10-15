"""Offline-first evaluation: python -m researchlens.evaluation --help."""

import math
import platform
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from statistics import median
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from researchlens.answers import (
    INSTRUCTIONS,
    AnswerProvider,
    OpenAIProvider,
    prepare_answer_context,
)
from researchlens.artifacts import (
    EncodingMetadata,
    canonical_hash,
    passage_identity,
)
from researchlens.defaults import DEFAULT_MODEL
from researchlens.ingest import ROOT
from researchlens.models import Passage, SearchHit
from researchlens.retrieval import HYBRID_DEFAULTS

from researchlens_eval.context_evaluation import (
    STANDARD_BUDGETS,
    context_profile,
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
    TextRange,
    coverage_loss,
    evidence_coverage,
    ranking_metrics,
    validate_encoding_diagnostics,
    validate_labels,
    validate_pair_diagnostics,
)
from researchlens_eval.evaluation_memory import process_peak_rss_bytes
from researchlens_eval.evaluation_schema import (
    Dataset,
    ExecutionConfig,
    GenerationConfig,
    RetrievalConfig,
)

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


class Search(Protocol):
    def search(self, question: str, limit: int = 4) -> list[SearchHit]: ...


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
        "tiktoken",
        "scipy",
    ):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return packages


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
    context_budgets: list[int] | None = None,
) -> dict:
    """Injected implementations own their resources; never serialize clients/settings.

    Retrieval implementations must be local for an offline run. Live providers require
    reviewed cases and an explicit prior estimate; the CLI never constructs one.
    """
    passages = validate_artifact(dataset, artifact)
    retrieval = validate_retrieval_config(retrieval, artifact)
    if context_budgets is not None and (
        not context_budgets
        or any(b not in STANDARD_BUDGETS for b in context_budgets)
        or (any(b != 4 for b in context_budgets) and retrieval.limit < 40)
    ):
        raise ValueError(
            "Context profiles require standard budgets and at least 40 ranked candidates"
        )
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
            provider.model != DEFAULT_MODEL
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
        if context_budgets:
            row["context_profiles"] = {
                str(b): context_profile(case.question, scored_hits, entry, b)
                for b in context_budgets
            }
        if hits is not None:
            budget = (
                {
                    "max_context_chars": provider.context_chars,
                    "mode": provider.context_mode,
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
            "context_scoring": "serialized-provider-prefix-v1",
            "asked_group_rule": "group-id-starts-with-part-",
            "confidence_interval": "Clopper-Pearson-two-sided-95-percent",
            "paired_test": "exact-McNemar-two-sided-binomial",
        },
        "cutoffs": cutoffs,
        "context_budgets": context_budgets,
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
