"""The owner-approved formula adoption record still pins the active corpus, labels and splits."""

import hashlib
import json
from collections import Counter

from researchlens.artifacts import canonical_hash, load_artifact
from researchlens.corpus import DIRECTORY
from researchlens.evaluation import load_dataset, validate_dataset_references
from researchlens.evaluation_evidence import EvidenceLabels, validate_labels
from researchlens.ingest import ROOT, build_index

APPROVAL = ROOT / "evaluation/reviews/2026-10-14-pr15/approval.json"
# Pinned historical files moved to the archive/evaluation-2026-10 tag; the rest stay on main.
ARCHIVED = {
    "evaluation/reviews/2026-10-01-pr8/README.md",
    "evaluation/reviews/2026-10-01-pr8/evidence-fixes.json",
    "evaluation/reviews/2026-10-01-pr8/evidence-fixes.md",
    "evaluation/reviews/2026-10-01-pr8/evidence-review.json",
    "evaluation/reviews/2026-10-01-pr8/evidence-review.md",
    "evaluation/reviews/2026-10-01-pr8/rejected-cases.json",
    "evaluation/reviews/2026-10-01-pr8/review.json",
    "docs/answer-quality-results.json",
}


def read(path):
    return json.loads(path.read_bytes())


def test_manifest_cites_the_owner_approval_of_the_adopted_corpus():
    manifest = read(DIRECTORY / "manifest.json")
    approval = read(APPROVAL)
    assert ROOT / manifest["formula_approval_record"] == APPROVAL
    assert manifest["documents_sha256"] == approval["adopted_corpus_sha256"]
    assert approval["review_status"] == "approved"
    assert approval["reviewer_type"] == "human"
    assert approval["review_date"] == "2026-10-14"
    assert approval["reason"] == "source text change from formula rendering"
    assert approval["held_out_retrieval_executed"] is False
    assert approval["held_out_answers_inspected"] is False
    assert approval["paid_api_calls"] == 0


def test_kept_historical_evidence_matches_its_approval_hashes():
    approval = read(APPROVAL)
    kept = {
        name: expected
        for name, expected in approval["historical_evidence_preserved_sha256"].items()
        if name not in ARCHIVED
    }
    assert set(kept) == {
        "evaluation/reviews/2026-10-01-pr8/evidence-human-review.json",
        "evaluation/reviews/2026-10-01-pr8/human-review.json",
        "evaluation/answer-quality-evidence-manifest.json",
    }
    for name, expected in kept.items():
        raw = (ROOT / name).read_bytes()
        if name in approval["historical_evidence_lf_normalized_paths"]:
            raw = raw.replace(b"\r\n", b"\n")
        assert hashlib.sha256(raw).hexdigest() == expected


def test_active_labels_are_the_approved_labels_and_validate_on_the_corpus(tmp_path):
    approval = read(APPROVAL)
    labels_path = ROOT / "evaluation/labels/technical-development.json"
    labels = EvidenceLabels.model_validate_json(labels_path.read_bytes())
    assert (
        hashlib.sha256(labels_path.read_bytes()).hexdigest() == approval["approved_labels_sha256"]
    )
    assert (
        canonical_hash(labels.model_dump(mode="json"))
        == approval["approved_labels_canonical_sha256"]
    )
    assert labels.review_date.isoformat() == "2026-10-14"
    assert labels.review_status == "approved"
    assert approval["counts"] == dict(cases=36, groups=92, alternatives=140, span_occurrences=167)
    build_index(DIRECTORY / "documents.json", tmp_path / "index.json")
    artifact, passages = load_artifact(tmp_path / "index.json", source=DIRECTORY / "documents.json")
    validate_labels(
        labels,
        load_dataset(ROOT / "evaluation/datasets/technical-development.json"),
        artifact,
        passages,
    )
    assert artifact["source_sha256"] == approval["adopted_corpus_sha256"]


def test_active_held_out_is_the_approved_frozen_file(tmp_path):
    approval = read(APPROVAL)["held_out"]
    path = ROOT / "evaluation/datasets/held-out.json"
    held_out = read(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == approval["file_sha256"]
    assert held_out["version"] == approval["version"] == "4-readable-formulas-frozen"
    assert held_out["status"] == "frozen"
    changes = approval["reference_changes"]
    assert len(changes) == 11
    assert Counter(r["status"] for r in changes) == {"ID changed": 4, "text changed": 7}
    assert sum(len(c["references"]) for c in held_out["cases"]) == 66
    build_index(DIRECTORY / "documents.json", tmp_path / "index.json")
    artifact, _ = load_artifact(tmp_path / "index.json", source=DIRECTORY / "documents.json")
    validate_dataset_references(load_dataset(path), artifact)
