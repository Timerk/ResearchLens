"""Failure and offline context diagnostics using the existing evidence scorer."""

import argparse
import json
from collections import Counter
from pathlib import Path

from researchlens.answers import prepare_answer_context
from researchlens.artifacts import canonical_hash
from researchlens.evaluation_evidence import (
    CaseEvidence,
    EvidenceLabels,
    TextRange,
    dataset_digest,
    evidence_coverage,
)
from researchlens.evaluation_schema import Dataset
from researchlens.models import SearchHit


def minimal_supports(entry: CaseEvidence) -> list[frozenset[str]]:
    """Label-only oracle: minimal passage sets satisfying all OR/AND alternatives.

    Used after retrieval for diagnosis only. Search/selection never receives labels.
    Character visibility is assessed separately by the existing evidence scorer.
    """
    supports = [frozenset()]
    for group in entry.groups:
        options = [frozenset(span.passage_id for span in option) for option in group.alternatives]
        expanded = sorted({support | option for support in supports for option in options}, key=len)
        minimal = []
        for support in expanded:
            if not any(previous <= support for previous in minimal):
                minimal.append(support)
        supports = minimal
    return supports


def analyze_run(run: dict) -> dict:
    if run["dataset"]["split"] != "development" or not run.get("evidence_labels"):
        raise ValueError("Failure analysis requires labeled development runs")
    labels = EvidenceLabels.model_validate(run["evidence_labels"])
    if labels.review_status != "approved":
        raise ValueError("Failure analysis requires approved development labels")
    if (
        labels.dataset_sha256 != dataset_digest(Dataset.model_validate(run["dataset"]))
        or labels.dataset_sha256 != run["dataset_sha256"]
        or labels.corpus_sha256 != run["corpus"]["source_sha256"]
        or labels.shared_passage_sha256 != run["corpus"]["shared_passage_sha256"]
        or canonical_hash(labels.model_dump(mode="json"))
        != run["evaluation_contract"]["evidence_labels_sha256"]
    ):
        raise ValueError("Failure analysis labels do not match run identities")
    entries = {entry.case_id: entry for entry in labels.cases}
    cases = {case["id"]: case for case in run["dataset"]["cases"]}
    measured = {
        p["passage_id"]: p for p in (run.get("encoding_diagnostics") or {}).get("passages", [])
    }
    results = []
    for row in run["results"]:
        case, entry = cases[row["case_id"]], entries.get(row["case_id"])
        hits = [SearchHit.model_validate(p) for p in row["retrieved_passages"]]
        ids = {hit.id for hit in hits}
        supports = minimal_supports(entry) if entry else []
        within_candidates = [support for support in supports if support <= ids]
        minimum = min(map(len, supports)) if supports else None
        candidate_minimum = min(map(len, within_candidates)) if within_candidates else None
        if entry is None:
            failure = "negative-unscored" if case["expected_abstention"] else "unlabeled-answerable"
        elif row["error"]:
            failure = "retrieval-error"
        elif row["metrics_at_k"]["4"]["complete_evidence"]:
            failure = "complete-at-four"
        elif minimum > 4:
            failure = "labels-require-more-than-four-passages"
        elif candidate_minimum is None:
            failure = "candidate-pool-missing-evidence"
        elif candidate_minimum > 4:
            failure = "candidate-alternatives-require-more-than-four"
        else:
            failure = "ranking-or-selection"
        contexts = {}
        for budget in (4, 6, 8):
            prepared = prepare_answer_context(hits, max_passages=budget)
            coverage = evidence_coverage(
                entry,
                {
                    pid: [TextRange(start=0, end=length)]
                    for pid, length in prepared.diagnostics.visible_chars.items()
                    if length
                },
            )
            contexts[str(budget)] = {
                "coverage": coverage,
                "diagnostics": prepared.diagnostics.model_dump(),
            }
        encoded_coverage = evidence_coverage(
            entry,
            {
                hit.id: [
                    TextRange.model_validate(region)
                    for region in measured[hit.id]["retained_ranges"]
                ]
                if hit.id in measured
                else None
                for hit in hits
            },
        )
        results.append(
            {
                "case_id": case["id"],
                "query_style": case["query_style"],
                "failure": failure,
                "minimum_labeled_passages": minimum,
                "minimum_within_candidates": candidate_minimum,
                "candidate_passage_ids": row["retrieved_passage_ids"],
                "candidate_encoder_coverage": encoded_coverage,
                "contexts": contexts,
            }
        )
    answerable = [row for row in results if row["minimum_labeled_passages"] is not None]
    context_summary = {}
    for budget in (4, 6, 8):
        key = str(budget)
        context_summary[key] = {
            "answerable_cases": sum(not case["expected_abstention"] for case in cases.values()),
            "evidence_labeled_cases": len(answerable),
            "complete_evidence_cases": sum(
                row["contexts"][key]["coverage"]["complete_evidence"] is True for row in answerable
            ),
            "mean_group_coverage": sum(
                row["contexts"][key]["coverage"]["group_coverage"] for row in answerable
            )
            / len(answerable)
            if answerable
            else None,
            "mean_serialized_chars_all_cases": sum(
                row["contexts"][key]["diagnostics"]["serialized_chars"] for row in results
            )
            / len(results),
            "cohorts": {
                style: {
                    "cases": sum(row["query_style"] == style for row in answerable),
                    "complete_evidence_cases": sum(
                        row["query_style"] == style
                        and row["contexts"][key]["coverage"]["complete_evidence"] is True
                        for row in answerable
                    ),
                }
                for style in ("exact-terminology", "paraphrase", "cross-document")
            },
        }
    return {
        "schema_version": 1,
        "run_id": run["run_id"],
        "run_sha256": canonical_hash(run),
        "dataset_sha256": run["dataset_sha256"],
        "evaluation_contract": run["evaluation_contract"],
        "corpus": run["corpus"],
        "generation": "none",
        "description": "Label-only failure oracle and offline context experiments; "
        "no query-time label use or answer generation.",
        "failure_counts": dict(Counter(row["failure"] for row in results)),
        "context_summary": context_summary,
        "cases": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    result = analyze_run(json.loads(args.run.read_bytes()))
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"failures": result["failure_counts"], "contexts": result["context_summary"]}))


if __name__ == "__main__":
    main()
