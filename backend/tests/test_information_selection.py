"""Offline selection and grounding contracts; no downloads or scientific-quality claims."""

import hashlib

import numpy as np
import pytest
from researchlens.information_selection import FixedPoolSelector, select_indices
from researchlens.local_needs import question_schema, validate_needs
from researchlens.models import Passage


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


def test_fixed_adapter_preserves_identity_and_does_not_hide_decomposition_failures():
    passages = [
        Passage(
            id=str(i),
            document_id="study",
            title="Study",
            paragraph=i + 1,
            text=f"Canonical passage {i}.",
            kind="synthetic",
            license="test",
            source_url=None,
        )
        for i in range(40)
    ]
    row = {
        "question_sha256": hashlib.sha256(b"known question").hexdigest(),
        "candidate_ids": [p.id for p in passages],
        "dense_scores": list(range(40)),
        "original_scores": list(range(40)),
        "rule_scores": [],
        "need_scores": [],
        "original_pair_diagnostics": [],
        "error": "invalid_or_failed_local_decomposition",
    }
    bundle = {"cases": [row], "manifest": {"reranker": {}}, "encoding_diagnostics": None}
    vectors = np.tile([1.0, 0.0], (40, 1))
    control = FixedPoolSelector(bundle, passages, vectors, "dense-order", "0" * 64)
    hits = control.search("known question", 4)
    assert [h.id for h in hits] == ["39", "38", "37", "36"]
    assert hits[0].model_dump(exclude={"score"}) == passages[39].model_dump()
    with pytest.raises(ValueError, match="absent from the frozen"):
        control.search("unseen question")
    failed = FixedPoolSelector(bundle, passages, vectors, "needs-max", "0" * 64)
    with pytest.raises(ValueError, match="no silent decomposition fallback"):
        failed.search("known question")
