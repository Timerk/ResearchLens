"""Verify audit completeness and quotations with the existing canonical chunker."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from researchlens.ingest import chunk_documents  # noqa: E402
from researchlens.models import Document  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def spans(value):
    if isinstance(value, dict):
        if {"passage_id", "start", "end", "quote"} <= value.keys():
            yield value
        for child in value.values():
            yield from spans(child)
    elif isinstance(value, list):
        for child in value:
            yield from spans(child)


def main():
    dataset = read(ROOT / "evaluation/datasets/technical-development.json")
    cases = {case["id"]: case for case in dataset["cases"]}
    documents = [Document.model_validate(d) for d in read(ROOT / "data/technical/documents.json")]
    canonical = {passage.id: passage for passage in chunk_documents(documents)}
    names = ("canopy-heater.json", "wafer-autoencoder.json", "comparisons-negatives.json")
    audited = {}
    span_count = 0
    for name in names:
        artifact = read(OUT / name)
        for case in artifact["cases"]:
            cid = case.get("case_id", case.get("id"))
            if cid in audited or cid not in cases:
                raise ValueError(f"Duplicate or unknown case: {cid}")
            if case["question"] != cases[cid]["question"]:
                raise ValueError(f"Question changed in audit: {cid}")
            classified = {(r["field"], r["index"]) for r in case["requirements"]}
            expected = {
                (field, index)
                for field in ("required_claims", "required_qualifications", "forbidden_claims")
                for index in range(len(cases[cid][field]))
            }
            if classified != expected:
                raise ValueError(f"Incomplete requirement review: {cid}, {expected - classified}")
            audited[cid] = name
        for span in spans(artifact):
            passage = canonical[span["passage_id"]]
            if passage.text[span["start"] : span["end"]] != span["quote"]:
                raise ValueError(f"Audit quotation mismatch: {name}, {span['passage_id']}")
            if "source_id" in span and span["source_id"] != passage.document_id:
                raise ValueError("Audit source identity mismatch")
            if "source_locator" in span and span["source_locator"] != passage.source_locator:
                raise ValueError("Audit source locator mismatch")
            span_count += 1
    if audited.keys() != cases.keys():
        raise ValueError(f"Missing case reviews: {cases.keys() - audited.keys()}")
    hashes = read(OUT / "input-audit.json")["protected_file_sha256"]
    for path, checksum in hashes.items():
        # Byte hashing only, including held-out and mixed historical archives.
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != checksum:
            raise ValueError(f"Protected input changed: {path}")
    output = {
        "audit_cases": len(audited),
        "canonical_passages": len(canonical),
        "audit_quote_occurrences_checked": span_count,
        "all_original_requirement_indices_classified": True,
        "protected_files_unchanged": len(hashes),
        "case_artifacts": audited,
        "limits": (
            "Structural/exact-text validation, not proof of semantic correctness or human "
            "approval. Held-out content not parsed."
        ),
    }
    (OUT / "verification.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"Verified {len(audited)} cases, {span_count} audit quotes, {len(hashes)} unchanged files."
    )


if __name__ == "__main__":
    main()
