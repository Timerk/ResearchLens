"""Offline contracts for experimental selection; no model downloads or labels."""

import hashlib
from types import SimpleNamespace

import numpy as np
import pytest
from researchlens.evidence_selection import (
    EvidenceSelector,
    Facet,
    QuestionDecomposer,
    scoring_text,
    select_complementary,
)
from researchlens.models import SearchHit
from researchlens.selection_experiments import RecordingSearch, plan


def hit(i, doc, title, text):
    return SearchHit(
        id=str(i),
        document_id=doc,
        title=title,
        text=text,
        paragraph=i,
        source_url=None,
        license="test",
        kind="synthetic",
        score=1.0,
        source_section="Methods",
    )


PASSAGES = [
    hit(1, "alpha", "Microscope imaging", "A microscope measures fluorescent patches."),
    hit(2, "alpha", "Microscope imaging", "Its calibration takes ten seconds."),
    hit(3, "beta", "Interferometer imaging", "An interferometer measures phase shifts."),
    hit(4, "beta", "Interferometer imaging", "Its calibration takes twenty seconds."),
]


class Base:
    passages = PASSAGES

    def get_encoding_diagnostics(self):
        return None

    def search(self, question, limit):
        return self.passages[:limit]


def test_decomposition_is_bounded_uses_metadata_and_preserves_original():
    decomposer = QuestionDecomposer(PASSAGES)
    question = "Compare the microscope and interferometer calibration procedures."
    parts = decomposer.split(question)
    assert parts[0].query == question
    assert [p.document_id for p in parts[1:]] == ["alpha", "beta"]
    assert len(parts) == 3
    assert decomposer.split("How is microscope calibration performed?") == [
        Facet("How is microscope calibration performed?")
    ]
    clauses = decomposer.split(
        "In the microscope study, what is measured, and how long does calibration take?"
    )
    assert len(clauses) == 3
    assert "how long" in clauses[-1].query
    assert all(
        len(p.query) <= 2000
        for p in decomposer.split("x" * 1970 + " microscope and interferometer")
    )


def test_diminishing_coverage_selects_complementary_support_not_repeated_topical_hits():
    utilities = np.array([[1, 0.9, 0.8, 0.7], [1, 0.95, 0.9, 0], [0, 0, 0, 1]])
    chosen = select_complementary(utilities, 2)
    assert chosen == [0, 3]
    with pytest.raises(ValueError):
        select_complementary(np.array([[np.nan]]), 1)


def test_selection_returns_full_original_passages_and_retains_original_candidates():
    selector = EvidenceSelector(Base(), candidates=4, per_query=2)
    question = "Compare microscope and interferometer imaging."
    selected = selector.search(question, limit=2)
    assert {h.document_id for h in selected} == {"alpha", "beta"}
    assert selector.last_selection["candidate_ids"][:2] == ["1", "2"]
    for h in selected:
        original = next(p for p in PASSAGES if p.id == h.id)
        assert h.model_dump(exclude={"score"}) == original.model_dump(exclude={"score"})


def test_metadata_scoring_measures_enriched_input_but_maps_to_canonical_passages():
    class Scorer:
        metadata = {}
        last_diagnostics = []

        def score(self, question, passages):
            assert all(p.text.startswith("Title:") for p in passages)
            self.last_diagnostics = [
                {
                    "passage_id": p.id,
                    "input_tokens": 100,
                    "encoded_tokens": 100,
                    "truncated": False,
                    "text_sha256": hashlib.sha256(p.text.encode()).hexdigest(),
                    "retained_ranges": [{"start": 0, "end": len(p.text)}],
                }
                for p in passages
            ]
            return np.arange(len(passages), 0, -1)

    selector = EvidenceSelector(
        Base(),
        Scorer(),
        decompose=False,
        complementary=False,
        candidates=4,
        per_query=4,
        representation="title-section-text-v1",
    )
    question = "What does the microscope measure?"
    selected = selector.search(question)
    assert [p.id for p in selected] == ["1", "2", "3", "4"]
    for p, row in zip(selected, selector.get_reranking_diagnostics(question), strict=True):
        assert row["text_sha256"] == hashlib.sha256(p.text.encode()).hexdigest()
        assert row["input_tokens"] == 100
        assert row["retained_ranges"] == [{"start": 0, "end": len(p.text)}]
    assert selector.get_reranking_diagnostics("another question") == []
    assert scoring_text(PASSAGES[0], "passage-text-only") == PASSAGES[0].text


def test_invalid_scores_or_truncation_fail_instead_of_claiming_full_visibility():
    scorer = SimpleNamespace(metadata={}, last_diagnostics=[], score=lambda *_: [float("nan")] * 4)
    selector = EvidenceSelector(Base(), scorer, per_query=4)
    with pytest.raises(ValueError, match="invalid facet scores"):
        selector.search("question", 4)


@pytest.mark.parametrize("broken", ["truncated", "text_sha256", "encoded_tokens"])
def test_incomplete_or_stale_pair_measurements_are_rejected(broken):
    class Scorer:
        metadata = {}

        def score(self, question, passages):
            self.last_diagnostics = [
                {
                    "passage_id": p.id,
                    "input_tokens": 10,
                    "encoded_tokens": 10,
                    "truncated": False,
                    "text_sha256": hashlib.sha256(p.text.encode()).hexdigest(),
                }
                for p in passages
            ]
            self.last_diagnostics[0][broken] = {
                "truncated": True,
                "text_sha256": "0" * 64,
                "encoded_tokens": 9,
            }[broken]
            return np.ones(len(passages))

    selector = EvidenceSelector(Base(), Scorer(), per_query=4)
    with pytest.raises(ValueError, match="complete, ordered passage measurements"):
        selector.search("question", 4)


def test_observer_records_each_search_without_caching_and_plan_is_bounded():
    adapter = EvidenceSelector(Base(), per_query=4)
    observer = RecordingSearch(adapter)
    assert observer.passages is adapter.passages
    observer.search("question", 4)
    first = observer.records[hashlib.sha256(b"question").hexdigest()]
    observer.search("question", 4)
    assert observer.records[hashlib.sha256(b"question").hexdigest()] is not first
    entries = plan()
    assert len(entries) == len({e["name"] for e in entries}) == 8
    assert sum(not e["selector"] for e in entries) == 3
