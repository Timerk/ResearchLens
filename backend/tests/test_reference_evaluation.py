from researchlens.models import SearchHit
from researchlens.reference_evaluation import (
    compare_references,
    reference_scores,
    summarize_references,
)


def fixture():
    hits = [SearchHit(
        id=f"fixture:p{i}:w0", document_id="a" if i < 5 else "b", title="Fixture",
        source_url=None, license="CC0", kind="synthetic", paragraph=i,
        text="evidence", score=1 / i,
    ).model_dump() for i in range(1, 7)]
    case = {"id": "positive", "expected_abstention": False,
            "expected_source_ids": ["a", "b"],
            "references": [{"passage_id": "fixture:p1:w0"},
                           {"passage_id": "fixture:p5:w0"},
                           {"passage_id": "fixture:p5:w0"}]}
    return case, {"case_id": "positive", "error": None, "retrieved_passages": hits}


def test_strict_cutoff_and_all_references_differ_from_character_context():
    case, row = fixture()
    four = reference_scores(case, row, 4)
    large = reference_scores(case, row, 12000)
    assert four["passage_recall_at_4"] == large["passage_recall_at_4"] == 0.5
    assert four["mrr_at_4"] == large["mrr_at_4"] == 1
    assert four["complete_evidence"] is False
    assert four["both_documents"] is False
    assert large["complete_evidence"] is True
    assert large["both_documents"] is True
    # An irrelevant passage from the second document satisfies the document metric.
    case["references"][1]["passage_id"] = "absent"
    assert reference_scores(case, row, 12000)["both_documents"] is True
    assert reference_scores(case, row, 12000)["complete_evidence"] is False


def test_negatives_errors_and_empty_visible_text():
    case, row = fixture()
    for refs in ([], case["references"]):
        negative = {**case, "expected_abstention": True, "references": refs}
        assert reference_scores(negative, row, 4) == {"case_id": "positive", "scored": False}
    row["error"] = {"stage": "retrieval"}
    scored = reference_scores(case, row, 12000)
    assert scored["mrr_at_4"] == scored["passage_recall_at_4"] == 0
    assert scored["context_hit"] is False
    row["error"] = None
    row["retrieved_passages"][0]["text"] = ""
    assert reference_scores(case, row, 4)["context_hit"] is False


def test_nonbinomial_intervals_and_paired_denominators():
    case, row = fixture()
    negative = {**case, "id": "negative", "expected_abstention": True}
    run = {"dataset": {"cases": [case, negative]},
           "results": [row, {**row, "case_id": "negative"}]}
    first, a = summarize_references(run, 4)
    second, b = summarize_references(run, 12000)
    assert first["metrics"]["complete_evidence"]["denominator"] == 1
    assert first["metrics"]["mrr_at_4"]["interval_method"] == "Hoeffding bounded mean"
    assert first["micro_recall_at_4"]["denominator"] == 2
    comparisons = compare_references([("base", first, a), ("large", second, b)])
    assert comparisons[0]["paired_cases"] == 1
    assert comparisons[0]["excluded_unscored_cases"] == 1
    assert comparisons[0]["gains"] == 1
    assert all(c["p_holm"] >= c["p_two_sided"] for c in comparisons)
