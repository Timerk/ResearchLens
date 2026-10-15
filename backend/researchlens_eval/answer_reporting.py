"""Answer scoring commands for the existing evaluation runner."""

import hashlib
import itertools
from statistics import mean

from researchlens.artifacts import canonical_hash

from researchlens_eval.answer_constants import STUDY_CASES
from researchlens_eval.answer_scoring import Prices
from researchlens_eval.evaluation_metrics import binomial_ci, exact_mcnemar
from researchlens_eval.evaluation_reporting import comparison_report

METRICS = [
    "answer_correct",
    "required_claims_met",
    "qualifications_preserved",
    "no_forbidden_claims",
    "citation_ids_valid",
    "citation_support",
    "negative_abstention_correct",
]


def quality_report(runs):

    comparison_report(runs, [None] * len(runs))  # Reuse controlled-comparison identity checks.
    if any(
        len(r["results"]) != STUDY_CASES or r["dataset"]["split"] != "development" for r in runs
    ):
        raise ValueError("Report requires complete development runs")
    for run in runs:
        if {r["case_id"] for r in run["results"]} != {c["id"] for c in run["dataset"]["cases"]}:
            raise ValueError("Missing or duplicate answer cases")
    if len({r["answer_evaluation"]["plan_sha256"] for r in runs}) != 1:
        raise ValueError("Compare runs from one approved plan")
    cases = {c["id"]: c for c in runs[0]["dataset"]["cases"]}
    cohorts = ["all", *sorted({c["query_style"] for c in cases.values()})]
    summaries, comparisons, fractional = [], [], []
    for cohort in cohorts:
        ids = {cid for cid, c in cases.items() if cohort == "all" or c["query_style"] == cohort}
        for run in runs:
            for metric in METRICS:
                values = [
                    r["answer_quality"][metric] for r in run["results"] if r["case_id"] in ids
                ]
                measured = [v for v in values if v is not None]
                successes = sum(v is True for v in measured)
                summaries.append(
                    {
                        "run": run["run_id"],
                        "cohort": cohort,
                        "metric": metric,
                        "successes": successes,
                        "scored": len(measured),
                        "unscored_or_not_applicable": len(values) - len(measured),
                        "ci95": binomial_ci(successes, len(measured)),
                    }
                )
        for before, after in itertools.combinations(runs, 2):
            for metric in METRICS:
                states = [
                    {
                        r["case_id"]: r["answer_quality"][metric]
                        for r in run["results"]
                        if r["case_id"] in ids
                    }
                    for run in (before, after)
                ]
                comparisons.append(
                    {
                        "baseline": before["run_id"],
                        "candidate": after["run_id"],
                        "cohort": cohort,
                        "metric": metric,
                        **exact_mcnemar(*states),
                    }
                )
            import numpy as np

            first = {r["case_id"]: r["answer_quality"] for r in before["results"]}
            second = {r["case_id"]: r["answer_quality"] for r in after["results"]}
            for metric in ("required_claim_coverage", "qualification_preservation"):
                deltas = [
                    second[cid][metric] - first[cid][metric]
                    for cid in sorted(ids)
                    if first[cid][metric] is not None and second[cid][metric] is not None
                ]
                interval = None
                if deltas:
                    rng = np.random.default_rng(20261013)
                    samples = rng.choice(deltas, (10000, len(deltas)), replace=True).mean(axis=1)
                    interval = np.quantile(samples, [0.025, 0.975]).tolist()
                fractional.append(
                    {
                        "baseline": before["run_id"],
                        "candidate": after["run_id"],
                        "cohort": cohort,
                        "metric": metric,
                        "paired_cases": len(deltas),
                        "mean_paired_delta": mean(deltas) if deltas else None,
                        "bootstrap_ci95": interval,
                        "method": "paired-percentile-bootstrap-10000-seed-20261013",
                    }
                )
    costs = []
    for run in runs:
        prices = Prices.model_validate(run["answer_evaluation"]["prices"])
        generation_input = generation_output = judge_input_tokens = judge_output_tokens = 0
        unknown = 0
        for row in run["results"]:
            no_call = (row.get("answer") or {}).get("status") == "no_matches"
            if row.get("input_tokens") is not None and row.get("output_tokens") is not None:
                generation_input += row["input_tokens"]
                generation_output += row["output_tokens"]
            elif not no_call:
                unknown += 1
            if row.get("judge_usage"):
                judge_input_tokens += row["judge_usage"]["input_tokens"]
                judge_output_tokens += row["judge_usage"]["output_tokens"]
            elif row.get("raw_judgment") or (row.get("error") or {}).get("stage") == "judge":
                unknown += 1
        costs.append(
            {
                "run": run["run_id"],
                "generation_input_tokens": generation_input,
                "generation_output_tokens": generation_output,
                "judge_input_tokens": judge_input_tokens,
                "judge_output_tokens": judge_output_tokens,
                "unknown_usage_calls": unknown,
                "generation_cost_usd": prices.cost(generation_input, generation_output),
                "judge_cost_usd": prices.cost(judge_input_tokens, judge_output_tokens),
            }
        )
    return {
        "summaries": summaries,
        "paired": comparisons,
        "fractional_paired": fractional,
        "costs": costs,
        "errors": {
            run["run_id"]: [
                {"case_id": r["case_id"], "error": r["error"]}
                for r in run["results"]
                if r.get("error")
            ]
            for run in runs
        },
        "caution": "Exploratory development tests, no multiplicity correction. "
        "Unknown decisions excluded, not credited. Judge reliability needs review.",
    }


def spot_check_template(run):
    # Stable sample, two cases per cohort, independent of quality outcomes.
    cases = {c["id"]: c for c in run["dataset"]["cases"]}
    selected = []
    for cohort in sorted({c["query_style"] for c in cases.values()}):
        rows = sorted(
            (r for r in run["results"] if cases[r["case_id"]]["query_style"] == cohort),
            key=lambda r: hashlib.sha256(r["case_id"].encode()).hexdigest(),
        )[:2]
        selected.extend(
            {
                "case_id": r["case_id"],
                "cohort": cohort,
                "human_scores": {m: None for m in METRICS},
                "evidence_notes": "",
            }
            for r in rows
        )
    return {
        "run_sha256": canonical_hash(run),
        "reviewer": None,
        "cases": selected,
        "instructions": "Independently score saved answers against approved claims and "
        "visible evidence spans. Complete before consulting judge scores. "
        "null means unresolved or not applicable; retain evidence notes.",
    }


def reliability(run, review):
    if review["run_sha256"] != canonical_hash(run) or not review.get("reviewer"):
        raise ValueError("Independent reviewer and matching run hash required")
    if [c["case_id"] for c in review["cases"]] != [
        c["case_id"] for c in spot_check_template(run)["cases"]
    ]:
        raise ValueError("Review must use the preselected sample")
    rows = {r["case_id"]: r for r in run["results"]}
    result = {}
    for metric in METRICS:
        pairs = []
        semantic_pairs = []
        semantic_unknown = 0
        for case in review["cases"]:
            human = case["human_scores"][metric]
            if human is not None and (
                type(human) is not bool or not case["evidence_notes"].strip()
            ):
                raise ValueError("Boolean review scores require evidence notes")
            judge = rows[case["case_id"]]["answer_quality"][metric]
            if (
                human is not None
                and judge is None
                and rows[case["case_id"]].get("raw_judgment")
                and metric not in ("citation_ids_valid", "negative_abstention_correct")
            ):
                semantic_unknown += 1
            if human is not None and judge is not None:
                pairs.append(human == judge)
                if rows[case["case_id"]].get("raw_judgment") and metric not in (
                    "citation_ids_valid",
                    "negative_abstention_correct",
                ):
                    semantic_pairs.append(human == judge)
        result[metric] = {
            "agreement": sum(pairs),
            "compared": len(pairs),
            "ci95": binomial_ci(sum(pairs), len(pairs)),
            "judge_only_agreement": sum(semantic_pairs),
            "judge_only_compared": len(semantic_pairs),
            "judge_only_ci95": binomial_ci(sum(semantic_pairs), len(semantic_pairs)),
            "judge_only_unresolved": semantic_unknown,
        }
    return result
