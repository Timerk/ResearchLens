"""Offline-first evaluation: python -m researchlens.evaluation --help."""

import hashlib
import json
import subprocess
from pathlib import Path

from researchlens.artifacts import (
    canonical_hash,
    validate_passage_artifact,
)
from researchlens.ingest import ROOT
from researchlens.models import Passage

from researchlens_eval.evaluation_schema import (
    Dataset,
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encoded(value: dict) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def load_dataset(path: Path) -> Dataset:
    return Dataset.model_validate_json(path.read_bytes())


def validate_splits(development: Dataset, held_out: Dataset) -> None:
    if development.split != "development" or held_out.split != "held-out":
        raise ValueError("Expected separate development and held-out datasets")
    ids = {c.id for c in development.cases}
    questions = {" ".join(c.question.casefold().split()) for c in development.cases}
    if any(
        c.id in ids or " ".join(c.question.casefold().split()) in questions for c in held_out.cases
    ):
        raise ValueError("Development and held-out cases overlap")


def validate_artifact(dataset: Dataset, artifact: dict) -> list[Passage]:
    if not dataset.cases:
        raise ValueError("No cases: question creation and source review are pending")
    if dataset.split == "held-out" and dataset.status != "frozen":
        raise ValueError("Held-out runs require a frozen, approved dataset")
    return validate_dataset_references(dataset, artifact)


def validate_dataset_references(dataset: Dataset, artifact: dict) -> list[Passage]:
    """Check pinned sources/locations without executing retrieval or approving drafts.

    This permits offline authoring checks for held-out candidates. Execution must
    still go through validate_artifact, which enforces the held-out freeze guard.
    Valid locations do not establish that the referenced text supports a claim.
    """
    if dataset.corpus_sha256 != artifact.get("source_sha256"):
        raise ValueError("Dataset corpus hash differs from the passage artifact; review references")
    passages = validate_passage_artifact(artifact)
    by_id = {p.id: p for p in passages}
    if not passages or len(by_id) != len(passages):
        raise ValueError("Passage artifact must contain unique passages")
    if dataset.material == "real-corpus" and any(p.kind != "technical" for p in passages):
        raise ValueError("Real-corpus evaluation cannot use synthetic passages")
    if dataset.source_versions:
        sources = {s.source_id: s for s in dataset.source_versions}
        if set(sources) != {p.document_id for p in passages}:
            raise ValueError("Dataset source versions do not cover the full corpus")
        for passage in passages:
            expected = sources[passage.document_id]
            actual = passage.attribution
            if not actual or (expected.source_sha256, expected.doi, expected.publication_date) != (
                actual.source_sha256,
                actual.doi,
                actual.publication_date,
            ):
                raise ValueError("Original source version differs from dataset")
    for case in dataset.cases:
        for ref in case.references:
            passage = by_id.get(ref.passage_id)
            if not passage or (passage.document_id, passage.paragraph) != (
                ref.source_id,
                ref.paragraph,
            ):
                raise ValueError("Expected passage/source/paragraph reference is stale")
            if (
                ref.source_section is not None and ref.source_section != passage.source_section
            ) or (ref.source_locator is not None and ref.source_locator != passage.source_locator):
                raise ValueError("Expected source location is stale")
    return passages


def code_state() -> dict:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

    try:
        # Paths/diff contents are not saved, only identity and a dirty flag/hash.
        return {
            "commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
            "evaluation_code_sha256": canonical_hash(
                {
                    path.relative_to(ROOT / "backend").as_posix(): digest(
                        path.read_bytes().replace(b"\r\n", b"\n")
                    )
                    for package in ("researchlens", "researchlens_eval")
                    for path in sorted((ROOT / "backend" / package).rglob("*.py"))
                }
            ),
        }
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}
