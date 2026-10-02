"""Offline selection and grounding contracts; no downloads or scientific-quality claims."""

import numpy as np
import pytest
from researchlens.information_selection import select_indices
from researchlens.local_needs import question_schema, validate_needs


def test_decoding_schema_contains_only_exact_question_phrases():
    question = "Which forward and backward light sources are used in the microscope?"
    schema = question_schema(question)
    fields = schema["properties"]["needs"]["items"]["properties"]
    assert "microscope" in fields["subject"]["enum"]
    assert "forward and backward light sources" in fields["aspect"]["enum"]
    assert "forward light sources" not in fields["aspect"]["enum"]
    assert all(value in question for value in fields["aspect"]["enum"])
    assert question_schema(question) == schema


def test_needs_use_exact_question_phrases_and_deduplicate():
    question = "Compare microscope and interferometer inputs and calibration procedures."
    raw = {
        "needs": [
            {"subject": "microscope", "aspect": "inputs"},
            {"subject": "interferometer", "aspect": "calibration procedures"},
            {"subject": "microscope", "aspect": "inputs"},
        ]
    }
    assert validate_needs(question, raw) == [
        "microscope inputs",
        "interferometer calibration procedures",
    ]


@pytest.mark.parametrize(
    "raw",
    [
        {"needs": []},
        {"needs": [{"subject": "microscope", "aspect": "quantum efficiency"}]},
        {"needs": [{"subject": " microscope", "aspect": "inputs"}]},
        {"needs": [{"subject": "microscope", "aspect": ""}]},
        {"needs": [{"subject": "microscope", "aspect": "inputs", "answer": "42"}]},
        {"needs": [{"subject": 42, "aspect": "inputs"}]},
    ],
)
def test_invalid_or_invented_information_needs_are_rejected(raw):
    with pytest.raises(ValueError):
        validate_needs("Compare microscope inputs.", raw)


def test_round_robin_covers_distinct_needs_and_preserves_deterministic_ties():
    scores = [[3, 2, 1, 0], [4, 3, 0, 0], [0, 0, 4, 3]]
    assert select_indices(scores, 2, "needs-round-robin") == [0, 2]
    assert select_indices(scores, 2, "whole-rerank") == [0, 1]


def test_saturation_can_select_multiple_passages_per_need_without_duplicates():
    scores = [[0, 0, 0, 0], [4, 3, -4, -4], [-4, -4, 4, 3]]
    chosen = select_indices(scores, 4, "needs-saturation", np.eye(4))
    assert chosen[:2] == [0, 2]
    assert len(set(chosen)) == 4
    with pytest.raises(ValueError):
        select_indices([[np.nan]], 1, "needs-max")
    with pytest.raises(ValueError):
        select_indices([[1]], 1, "needs-saturation")
