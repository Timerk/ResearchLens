"""Check owner-approved migration provenance without executing held-out retrieval."""

import hashlib
import json
from collections import Counter

import pytest
from researchlens.artifacts import canonical_hash, load_artifact
from researchlens.corpus import DIRECTORY
from researchlens.evaluation import load_dataset, validate_dataset_references
from researchlens.evaluation_evidence import EvidenceLabels, validate_labels
from researchlens.formula_adoption import REVIEW, adopt
from researchlens.formula_report import implementation_hashes
from researchlens.ingest import ROOT, build_index


def read(path):
    return json.loads(path.read_bytes())


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_report_source_hashes_match_fresh_lf_checkout(tmp_path, newline):
    committed = b"def answer():\n    return 42\n"
    (tmp_path / "module.py").write_bytes(committed.replace(b"\n", newline))
    # The report must pin the same code in Windows and Linux checkouts.
    assert implementation_hashes(tmp_path, ("module.py",)) == {
        "module.py": hashlib.sha256(committed).hexdigest()
    }


def test_approval_and_archives_pin_current_and_previous_versions(tmp_path):
    approval = read(REVIEW / "approval.json")
    assert approval["review_status"] == "approved"
    assert approval["reviewer_type"] == "human"
    assert approval["review_date"] == "2026-10-14"
    assert approval["reason"] == "source text change from formula rendering"
    assert approval["held_out_retrieval_executed"] is False
    assert approval["held_out_answers_inspected"] is False
    assert approval["paid_api_calls"] == 0
    for root, hashes in (
        (REVIEW, approval["preserved_archive_sha256"]),
        (ROOT, approval["historical_evidence_preserved_sha256"]),
    ):
        for name, expected in hashes.items():
            raw = (root / name).read_bytes()
            if root == ROOT and name in approval["historical_evidence_lf_normalized_paths"]:
                raw = raw.replace(b"\r\n", b"\n")
            assert hashlib.sha256(raw).hexdigest() == expected
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


def test_only_approved_reference_migration_changes_frozen_held_out(tmp_path):
    old = read(REVIEW / "datasets/held-out.json")
    new_path = ROOT / "evaluation/datasets/held-out.json"
    new = read(new_path)
    approval = read(REVIEW / "approval.json")
    assert new["version"] == "4-readable-formulas-frozen"
    assert new["status"] == old["status"] == "frozen"
    for key in set(old) - {"version", "corpus_sha256", "notes", "cases"}:
        assert old[key] == new[key]
    proposals = {
        (r["case_id"], r["reference_index"]): r for r in approval["held_out"]["reference_changes"]
    }
    assert len(proposals) == 11
    assert Counter(r["status"] for r in proposals.values()) == {"ID changed": 4, "text changed": 7}
    for before, after in zip(old["cases"], new["cases"], strict=True):
        # Compare opaque fields without examining answer/claim content.
        assert {k: v for k, v in before.items() if k != "references"} == {
            k: v for k, v in after.items() if k != "references"
        }
        expected = []
        for i, ref in enumerate(before["references"]):
            proposal = proposals.get((before["id"], i))
            expected.extend(proposal["new_references"] if proposal else [ref])
        assert after["references"] == expected
    assert sum(len(c["references"]) for c in old["cases"]) == 62
    assert sum(len(c["references"]) for c in new["cases"]) == 66
    assert hashlib.sha256(new_path.read_bytes()).hexdigest() == approval["held_out"]["file_sha256"]
    build_index(DIRECTORY / "documents.json", tmp_path / "index.json")
    artifact, _ = load_artifact(tmp_path / "index.json", source=DIRECTORY / "documents.json")
    validate_dataset_references(load_dataset(new_path), artifact)


def test_new_development_groups_preserve_approved_evidence_requirements():
    old = read(REVIEW / "labels/technical-development.json")
    new = read(ROOT / "evaluation/labels/technical-development.json")
    for before, after in zip(old["cases"], new["cases"], strict=True):
        assert before["case_id"] == after["case_id"]
        for old_group, new_group in zip(before["groups"], after["groups"], strict=True):
            assert {k: v for k, v in old_group.items() if k != "alternatives"} == {
                k: v for k, v in new_group.items() if k != "alternatives"
            }
            assert len(old_group["alternatives"]) == len(new_group["alternatives"])
    before = read(REVIEW / "datasets/technical-development.json")
    after = read(ROOT / "evaluation/datasets/technical-development.json")
    assert before["cases"] == after["cases"]
    assert before["source_versions"] == after["source_versions"]


def test_adoption_cannot_overwrite_existing_owner_record(tmp_path):
    before = (REVIEW / "approval.json").read_bytes()
    with pytest.raises(ValueError, match="already recorded"):
        adopt(tmp_path)
    assert (REVIEW / "approval.json").read_bytes() == before


def test_active_retrieval_selection_and_tier_summaries_use_adopted_pins():
    approval = read(REVIEW / "approval.json")
    summary_path = ROOT / "docs/formula-adoption-results.json"
    summary = read(summary_path)
    selected = read(ROOT / "docs/development-selected-context-budget.json")
    assert (
        selected["corpus_sha256"] == summary["corpus_sha256"] == approval["adopted_corpus_sha256"]
    )
    assert selected["dataset_sha256"] == approval["pins"]["dataset_sha256"]
    assert selected["shared_passage_sha256"] == approval["pins"]["shared_passage_sha256"]
    assert selected["evidence_labels_sha256"] == approval["approved_labels_canonical_sha256"]
    assert selected["study_summary_sha256"] == hashlib.sha256(summary_path.read_bytes()).hexdigest()
    assert set(summary["manifest"]["indexes"]) == {"full", "standard", "light", "minimal"}
    for index in summary["manifest"]["indexes"].values():
        assert index["source_sha256"] == approval["adopted_corpus_sha256"]
        assert index["passages"] == 207
    assert (
        selected["retrieval"]["artifact_sha256"]
        == summary["manifest"]["indexes"]["full"]["artifact_sha256"]
    )
    for name, expected in summary["implementation_sha256"].items():
        assert (
            hashlib.sha256(
                (ROOT / "backend/researchlens" / name).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            == expected
        )
    assert summary["implementation_hash_method"] == (
        "SHA-256 of source bytes with CRLF normalized to LF"
    )
    assert summary["qwen_meets_all_five_at_12k_and_16k"] is True
    assert summary["api_calls"] == 0
    assert summary["held_out_searches"] == 0
    for budget in ("12000", "16000"):
        assert all(
            summary["models"]["qwen3-4b"]["budgets"][budget]["totals"]["targets_met"].values()
        )
