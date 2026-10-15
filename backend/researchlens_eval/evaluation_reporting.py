"""Offline-first evaluation: python -m researchlens.evaluation --help."""

import json
from statistics import median

from researchlens.artifacts import (
    canonical_hash,
)

from researchlens_eval.context_evaluation import (
    context_report_details,
)
from researchlens_eval.evaluation_core import digest as digest
from researchlens_eval.evaluation_core import encoded as encoded
from researchlens_eval.evaluation_metrics import (
    comparison_details,
    cutoff_summary,
    percentile_nearest_rank,
)
from researchlens_eval.evaluation_schema import (
    CaseReview,
    ClaimReview,
    Review,
)


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
        "Differences of 1-3 complete questions out of 36 are not significant at 5% "
        "under the exact paired McNemar test. Context coverage is not answer quality.",
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
    lines.extend(context_report_details(runs))
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
