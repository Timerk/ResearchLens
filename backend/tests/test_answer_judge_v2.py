from types import SimpleNamespace

import pytest
from researchlens.answer_evaluation import Prices
from researchlens.answer_judge_v2 import quote_verified
from researchlens.answer_study_budget import StudyBudget


def test_receipt_normalization_preserves_substantive_text():
    passage = "Intel®core i7 and 8 GB RAM. After ∆t the charge is accumulated."
    assert quote_verified("Intel core i7 and 8 GB RAM.", passage)
    assert quote_verified("After Δt the charge is accumulated.", passage)
    assert not quote_verified("Intel core i7 and 80 GB RAM.", passage)
    assert not quote_verified("Intel core i7 and 8 MB RAM.", passage)
    assert not quote_verified("After Δt the charge is not accumulated.", passage)
    assert not quote_verified("An invented result.", passage)
    assert not quote_verified("®", passage)
    assert not quote_verified(" ", passage)


def test_shared_cap_keeps_unknown_costs_and_releases_only_verified_usage(tmp_path):
    prices = Prices(
        date="2026-10-13", provenance="test", input_per_million=0.1, output_per_million=0.5
    )
    path = tmp_path / "study.json"
    budget = StudyBudget(path, 3, prices)
    budget.reserve("unknown", 2)
    with pytest.raises(ValueError, match="cap exceeded"):
        StudyBudget(path, 3, prices).reserve("next", 2)
    budget.settle("unknown", None)
    assert budget.read()["calls"][0]["charged_usd"] == 2
    budget.settle("unknown", SimpleNamespace(input_tokens=100, output_tokens=100))
    assert budget.read()["calls"][0]["charged_usd"] == pytest.approx(0.00006)
    budget.reserve("next", 2)
    with pytest.raises(ValueError, match="repeated paid call"):
        budget.reserve("next", 0.001)
    with pytest.raises(ValueError, match="cannot change"):
        StudyBudget(path, 2, prices)


def test_guarded_review_rejects_unapproved_plan_without_a_client(tmp_path, monkeypatch):
    from researchlens import answer_judge_experiment as module

    monkeypatch.setattr(module, "OpenAI", lambda **kw: pytest.fail("Paid client constructed"))
    with pytest.raises(ValueError, match="approval"):
        module.run_review(SimpleNamespace(approve_plan_sha256="wrong"), {"mode": "test"}, None)
