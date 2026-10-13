from copy import deepcopy
from types import SimpleNamespace

import pytest
from researchlens.answer_evaluation import (
    CitationDecision,
    CostGuard,
    Decision,
    Judgment,
    all_decided,
    execute,
    score,
)
from researchlens.answers import prepare_answer_context
from researchlens.evaluation import load_dataset
from researchlens.ingest import ROOT
from researchlens.models import SearchHit


@pytest.fixture
def scoring():
    case = load_dataset(ROOT / "evaluation/datasets/technical-development.json").cases[0]
    hit = SearchHit(
        id="test:p1",
        document_id="test",
        title="Test",
        source_url="https://example.com/test",
        license="CC-BY-4.0",
        paragraph=1,
        text="The approved visible measurement.",
        kind="technical",
        score=1,
    )
    prepared = prepare_answer_context([hit])
    answer = {
        "status": "answered",
        "sections": [{"text": "The measurement was reported.", "citation_ids": [hit.id]}],
    }
    decision = Decision(value=True, reason="Matches approved evidence")
    judgment = Judgment(
        required_claims=[decision] * len(case.required_claims),
        qualifications=[decision] * len(case.required_qualifications),
        forbidden_claims=[Decision(value=False, reason="Not asserted")]
        * len(case.forbidden_claims),
        citations=[
            CitationDecision(
                value=True,
                reason="Visible support",
                section_index=0,
                citation_id=hit.id,
                evidence_quotes=[hit.text],
            )
        ],
        sections_fully_supported=[decision],
    )
    return case, prepared, answer, judgment


def test_correct_abstention_does_not_require_negative_qualification_prose():
    case = load_dataset(ROOT / "evaluation/datasets/technical-development.json").cases[-1]
    scored = score(
        case, {"status": "insufficient_evidence", "sections": []}, prepare_answer_context([])
    )
    assert scored["answer_correct"] is True
    assert scored["negative_abstention_correct"] is True
    assert scored["qualifications_preserved"] is None
    assert (
        score(case, {"status": "no_matches", "sections": []}, prepare_answer_context([]))[
            "negative_abstention_correct"
        ]
        is False
    )


def test_judge_cannot_verify_invented_or_truncated_quotes(scoring):
    case, prepared, answer, judgment = scoring
    assert score(case, answer, prepared, judgment)["answer_correct"] is True
    judgment.citations[0].evidence_quotes = ["An invisible measurement."]
    scored = score(case, answer, prepared, judgment)
    assert scored["citation_ids_valid"] is True
    assert scored["citation_support"] is None
    assert scored["answer_correct"] is None


def test_valid_ids_do_not_establish_support_and_judge_cannot_override_unknown_id(scoring):
    case, prepared, answer, judgment = scoring
    judgment.citations[0].value = False
    assert score(case, answer, prepared, judgment)["answer_correct"] is False
    answer["sections"][0]["citation_ids"] = ["unsupplied"]
    judgment.citations[0].citation_id = "unsupplied"
    judgment.citations[0].value = True
    assert score(case, answer, prepared, judgment)["citation_ids_valid"] is False


def test_incomplete_or_misaligned_judgments_are_rejected(scoring):
    case, prepared, answer, judgment = scoring
    original = deepcopy(judgment)
    judgment.required_claims = []
    with pytest.raises(ValueError, match="incomplete"):
        score(case, answer, prepared, judgment)
    judgment = original
    judgment.citations[0].section_index = 10
    with pytest.raises(ValueError):
        score(case, answer, prepared, judgment)


def test_cost_cap_reserves_failed_calls_and_rejects_invalid_caps():
    for invalid in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            CostGuard(invalid)
    guard = CostGuard(0.03)
    guard.reserve(0.02)
    with pytest.raises(ValueError, match="cap exceeded"):
        guard.reserve(0.02)
    assert guard.reserved == 0.02


def test_approval_and_cap_checked_before_client_creation(tmp_path, monkeypatch):
    from researchlens import answer_evaluation as module
    from researchlens.artifacts import canonical_hash

    monkeypatch.setattr(module, "OpenAI", lambda **kw: pytest.fail("Paid client constructed"))
    plan = {"total_reserved_usd": 1}
    args = SimpleNamespace(approve_plan_sha256="wrong", max_cost_usd=2, output=tmp_path / "run")
    with pytest.raises(ValueError, match="approval"):
        execute(args, None, None, None, plan, None)
    args.approve_plan_sha256 = canonical_hash(plan)
    args.max_cost_usd = 0.5
    with pytest.raises(ValueError, match="exceeds"):
        execute(args, None, None, None, plan, None)
    assert not args.output.exists()


def test_unknown_scores_are_not_credited():
    assert all_decided([True, None]) is None
    assert all_decided([False, None]) is False


def test_missing_content_and_forbidden_assertions_fail_quality(scoring):
    case, prepared, answer, judgment = scoring
    judgment.required_claims[0].value = False
    judgment.qualifications[0].value = False
    judgment.forbidden_claims[0].value = True
    result = score(case, answer, prepared, judgment)
    assert result["required_claim_coverage"] == 0
    assert result["qualification_preservation"] == 0
    assert result["forbidden_claims"] == [True]
    assert result["no_forbidden_claims"] is False
    assert result["answer_correct"] is False


def test_report_keeps_negatives_and_unknown_pairs_separate(monkeypatch):
    from researchlens import evaluation
    from researchlens.answer_evaluation import METRICS, quality_report

    monkeypatch.setattr(evaluation, "comparison_report", lambda *args: "")
    dataset = load_dataset(ROOT / "evaluation/datasets/technical-development.json")
    rows = []
    for case in dataset.cases:
        values = dict.fromkeys(METRICS, True)
        values.update(
            negative_abstention_correct=True if case.expected_abstention else None,
            required_claim_coverage=None if case.expected_abstention else 1.0,
            qualification_preservation=None if case.expected_abstention else 1.0,
        )
        rows.append({"case_id": case.id, "answer_quality": values})
    baseline = {
        "run_id": "before",
        "dataset": dataset.model_dump(mode="json"),
        "results": rows,
        "answer_evaluation": {
            "plan_sha256": "one-plan",
            "prices": {
                "date": "2026-10-13",
                "provenance": "test",
                "input_per_million": 0.1,
                "output_per_million": 0.5,
            },
        },
    }
    baseline["results"][0]["answer_quality"]["answer_correct"] = False
    candidate = deepcopy(baseline)
    candidate["run_id"] = "after"
    candidate["results"][0]["answer_quality"]["answer_correct"] = True
    report = quality_report([baseline, candidate])
    overall = next(
        p for p in report["paired"] if p["cohort"] == "all" and p["metric"] == "answer_correct"
    )
    assert overall["paired_cases"] == 50
    assert overall["gains"] == 1 and overall["losses"] == 0
    negatives = next(
        p
        for p in report["paired"]
        if p["cohort"] == "all" and p["metric"] == "negative_abstention_correct"
    )
    assert negatives["paired_cases"] == 14
    assert negatives["excluded_unscored_cases"] == 36
    assert len(report["fractional_paired"]) == 12  # Overall plus five cohorts.


def test_plan_has_generation_and_judge_without_creating_paid_client(scoring, monkeypatch):
    from researchlens import answer_evaluation as module

    monkeypatch.setattr(module, "OpenAI", lambda **kwargs: pytest.fail("Paid client"))
    case, prepared, *_ = scoring
    dataset = SimpleNamespace(cases=[case], model_dump=lambda **kw: {"case": case.id})
    hit = prepared.supplied[0]
    run = {"results": [{"case_id": case.id, "retrieved_passages": [hit.model_dump()]}]}
    prices = module.Prices(
        date="2026-10-13", provenance="test", input_per_million=0.1, output_per_million=0.5
    )
    plan = module.make_plan(dataset, {}, [run, run], prices, ["tfidf4", "qwen12k"])
    assert plan["total_reserved_usd"] > sum(
        e["generation_cost_estimate_usd"] + e["judge_cost_estimate_usd"]
        for e in plan["configurations"]
    )
    assert all(
        e["generation_calls"] == e["judge_calls_upper_bound"] == 1 for e in plan["configurations"]
    )


@pytest.mark.parametrize("invalid_id", [False, True])
def test_execution_calls_real_provider_and_checkpoints_raw_judge(
    scoring, tmp_path, monkeypatch, invalid_id
):
    import json

    from researchlens import answer_evaluation as module
    from researchlens.artifacts import canonical_hash
    from researchlens.models import AnswerSection, GeneratedAnswer

    case, prepared, _, judgment = scoring
    calls = []
    usage = SimpleNamespace(
        input_tokens=100,
        output_tokens=50,
        model_dump=lambda: {"input_tokens": 100, "output_tokens": 50},
    )

    def parse(**kwargs):
        calls.append(kwargs)
        generated = GeneratedAnswer(
            status="answered",
            sections=[
                AnswerSection(
                    text="The measurement was reported.",
                    citation_ids=["not-supplied" if invalid_id else prepared.items[0]["id"]],
                )
            ],
        )
        parsed = generated if kwargs["text_format"] is GeneratedAnswer else judgment
        return SimpleNamespace(
            status="completed",
            output_parsed=parsed,
            usage=usage,
            model_dump=lambda **kw: {"status": "completed", "raw": "saved"},
        )

    client = SimpleNamespace(responses=SimpleNamespace(parse=parse), close=lambda: None)
    monkeypatch.setattr(module, "OpenAI", lambda **kw: client)
    monkeypatch.setattr(module.Settings, "from_env", lambda *args: SimpleNamespace(api_key="test"))
    dataset = SimpleNamespace(cases=[case], model_dump=lambda **kw: {"case": case.id})
    run = {
        "run_id": "archived",
        "code": {"commit": "pinned"},
        "results": [
            {"case_id": case.id, "retrieved_passages": [p.model_dump() for p in prepared.supplied]}
        ],
    }
    prices = module.Prices(
        date="2026-10-13", provenance="test", input_per_million=0.1, output_per_million=0.5
    )
    plan = module.make_plan(dataset, {}, [run, run], prices, ["tfidf4"])
    # The one-case fixture intentionally bypasses CLI's strict development study loading.
    monkeypatch.setattr(module, "spot_check_template", lambda run: {"fixture": True})
    args = SimpleNamespace(
        approve_plan_sha256=canonical_hash(plan),
        max_cost_usd=1,
        env_file=tmp_path / ".env",
        output=tmp_path / "answers",
    )
    if invalid_id:
        with pytest.raises(ValueError, match="stopped"):
            module.execute(args, dataset, {}, [run, run], plan, prices)
    else:
        module.execute(args, dataset, {}, [run, run], plan, prices)
    assert len(calls) == (1 if invalid_id else 2)
    assert all(c["model"] == "gpt-6-luna" for c in calls)
    assert json.loads(calls[0]["input"])["passages"] == prepared.items
    result = json.loads((args.output / "tfidf4/run.json").read_bytes())
    row = result["results"][0]
    assert row["raw_generation"]["raw"] == "saved"
    if invalid_id:
        assert row["answer_quality"]["citation_ids_valid"] is False
        assert row["answer_quality"]["answer_correct"] is False
        assert row["input_tokens"] == 100
    else:
        assert row["raw_judgment"]["raw"] == "saved"
        assert row["answer_quality"]["answer_correct"] is True
    assert json.loads((args.output / "cost-ledger.json").read_bytes())["reserved_usd"] > 0
    reservation = (args.output / "cost-ledger.json").read_bytes()
    args.resume = True
    if invalid_id:
        with pytest.raises(ValueError, match="never repeats"):
            module.execute(args, dataset, {}, [run, run], plan, prices)
    else:
        module.execute(args, dataset, {}, [run, run], plan, prices)
    assert len(calls) == (1 if invalid_id else 2)
    assert (args.output / "cost-ledger.json").read_bytes() == reservation


def test_duplicate_citation_subclaims_are_conservatively_combined(scoring):
    case, prepared, answer, judgment = scoring
    duplicate = judgment.citations[0].model_copy(deep=True)
    judgment.citations.append(duplicate)
    assert score(case, answer, prepared, judgment)["citation_support"] is True
    duplicate.value = False
    assert score(case, answer, prepared, judgment)["citation_support"] is False
