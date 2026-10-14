"""Apply the registered context-default rule without admitting unreliable endpoints."""

import argparse
import hashlib
import json
from pathlib import Path

from researchlens.answer_judge_freeze import assert_frozen
from researchlens.answer_judge_review import REVIEW
from researchlens.artifacts import canonical_hash


def safety_guard(reliable, kind, field, before, after, *, citations=False):
    if kind not in reliable:
        return None

    def violations(rows):
        scored = [row for row in rows if not citations or row["answer"]["sections"]]
        values = [row["answer_quality"][field] for row in scored]
        if any(value is None for value in values):
            return None
        return sum(value is False for value in values)

    first, second = violations(before), violations(after)
    return None if first is None or second is None else second <= first


def decide(result, rule, before, after):
    reliable = set(result["reliable_types"])
    primary = result["primary_required_claim_comparison"]
    summaries = {summary["configuration"]: summary for summary in result["summaries"]}
    baseline = summaries[rule["primary_comparison"]["baseline"]]
    candidate = summaries[rule["primary_comparison"]["candidate"]]
    required = bool(
        "required_claim" in reliable
        and primary["paired_cases"] == 36
        and primary["excluded_unscored_cases"] == 0
        and primary["gains"] > primary["losses"]
        and primary["p_two_sided"] < rule["required_claim_p_threshold"]
    )
    negative = (
        candidate["correct_negative_abstentions"] >= baseline["correct_negative_abstentions"]
        if "abstention" in reliable
        else None
    )
    unsupported = safety_guard(
        reliable, "citation", "citation_support", before, after, citations=True
    )
    forbidden = safety_guard(reliable, "forbidden_claim", "no_forbidden_claims", before, after)
    conditions = {
        "required_claim_gain_significant": required,
        "unsupported_claims_do_not_increase": unsupported,
        "forbidden_claims_do_not_increase": forbidden,
        "negative_abstention_does_not_worsen": negative,
    }
    promote = all(value is True for value in conditions.values())
    return {
        "decision": "promote_per_tier_budgets" if promote else "keep_defaults",
        "conditions": conditions,
        "primary_comparison": rule["primary_comparison"],
        "primary_required_claim_comparison": primary,
        "excluded_types": result["excluded_types"],
        "unassessable_conditions": [key for key, value in conditions.items() if value is None],
        "defaults": rule["if_pass"] if promote else rule["if_fail_or_unassessable"],
        "secondary_comparisons_used_to_replace_primary": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Decision output already exists")
    frozen = assert_frozen()
    result = json.loads(args.results.read_bytes())
    if result["frozen_contract_sha256"] != canonical_hash(frozen["contract"]):
        raise ValueError("Results differ from the judge freeze")
    rule_path = REVIEW / "context-decision-rule.json"
    rule = json.loads(rule_path.read_bytes())
    runs = []
    for name in rule["primary_comparison"].values():
        run = json.loads((args.runs / name / "run.json").read_bytes())
        if canonical_hash(run) != result["run_hashes"][name]:
            raise ValueError("Decision input run hash mismatch")
        runs.append(run["results"])
    decision = decide(result, rule, *runs)
    decision.update(
        results_sha256=hashlib.sha256(args.results.read_bytes()).hexdigest(),
        registered_rule_sha256=hashlib.sha256(rule_path.read_bytes()).hexdigest(),
    )
    args.output.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
