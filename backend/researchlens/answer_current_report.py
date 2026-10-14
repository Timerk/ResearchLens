"""Summarize the five current-corpus development runs with reliability exclusions."""

import argparse
import hashlib
import json
from pathlib import Path

from researchlens.answer_evaluation import quality_report
from researchlens.answer_judge_freeze import assert_frozen
from researchlens.answer_judge_review import REVIEW
from researchlens.artifacts import canonical_hash
from researchlens.evaluation_metrics import exact_mcnemar

CONFIGURATIONS = ("tfidf4", "qwen4", "qwen12k", "qwen16k", "bge16k")


def report(folder, ledger):
    frozen = assert_frozen()
    validation = json.loads((REVIEW / "validation-results.json").read_bytes())
    runs = [json.loads((folder / name / "run.json").read_bytes()) for name in CONFIGURATIONS]
    # Reuse the established comparison identity, completeness, cost and error checks.
    detailed = quality_report(runs)
    costs = json.loads(ledger.read_bytes())
    if any(not call["usage_known"] for call in costs["calls"]):
        raise ValueError("Report unknown paid-call costs explicitly before completing the study")
    charged = sum(call["charged_usd"] for call in costs["calls"])
    if charged > 3:
        raise ValueError("Study exceeds $3")
    cases = {case["id"]: case for case in runs[0]["dataset"]["cases"]}
    answerable = {cid for cid, case in cases.items() if not case["expected_abstention"]}
    negatives = set(cases) - answerable
    summaries = []
    states = {}
    for name, run in zip(CONFIGURATIONS, runs, strict=True):
        rows = {row["case_id"]: row for row in run["results"]}
        if any(row["error"] for row in rows.values()):
            raise ValueError("Incomplete or failed generation cannot qualify as a full comparison")
        states[name] = {
            cid: row["answer_quality"]["required_claims_met"]
            for cid, row in rows.items()
            if cid in answerable
        }
        summaries.append(
            {
                "configuration": name,
                "cases": len(rows),
                "complete_required_claims": sum(value is True for value in states[name].values()),
                "required_claim_cases": len(answerable),
                "unknown_required_claim_cases": sum(
                    value is None for value in states[name].values()
                ),
                "false_abstentions": sum(
                    not row["answer_quality"]["abstention_correct"]
                    for cid, row in rows.items()
                    if cid in answerable
                ),
                "correct_negative_abstentions": sum(
                    rows[cid]["answer_quality"]["negative_abstention_correct"] is True
                    for cid in negatives
                ),
                "negative_cases": len(negatives),
                "generation_calls": sum(bool(row.get("raw_generation")) for row in rows.values()),
                "judge_calls": sum(bool(row.get("raw_judgment")) for row in rows.values()),
                "recorded_usage_cost_usd": sum(
                    (row.get("estimated_api_cost_usd") or 0)
                    + (row.get("judge_estimated_api_cost_usd") or 0)
                    for row in rows.values()
                ),
                "uncertified_diagnostics": {
                    "qualification_preserved": sum(
                        row["answer_quality"]["qualifications_preserved"] is True
                        for cid, row in rows.items()
                        if cid in answerable
                    ),
                    "forbidden_violations": sum(
                        row["answer_quality"]["no_forbidden_claims"] is False
                        for row in rows.values()
                    ),
                    "unsupported_citation_answers": sum(
                        row["answer_quality"]["citation_support"] is False for row in rows.values()
                    ),
                    "unknown_citation_answers": sum(
                        row["answer_quality"]["citation_support"] is None
                        for row in rows.values()
                        if row["answer"]["sections"]
                    ),
                    "meaning": "Not calibrated decision evidence; do not use the composite",
                },
            }
        )
    reliable_metrics = {"required_claims_met", "negative_abstention_correct"}
    comparisons = [
        comparison for comparison in detailed["paired"] if comparison["metric"] in reliable_metrics
    ]
    return {
        "schema_version": 1,
        "split": "development",
        "held_out_generation_or_retrieval": 0,
        "frozen_contract_sha256": canonical_hash(frozen["contract"]),
        "validation_results_sha256": hashlib.sha256(
            (REVIEW / "validation-results.json").read_bytes()
        ).hexdigest(),
        "reliable_types": validation["reliable_types"],
        "excluded_types": [
            kind for kind in validation["frozen_judge"] if kind not in validation["reliable_types"]
        ],
        "plan_sha256": runs[0]["answer_evaluation"]["plan_sha256"],
        "summaries": summaries,
        "primary_required_claim_comparison": exact_mcnemar(states["qwen4"], states["qwen12k"]),
        "descriptive_qwen16k_vs_four": exact_mcnemar(states["qwen4"], states["qwen16k"]),
        "comparisons_of_reliable_metrics": comparisons,
        "total_phase2_recorded_usage_cost_usd": charged,
        "total_phase2_paid_calls": len(costs["calls"]),
        "prices": costs["prices"],
        "cost_scope": (
            "Uncached token usage at owner-supplied rates; "
            "not an independently verified billing total"
        ),
        "run_hashes": {
            name: canonical_hash(run) for name, run in zip(CONFIGURATIONS, runs, strict=True)
        },
        "current_corpus": runs[0]["corpus"],
        "dataset_sha256": runs[0]["dataset_sha256"],
        "decision_applied": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    result = report(args.runs, args.ledger)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key
                in (
                    "summaries",
                    "primary_required_claim_comparison",
                    "total_phase2_recorded_usage_cost_usd",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
