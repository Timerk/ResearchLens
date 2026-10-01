"""Regressions for source scope and factual qualifications in development labels."""

import hashlib
import json

import pytest
from pydantic import TypeAdapter
from researchlens.evaluation import load_dataset
from researchlens.evaluation_evidence import (
    EvidenceLabels,
    TextRange,
    evidence_coverage,
    validate_labels,
)
from researchlens.ingest import ROOT, TECHNICAL_CORPUS, chunk_documents
from researchlens.models import Document


@pytest.fixture(scope="module")
def evidence():
    dataset = load_dataset(ROOT / "evaluation/datasets/technical-development.json")
    passages = chunk_documents(
        TypeAdapter(list[Document]).validate_json(TECHNICAL_CORPUS.read_bytes())
    )
    labels = EvidenceLabels.model_validate_json(
        (ROOT / "evaluation/labels/technical-development.json").read_bytes()
    )
    artifact = {
        "source_sha256": dataset.corpus_sha256,
        "chunking": {"method": "paragraph-word-windows", "max_words": 180},
    }
    entries = validate_labels(labels, dataset, artifact, passages)
    return labels, entries, {p.id: p for p in passages}


def coverage(evidence, case_id, *ids):
    _, entries, passages = evidence
    visible = {pid: [TextRange(start=0, end=len(passages[pid].text))] for pid in ids}
    return evidence_coverage(entries[case_id], visible)


def group(evidence, case_id, group_id):
    return next(g for g in evidence[1][case_id].groups if g.id == group_id)


def test_ai_fix_record_preserves_review_pins_and_separate_approval(evidence):
    directory = ROOT / "evaluation/reviews/2026-10-01-pr8"
    record = json.loads((directory / "evidence-fixes.json").read_bytes())
    review = json.loads((directory / "evidence-review.json").read_bytes())
    labels = evidence[0]
    assert record["input_labels_sha256"] == review["labels_file_sha256"]
    assert (
        record["output_labels_sha256"]
        == hashlib.sha256(
            (ROOT / "evaluation/labels/technical-development.json").read_bytes()
        ).hexdigest()
    )
    for name, checksum in record["review_files_sha256"].items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == checksum
    assert record["pins"] == {name: getattr(labels, name) for name in record["pins"]}
    assert labels.review_status == "unreviewed"
    assert labels.reviewer is labels.review_date is None
    assert record["substantive_findings_addressed"] == [f"F{i:02d}" for i in range(1, 15)]
    assert [d["proposal_number"] for d in record["recommendation_decisions"]] == list(range(1, 42))
    assert record["after"] == dict(cases=36, groups=92, alternatives=140, span_occurrences=165)
    dataset = load_dataset(ROOT / "evaluation/datasets/technical-development.json")
    assert all(not c.expected_abstention for c in dataset.cases if c.id in evidence[1])
    assert set(evidence[1]) == {c.id for c in dataset.cases if not c.expected_abstention}


def test_stage_two_sample_types_do_not_require_optional_clean_targets(evidence):
    entry = group(evidence, "tech-autoencoder-exact", "part-2")
    # Old p44 artificial-only evidence supplies stage-one and weight-transfer facts,
    # but cannot supply the stage-two normal/artificial sample requirement.
    old = coverage(evidence, "tech-autoencoder-exact", "pmc11121878:p44:w0")
    assert old["complete_evidence"] is False
    assert (
        coverage(evidence, "tech-autoencoder-exact", "pmc11121878:p8:w0")["complete_evidence"]
        is True
    )
    for option in entry.alternatives:
        text = " ".join(s.quote for s in option)
        assert "normal" in text and "artificially defective" in text
        assert "references" not in text and "counterparts" not in text
    assert entry.alternatives[-1][0].passage_id == "pmc11121878:p1:w0"
    assert entry.alternatives[-1][1].passage_id == "pmc11121878:p1:w180"


def test_rgb_channels_keep_ordered_antecedent_without_requiring_it_for_blue(evidence):
    red_green = group(evidence, "tech-rgb-channel-assignment", "part-1").alternatives[0][0]
    assert (red_green.start, red_green.end) == (168, 479)
    assert "forward lighting image and the backward lighting image" in red_green.quote
    assert "red channel and green channel" in red_green.quote
    blue = group(evidence, "tech-rgb-channel-assignment", "part-2").alternatives[0][0]
    assert "blue channel" in blue.quote and "averaging" in blue.quote
    assert "red channel" not in blue.quote


def test_architecture_coverage_requires_both_conflicting_statements(evidence):
    assert (
        coverage(evidence, "tech-amff-layers", "pmc11510794:p41:w0")["complete_evidence"] is False
    )
    assert (
        coverage(evidence, "tech-amff-layers", "pmc11510794:p41:w0", "pmc11510794:p46:w0")[
            "complete_evidence"
        ]
        is True
    )
    assert (
        coverage(evidence, "tech-amff-layers", "pmc11510794:p46:w0")["complete_evidence"] is False
    )  # P3/P5 prose is not P3/P4 evidence.


def test_efficiency_coverage_requires_operational_bounds(evidence):
    assert coverage(evidence, "tech-wafer-exact", "pmc10934137:p1:w0")["complete_evidence"] is False
    assert (
        coverage(
            evidence,
            "tech-wafer-exact",
            "pmc10934137:p1:w0",
            "pmc10934137:p14:w180",
            "pmc10934137:p16:w0",
        )["complete_evidence"]
        is True
    )
    qualification = group(evidence, "tech-wafer-exact", "efficiency-scope")
    text = " ".join(s.quote for s in qualification.alternatives[0])
    assert "Without considering the data transmission time" in text
    assert "line frequency is fixed" in text


def test_dynamic_gaussian_coverage_requires_identity_and_fixed_footprint(evidence):
    case = "tech-changing-neighborhood"
    assert coverage(evidence, case, "pmc11121878:p31:w0")["complete_evidence"] is False
    assert (
        coverage(evidence, case, "pmc11121878:p31:w0", "pmc11121878:p30:w0")["complete_evidence"]
        is False
    )
    assert (
        coverage(evidence, case, "pmc11121878:p31:w0", "pmc11121878:p30:w0", "pmc11121878:p29:w0")[
            "complete_evidence"
        ]
        is True
    )
    for gid in ("part-1", "part-2", "part-3"):
        for option in group(evidence, case, gid).alternatives:
            assert any("standard deviation" in s.quote and "Gaussian" in s.quote for s in option)


@pytest.mark.parametrize("case", ["tech-imagenet-initialization", "tech-compare-network-inputs"])
def test_transferred_input_sizes_require_architecture_scope(evidence, case):
    entry = group(evidence, case, "part-2")
    for option in entry.alternatives:
        assert all(s.passage_id != "pmc11768589:p25:w0" for s in option)
        assert any("ResNet-50 and Inception V3" in s.quote for s in option)
    visible = {
        pid: [TextRange(start=0, end=len(evidence[2][pid].text))]
        for pid in ("pmc11768589:p25:w0", "pmc11768589:p29:w0")
    }
    assert not next(
        g
        for g in evidence_coverage(evidence[1][case], visible)["groups"]
        if g["group_id"] == "part-2"
    )["covered"]


def test_aw_ssim_preserves_constant_weights_and_unchanged_components(evidence):
    case = "tech-aw-ssim-combination"
    assert (
        coverage(evidence, case, "pmc11121878:p8:w0", "pmc11121878:p46:w0", "pmc11121878:p27:w0")[
            "complete_evidence"
        ]
        is False
    )
    assert (
        coverage(evidence, case, "pmc11121878:p25:w0", "pmc11121878:p26:w0")["complete_evidence"]
        is True
    )
    for option in group(evidence, case, "part-2").alternatives:
        assert any(s.passage_id == "pmc11121878:p26:w0" and "constant" in s.quote for s in option)
    assert "dataset-scope" not in {
        g.id for g in evidence[1]["tech-compare-evaluation-metrics"].groups
    }


@pytest.mark.parametrize(
    "case,gid",
    [
        ("tech-adga-shapes", "part-3"),
        ("tech-adga-shapes", "part-4"),
        ("tech-too-many-shortcuts", "part-1"),
    ],
)
def test_original_complementary_and_options_still_require_each_span(evidence, case, gid):
    entry = evidence[1][case]
    option = group(evidence, case, gid).alternatives[0]
    assert len(option) == 2
    for kept in option:
        visible = {kept.passage_id: [TextRange(start=kept.start, end=kept.end)]}
        assert not next(
            g for g in evidence_coverage(entry, visible)["groups"] if g["group_id"] == gid
        )["covered"]
