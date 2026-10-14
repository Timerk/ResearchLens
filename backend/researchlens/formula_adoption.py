"""Apply the owner's 2026-10-14 formula migration approval, without held-out searches."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

from pydantic import TypeAdapter

from researchlens.artifacts import canonical_hash, load_artifact, passage_identity
from researchlens.corpus import DIRECTORY, SOURCES, build_corpus, extract
from researchlens.evaluation import encoded, load_dataset, validate_dataset_references
from researchlens.evaluation_evidence import EvidenceLabels, dataset_digest, validate_labels
from researchlens.formula_prototype import digest
from researchlens.ingest import ROOT, build_index
from researchlens.models import Document

REVIEW = ROOT / "evaluation/reviews/2026-10-14-pr15"
REVIEWER = "Project owner (human reviewer; approval in PR #15 thread)"
DATE = "2026-10-14"
REASON = "source text change from formula rendering"
HISTORICAL_LF_PATHS = (
    "evaluation/reviews/2026-10-01-pr8/README.md",
    "evaluation/answer-quality-evidence-manifest.json",
    "docs/answer-quality-results.json",
)


def migrate_references(dataset: dict, records: list[dict]) -> tuple[dict, list[dict]]:
    """Read only reference fields. Preserve the rest of every case as opaque content."""
    migrated = copy.deepcopy(dataset)
    proposals = {(r["case_id"], r["reference_index"]): r for r in records}
    changes = []
    for case in migrated["cases"]:
        references = []
        for i, ref in enumerate(case["references"]):
            proposal = proposals[(case["id"], i)]
            if proposal["old_passage_id"] != ref["passage_id"]:
                raise ValueError("Reference migration baseline differs")
            if proposal["status"] == "unmappable" or not proposal["same_source_location"]:
                raise ValueError("Approved reference proposal cannot map")
            replacements = [{**ref, "passage_id": pid} for pid in proposal["proposed_passage_ids"]]
            references.extend(replacements)
            if proposal["status"] != "unchanged":
                changes.append(
                    {
                        "case_id": case["id"],
                        "reference_index": i,
                        "status": proposal["status"],
                        "old_reference": ref,
                        "new_references": replacements,
                    }
                )
        case["references"] = references
    return migrated, changes


def adopt(candidate: Path) -> dict:
    if REVIEW.exists():
        raise ValueError("Adoption already recorded; do not overwrite the approval archive")
    summary = json.loads((candidate / "summary.json").read_bytes())
    recorded = json.loads(
        (ROOT / "data/technical/prototypes/mathml-readable-v2/summary.json").read_bytes()
    )
    if digest(candidate / "documents.json") != recorded["prototype_documents_sha256"]:
        raise ValueError("Candidate differs from owner-reviewed corpus")
    migration = json.loads((candidate / "remapping.json").read_bytes())
    if (
        digest(candidate / "remapping.json")
        != recorded["candidate_artifacts"]["exact_remapping_sha256"]
    ):
        raise ValueError("Migration differs from owner-reviewed proposal")
    for name, expected in summary["protected_inputs_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"Protected adoption input changed: {name}")
    candidate_artifact, candidate_passages = load_artifact(
        candidate / "index.json", source=candidate / "documents.json"
    )
    proposed_labels = EvidenceLabels.model_validate_json(
        (candidate / "development-labels.json").read_bytes()
    )
    validate_labels(
        proposed_labels,
        load_dataset(candidate / "development-dataset.json"),
        candidate_artifact,
        candidate_passages,
    )
    dataset_path = ROOT / "evaluation/datasets/technical-development.json"
    held_out_path = ROOT / "evaluation/datasets/held-out.json"
    label_path = ROOT / "evaluation/labels/technical-development.json"
    previous_corpus_sha = digest(DIRECTORY / "documents.json")
    previous_labels = json.loads(label_path.read_bytes())
    development = json.loads(dataset_path.read_bytes())
    held_out, reference_changes = migrate_references(
        json.loads(held_out_path.read_bytes()), migration["held_out_inventory"]["references"]
    )
    if len(reference_changes) != 11:
        raise ValueError("Expected exactly the 11 owner-approved reference changes")
    # Verify the extraction before publishing canonical files or the approval archive.
    rendered = [
        extract((DIRECTORY / "originals" / f"{pmcid}.xml").read_bytes(), pmcid)[0]
        for pmcid in SOURCES
    ]
    proposal = TypeAdapter(list[Document]).validate_json(
        (candidate / "documents.json").read_bytes()
    )
    for before, after in zip(proposal, rendered, strict=True):
        a, b = before.model_dump(), after.model_dump()
        a["attribution"].pop("changes")
        b["attribution"].pop("changes")
        if a != b:
            raise ValueError("Canonical extraction differs from approved formula text/provenance")
    # Retain immutable prior datasets and labels so earlier approval hashes still verify.
    REVIEW.mkdir(parents=True)
    preserved = {}
    for source, target in (
        (dataset_path, "datasets/technical-development.json"),
        (held_out_path, "datasets/held-out.json"),
        (label_path, "labels/technical-development.json"),
        (ROOT / "docs/formula-remapping-review.md", "phase1-remapping-review.md"),
        (ROOT / "docs/formula-rendering-results.json", "phase1-results.json"),
        (ROOT / "docs/development-selected-retrieval.json", "previous-selected-retrieval.json"),
        (ROOT / "docs/development-selected-context-budget.json", "previous-selected-context.json"),
    ):
        destination = REVIEW / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        preserved[target] = digest(destination)
    historical = {
        p.relative_to(ROOT).as_posix(): digest(p)
        for p in (ROOT / "evaluation/reviews/2026-10-01-pr8").iterdir()
        if p.is_file()
    }
    for path in (
        "evaluation/answer-quality-evidence-manifest.json",
        "docs/answer-quality-results.json",
    ):
        historical[path] = digest(ROOT / path)
    for path in HISTORICAL_LF_PATHS:
        # These tracked text files have LF Git blobs but may be CRLF in a Windows checkout.
        raw = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        historical[path] = hashlib.sha256(raw).hexdigest()

    build_corpus()
    corpus_sha = digest(DIRECTORY / "documents.json")
    for dataset, path, version in (
        (development, dataset_path, "5-readable-formulas-approved"),
        (held_out, held_out_path, "4-readable-formulas-frozen"),
    ):
        dataset.update(corpus_sha256=corpus_sha, version=version)
        dataset["notes"] += (
            f" Formula extraction and location migration approved by the project owner on {DATE}; "
            f"reason: {REASON}. Original source versions and all question/answer/claim content "
            "are preserved. Held-out reference migration is offline, derived from the corpus "
            "change, not model results. No held-out retrieval was executed. "
            "Previous frozen/approved version is archived in evaluation/reviews/2026-10-14-pr15."
        )
        path.write_bytes(encoded(dataset))
    build_index(DIRECTORY / "documents.json", ROOT / "data/index.json")
    artifact, passages = load_artifact(
        ROOT / "data/index.json", source=DIRECTORY / "documents.json"
    )
    for path in (dataset_path, held_out_path):
        # Offline metadata validation only. Never pass held-out to a retriever.
        validate_dataset_references(load_dataset(path), artifact)
    labels = proposed_labels.model_dump(mode="json")
    labels.update(
        dataset_sha256=dataset_digest(load_dataset(dataset_path)),
        corpus_sha256=corpus_sha,
        shared_passage_sha256=passage_identity(artifact, passages),
        review_status="approved",
        reviewer=REVIEWER,
        review_date=DATE,
        notes=(
            "Owner-approved development evidence migrated on 2026-10-14. Reason: source text "
            "change from formula rendering. All reviewed groups and alternatives retained; "
            "33 span occurrences remapped, two spans split into AND fragments. Approval in "
            "PR #15 conversation; see evaluation/reviews/2026-10-14-pr15/approval.json. "
            "No held-out span labels or generated-answer approval are implied."
        ),
    )
    validate_labels(
        EvidenceLabels.model_validate(labels), load_dataset(dataset_path), artifact, passages
    )
    label_path.write_bytes(encoded(labels))
    approval = {
        "schema_version": 1,
        "review_status": "approved",
        "reviewer_type": "human",
        "reviewer": REVIEWER,
        "review_date": DATE,
        "reason": REASON,
        "approval_source": "Explicit project-owner approval in the PR #15 conversation",
        "approval_statement": (
            "The owner has reviewed docs/formula-remapping-review.md and approves all "
            "development span remappings and held-out reference changes as proposed."
        ),
        "status": "approved_and_adopted",
        "scope": (
            "Formula source text, development spans, held-out references and corpus pins only."
        ),
        "phase1_commit": "e6237c2",
        "rebased_phase1_commit": "b398004",
        "main_base_commit": "051381c",
        "previous_corpus_sha256": previous_corpus_sha,
        "approved_candidate_corpus_sha256": recorded["prototype_documents_sha256"],
        "adopted_corpus_sha256": corpus_sha,
        "corpus_byte_change_from_candidate": (
            "Approved attribution replaces proposal-only status; all document text is identical."
        ),
        "previous_labels_sha256": preserved["labels/technical-development.json"],
        "proposed_labels_sha256": digest(candidate / "development-labels.json"),
        "approved_labels_sha256": digest(label_path),
        "approved_labels_canonical_sha256": canonical_hash(labels),
        "previous_pins": {
            k: previous_labels[k]
            for k in ("dataset_sha256", "corpus_sha256", "shared_passage_sha256")
        },
        "pins": {
            k: labels[k] for k in ("dataset_sha256", "corpus_sha256", "shared_passage_sha256")
        },
        "development_remapping_counts": recorded["label_remapping"]["counts"],
        "counts": {
            "cases": len(labels["cases"]),
            "groups": sum(len(c["groups"]) for c in labels["cases"]),
            "alternatives": sum(
                len(g["alternatives"]) for c in labels["cases"] for g in c["groups"]
            ),
            "span_occurrences": sum(
                len(a) for c in labels["cases"] for g in c["groups"] for a in g["alternatives"]
            ),
        },
        "approved_cases": [
            dict(case_id=c["case_id"], group_ids=[g["id"] for g in c["groups"]])
            for c in labels["cases"]
        ],
        "held_out": {
            "previous_version": "3-human-reviewed-frozen",
            "version": held_out["version"],
            "previous_file_sha256": preserved["datasets/held-out.json"],
            "file_sha256": digest(held_out_path),
            "reference_changes": reference_changes,
            "reference_change_counts": recorded["label_remapping"]["held_out_inventory"]["counts"],
            "question_answer_claim_content_unchanged": True,
            "source_versions_unchanged": True,
            "origin": "Offline corpus alignment, not held-out model results",
        },
        "preserved_archive_sha256": preserved,
        "historical_evidence_preserved_sha256": historical,
        "historical_evidence_lf_normalized_paths": list(HISTORICAL_LF_PATHS),
        "historical_evidence_hash_method": (
            "LF-normalized bytes for declared text paths; exact bytes for all other paths."
        ),
        "held_out_retrieval_executed": False,
        "held_out_answers_inspected": False,
        "paid_api_calls": 0,
    }
    (REVIEW / "approval.json").write_bytes(encoded(approval))
    return approval


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    args = parser.parse_args()
    result = adopt(args.candidate.resolve())
    print(f"Adopted corpus {result['adopted_corpus_sha256']}; {result['counts']}")
