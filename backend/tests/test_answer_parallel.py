import pytest
from researchlens.answer_parallel import merged_results


def test_worker_merge_rejects_duplicate_missing_and_failed_cases():
    def part(cid, error=None):
        return {
            "execution": {},
            "results": [{"case_id": cid, "error": error, "answer_quality": {}}],
        }

    assert [
        row["case_id"] for row in merged_results([part("b"), part("a")], ["a", "b"])["results"]
    ] == ["a", "b"]
    with pytest.raises(ValueError, match="exactly once"):
        merged_results([part("a"), part("a")], ["a", "b"])
    with pytest.raises(ValueError, match="exactly once"):
        merged_results([part("a")], ["a", "b"])
    with pytest.raises(ValueError, match="incomplete"):
        merged_results([part("a", "failed"), part("b")], ["a", "b"])
