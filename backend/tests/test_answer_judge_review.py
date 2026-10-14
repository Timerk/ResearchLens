from researchlens.answer_judge_review import agreement


def test_unknown_and_uncertain_do_not_inflate_accuracy():
    items = [{"id": str(i), "type": "citation"} for i in range(4)]
    grades = {
        "0": {"verdict": "PASS"},
        "1": {"verdict": "FAIL"},
        "2": {"verdict": "PASS"},
        "3": {"verdict": "UNCERTAIN"},
    }
    result = agreement(items, grades, {"0": True, "1": False, "2": None, "3": True})["citation"]
    assert result["accuracy_all_items"] == 0.5
    assert result["accuracy_decidable_pairs"] == 1
    assert result["cohens_kappa"] == 1
    assert result["owner_uncertain"] == result["judge_unknown"] == 1
    assert not result["acceptance_bar_met"]


def test_single_class_agreement_cannot_certify_kappa():
    result = agreement(
        [{"id": "G001", "type": "forbidden_claim"}],
        {"G001": {"verdict": "PASS"}},
        {"G001": True},
    )["forbidden_claim"]
    assert result["accuracy_all_items"] == 1
    assert result["cohens_kappa"] is None
    assert not result["acceptance_bar_met"]
