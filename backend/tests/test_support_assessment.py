"""Support output and set-selection contracts, not a quality evaluation."""

import numpy as np
import pytest
from researchlens.support_assessment import (
    assessment_schema,
    exact_support_set,
    source_quotes,
    validate_assessment,
)


def test_quote_grammar_is_grounded_and_requirement_keys_cannot_repeat():
    source = "First fact. " + "Long source phrase " * 40 + "Final fact."
    schema = assessment_schema(2, source)
    fields = schema["properties"]["requirements"]
    assert fields["required"] == ["r0", "r1"]
    quotes = source_quotes(source)
    assert all(q in source and len(q) <= 300 for q in quotes)
    assert "First fact." in quotes
    assert fields["properties"]["r0"]["anyOf"][0]["properties"]["quotes"]["items"]["enum"] == quotes


def test_checked_quote_spans_and_absent_support_remain_distinct():
    raw = {
        "requirements": {
            "r0": {"status": "full", "quotes": ["Source fact."], "missing": ""},
            "r1": {"status": "absent", "quotes": [], "missing": "The comparison study is missing."},
        }
    }
    result = validate_assessment(raw, "Source fact. Other source text.", 2)
    assert result[0]["spans"] == [{"start": 0, "end": 12}]
    assert result[1]["status"] == "absent"
    raw["requirements"]["r0"]["quotes"] = ["Invented fact."]
    with pytest.raises(ValueError, match="ungrounded"):
        validate_assessment(raw, "Source fact.", 2)


@pytest.mark.parametrize(
    "fields",
    [
        {"status": "full", "quotes": [], "missing": ""},
        {"status": "partial", "quotes": ["fact"], "missing": ""},
        {"status": "absent", "quotes": ["fact"], "missing": "Missing study"},
        {"status": "full", "quotes": ["fact"], "missing": "Unestablished condition"},
        {"id": 0, "status": "full", "quotes": ["fact"], "missing": ""},
    ],
)
def test_inconsistent_support_is_not_silently_repaired(fields):
    with pytest.raises(ValueError):
        validate_assessment({"requirements": {"r0": fields}}, "fact", 1)


def test_full_coverage_precedes_relevance_and_partial_matches():
    # Relevance strongly favors redundant first-fact matches. Full second-fact
    # support still wins, while two partial passages cannot prove joint support.
    statuses = [[1, 1, 0, 0], [0, 0.5, 1, 0.5]]
    assert exact_support_set(statuses, [100, 90, 1, 80], 2) == [0, 2]
    assert exact_support_set(np.ones((2, 5)), np.ones(5)) == [0, 1, 2, 3]
    with pytest.raises(ValueError):
        exact_support_set([[0.7]], [1], 1)
