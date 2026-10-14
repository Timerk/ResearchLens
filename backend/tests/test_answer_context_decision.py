from copy import deepcopy

from researchlens.answer_context_decision import decide


def fixture():
    report = {
        "reliable_types": ["required_claim", "abstention"],
        "excluded_types": ["qualification", "citation", "forbidden_claim"],
        "primary_required_claim_comparison": {
            "paired_cases": 36,
            "excluded_unscored_cases": 0,
            "gains": 8,
            "losses": 0,
            "p_two_sided": 0.0078125,
        },
        "summaries": [
            {"configuration": name, "correct_negative_abstentions": 14}
            for name in ("qwen4", "qwen12k")
        ],
    }
    rule = {
        "primary_comparison": {"baseline": "qwen4", "candidate": "qwen12k"},
        "required_claim_p_threshold": 0.05,
        "if_pass": "promote",
        "if_fail_or_unassessable": "keep",
    }
    rows = [
        {
            "answer": {"sections": ["claim"]},
            "answer_quality": {
                "citation_support": True,
                "no_forbidden_claims": True,
            },
        }
    ]
    return report, rule, rows


def test_significant_gain_cannot_waive_uncertified_safety_guards():
    report, rule, rows = fixture()
    result = decide(report, rule, rows, rows)
    assert result["conditions"]["required_claim_gain_significant"] is True
    assert result["decision"] == "keep_defaults"
    assert len(result["unassessable_conditions"]) == 2


def test_decision_requires_all_guards_and_the_registered_primary():
    report, rule, rows = fixture()
    report["reliable_types"] += ["citation", "forbidden_claim"]
    report["excluded_types"] = ["qualification"]
    assert decide(report, rule, rows, rows)["decision"] == "promote_per_tier_budgets"
    unknown = deepcopy(rows)
    unknown[0]["answer_quality"]["citation_support"] = None
    assert decide(report, rule, rows, unknown)["decision"] == "keep_defaults"
    unsupported = deepcopy(rows)
    unsupported[0]["answer_quality"]["citation_support"] = False
    assert decide(report, rule, rows, unsupported)["decision"] == "keep_defaults"
    forbidden = deepcopy(rows)
    forbidden[0]["answer_quality"]["no_forbidden_claims"] = False
    assert decide(report, rule, rows, forbidden)["decision"] == "keep_defaults"
    report["summaries"][1]["correct_negative_abstentions"] = 13
    assert decide(report, rule, rows, rows)["decision"] == "keep_defaults"
    report["summaries"][1]["correct_negative_abstentions"] = 14
    report["primary_required_claim_comparison"]["p_two_sided"] = 0.05
    report["descriptive_qwen16k_vs_four"] = {"p_two_sided": 0.001}
    assert decide(report, rule, rows, rows)["decision"] == "keep_defaults"
