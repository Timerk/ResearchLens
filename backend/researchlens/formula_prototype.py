"""Offline, proposal-only MathML extraction into an isolated versioned corpus.

This module never writes the canonical corpus, index, manifest, or approved labels.
Unknown MathML remains explicitly omitted instead of guessing its meaning.
"""

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from researchlens.corpus import DIRECTORY, SOURCES, extract
from researchlens.ingest import ROOT
from researchlens.mathml import local_name, readable_prose, render_math  # noqa: F401

VERSION = "mathml-readable-v2"
DESTINATION = ROOT / "evaluation" / "runs" / VERSION
LABELS = ROOT / "evaluation" / "labels" / "technical-development.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_prototype(destination: Path = DESTINATION) -> dict:
    if not destination.resolve().is_relative_to((ROOT / "evaluation" / "runs").resolve()):
        raise ValueError("Prototype destination must stay under evaluation/runs")
    if destination.exists():
        raise ValueError("Use a fresh candidate destination")
    canonical, proposed, sources = [], [], []
    alignments = {}
    for pmcid in SOURCES:
        path = DIRECTORY / "originals" / f"{pmcid}.xml"
        raw = path.read_bytes()
        document, _ = extract(raw, pmcid, readable_formulas=False)
        canonical.append(document)
        root = ET.fromstring(raw)
        counts = Counter()
        paragraphs = []
        for paragraph, source in enumerate(document.paragraph_sources, 1):
            element = root.find(source.locator)
            if element is None:
                raise ValueError(f"Source paragraph missing: {source.locator}")
            replacements = []
            paragraphs.append(readable_prose(element, counts, replacements))
            before = document.text.split("\n\n")[paragraph - 1]
            alignments[(document.id, paragraph)] = formula_alignment(
                before, paragraphs[-1], replacements
            )
        proposal = document.model_copy(deep=True)
        proposal.text = "\n\n".join(paragraphs)
        proposal.attribution.changes = proposal.attribution.changes.replace(
            "Mathematical formula markup is replaced with [formula omitted]. ", ""
        ) + (
            f" Proposal-only {VERSION}: supported presentation MathML rendered as "
            "grouped plain text; unsupported formulas remain omitted. Not scientifically reviewed."
        )
        proposed.append(proposal)
        sources.append(
            {
                "document_id": document.id,
                "original_sha256": digest(path),
                "mathml_elements_in_original": sum(
                    local_name(node) == "math" for node in root.iter()
                ),
                "paragraphs_changed": sum(
                    old != new
                    for old, new in zip(document.text.split("\n\n"), paragraphs, strict=True)
                ),
                **counts,
            }
        )
    checked_in_path = DIRECTORY / "documents.json"
    adoption = ROOT / "evaluation/reviews/2026-10-14-pr15"
    historical = (adoption / "approval.json").exists()
    if historical:
        # Historical baseline is reconstructed from immutable XML, never from current labels.
        checked_in = [doc.model_dump(mode="json") for doc in canonical]
        expected = json.loads((adoption / "approval.json").read_bytes())["previous_corpus_sha256"]
        raw = (json.dumps(checked_in, ensure_ascii=False, indent=2) + "\n").encode()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Historical canonical extraction no longer reproduces")
    else:
        checked_in = json.loads(checked_in_path.read_text(encoding="utf-8"))
        expected = digest(checked_in_path)
    if [doc.model_dump(mode="json") for doc in canonical] != checked_in:
        raise ValueError("Canonical re-extraction differs from the pinned corpus")
    summary = {
        "schema_version": 1,
        "artifact_version": VERSION,
        "prototype_script_sha256": digest(Path(__file__)),
        "implementation_sha256": {
            name: digest(Path(__file__).with_name(name))
            for name in ("formula_prototype.py", "formula_remapping.py", "mathml.py", "corpus.py")
        },
        "protected_inputs_sha256": {
            path: digest(ROOT / path)
            for path in (
                "data/technical/documents.json",
                "data/technical/manifest.json",
                "evaluation/labels/technical-development.json",
                "evaluation/datasets/technical-development.json",
                "evaluation/datasets/held-out.json",
            )
        },
        "status": "historical_candidate_already_adopted"
        if historical
        else "proposal_only_owner_approval_required",
        "canonical_documents_sha256": expected,
        "approved_development_labels_sha256": digest(
            adoption / "labels/technical-development.json" if historical else LABELS
        ),
        "scope": "candidate corpus; offline label remapping; development-only local retrieval",
        "chunking": {"method": "paragraph-word-windows", "max_words": 180},
        "sources": sources,
    }
    destination.mkdir(parents=True, exist_ok=True)
    documents_path = destination / "documents.json"
    documents_path.write_text(
        json.dumps([doc.model_dump() for doc in proposed], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    summary["prototype_documents_sha256"] = digest(documents_path)
    from researchlens.formula_remapping import build_remapping
    from researchlens.ingest import build_index

    build_index(documents_path, destination / "index.json")
    summary["candidate_index_sha256"] = digest(destination / "index.json")
    summary["label_remapping"] = build_remapping(destination, canonical, proposed, alignments)
    (destination / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return summary


def formula_alignment(before: str, after: str, replacements: list[str]) -> list[tuple]:
    """Align unchanged prose exactly and whole formula replacements atomically."""
    matches = list(re.finditer(re.escape("[formula omitted]"), before))
    if len(matches) != len(replacements):
        raise ValueError("Formula placeholder count differs")
    old_position = new_position = 0
    edits = []
    pieces = []
    for match, replacement in zip(matches, replacements, strict=True):
        prefix = before[old_position : match.start()]
        pieces.extend([prefix, replacement])
        new_position += len(prefix)
        if replacement != match.group():
            edits.append(
                (match.start(), match.end(), new_position, new_position + len(replacement))
            )
        old_position = match.end()
        new_position += len(replacement)
    pieces.append(before[old_position:])
    if "".join(pieces) != after:
        raise ValueError("Candidate changes extend beyond formula replacements")
    return edits


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DESTINATION)
    summary = build_prototype(parser.parse_args().destination)
    print(json.dumps(summary, ensure_ascii=True, indent=2))
