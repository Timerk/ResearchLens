"""Exact offline migration proposals. No searches and no approval metadata copying."""

import copy
import json
from collections import Counter
from pathlib import Path

from researchlens.artifacts import load_artifact, passage_identity
from researchlens.evaluation import encoded, load_dataset, validate_dataset_references
from researchlens.evaluation_evidence import EvidenceLabels, dataset_digest, validate_labels
from researchlens.ingest import ROOT, chunk_documents


def boundary(position: int, edits: list[tuple]) -> int:
    delta = 0
    for start, end, new_start, new_end in edits:
        if start < position < end:
            raise ValueError("Span boundary lies inside a replaced formula placeholder")
        if position <= start:
            break
        delta += (new_end - new_start) - (end - start)
    return position + delta


def window_ranges(passages: list) -> dict:
    """The chunker normalizes whitespace; its windows partition each paragraph."""
    ranges = {}
    positions = Counter()
    for passage in passages:
        key = (passage.document_id, passage.paragraph)
        start = positions[key]
        ranges[passage.id] = (start, start + len(passage.text))
        positions[key] += len(passage.text) + 1
    return ranges


def remap_span(span: dict, old: dict, new: dict, alignments: dict, old_ranges, new_ranges):
    passage = old.get(span["passage_id"])
    if not passage or passage.text[span["start"] : span["end"]] != span["quote"]:
        raise ValueError("Approved span does not match canonical text")
    key = (passage.document_id, passage.paragraph)
    base = old_ranges[passage.id][0]
    try:
        start = boundary(base + span["start"], alignments[key])
        end = boundary(base + span["end"], alignments[key])
    except ValueError as error:
        return "cannot map", [], str(error)
    mapped = []
    for candidate in new.values():
        if (candidate.document_id, candidate.paragraph) != key:
            continue
        left, right = new_ranges[candidate.id]
        a, b = max(start, left), min(end, right)
        if a < b:
            quote = candidate.text[a - left : b - left]
            mapped.append(
                {"passage_id": candidate.id, "start": a - left, "end": b - left, "quote": quote}
            )
    if not mapped:
        return "cannot map", [], "No candidate window covers the aligned quote"
    quote = " ".join(s["quote"] for s in mapped)
    if quote != span["quote"]:
        status = "quote text changed"
    elif mapped == [span]:
        status = "unchanged"
    else:
        status = "shifted only"
    return status, mapped, "Split into AND fragments" if len(mapped) > 1 else None


def remap_labels(labels: dict, old_passages, new_passages, alignments):
    proposed = copy.deepcopy(labels)
    old, new = ({p.id: p for p in passages} for passages in (old_passages, new_passages))
    old_ranges, new_ranges = (window_ranges(p) for p in (old_passages, new_passages))
    records = []
    for case in proposed["cases"]:
        for group in case["groups"]:
            for ai, option in enumerate(group["alternatives"]):
                updated = []
                for si, span in enumerate(option):
                    status, mapped, reason = remap_span(
                        span, old, new, alignments, old_ranges, new_ranges
                    )
                    records.append(
                        {
                            "case_id": case["case_id"],
                            "group_id": group["id"],
                            "alternative_index": ai,
                            "span_index": si,
                            "status": status,
                            "old": span,
                            "new": mapped,
                            "reason": reason,
                        }
                    )
                    updated.extend(mapped)
                # Never silently score a weakened alternative if any span cannot map.
                if any(
                    r["status"] == "cannot map"
                    for r in records
                    if r["case_id"] == case["case_id"]
                    and r["group_id"] == group["id"]
                    and r["alternative_index"] == ai
                ):
                    updated = []
                group["alternatives"][ai] = updated
    proposed.update(review_status="unreviewed", reviewer=None, review_date=None)
    proposed["notes"] = (
        "Candidate offset/text migration only; owner approval and scientific review pending. "
        "Group descriptions, claim indexes and alternatives retained. Split spans remain AND. "
        "Original approval applies only to canonical labels."
    )
    return proposed, records


def review_markdown(records: list[dict], inventory: dict) -> str:
    counts = Counter(r["status"] for r in records)
    lines = [
        "# Candidate span remapping review",
        "",
        "All offsets are half-open Unicode character offsets. Every occurrence was checked "
        "against the canonical quote. Only complete formula placeholders are replaced; "
        "all surrounding prose must match exactly. No fuzzy matching or semantic relabeling.",
        "",
        f"Classification counts: {dict(counts)}.",
        "",
        "Candidate labels are unreviewed. Splitting one span across windows requires all "
        "fragments together in the same alternative. This preserves the approved text "
        "requirement but can change retrieval coverage because passage boundaries change.",
        "",
        "## Held-out inventory",
        "",
        inventory["notes"],
        "",
        f"Reference counts: {inventory['counts']}. Freeze check: {inventory['freeze_check']}.",
        "",
        "| Held-out case / reference | Status | Old ID | Proposed IDs | Same source location |",
        "| --- | --- | --- | --- | --- |",
        *[
            f"| {r['case_id']} / {r['reference_index']} | {r['status']} | "
            f"{r['old_passage_id']} | {', '.join(r['proposed_passage_ids'])} | "
            f"{r['same_source_location']} |"
            for r in inventory["references"]
        ],
        "",
        "## Changed or unmappable occurrences",
        "",
        "| Case / group / alternative / span | Status and locations | Old quote | New quote |",
        "| --- | --- | --- | --- |",
    ]

    def escape(value):
        return value.replace("|", "\\|").replace("\n", "<br>")

    for row in records:
        if row["status"] == "unchanged":
            continue
        old = row["old"]
        location = f"{old['passage_id']}[{old['start']}:{old['end']}]"
        targets = (
            "; ".join(f"{s['passage_id']}[{s['start']}:{s['end']}]" for s in row["new"]) or "none"
        )
        key = (
            f"{row['case_id']} / {row['group_id']} / "
            f"{row['alternative_index']} / {row['span_index']}"
        )
        quote = escape(" ".join(s["quote"] for s in row["new"])) or "Cannot map"
        lines.append(
            f"| {key} | {row['status']}: {location} to {targets}. {row['reason'] or ''} | "
            f"{escape(old['quote'])} | {quote} |"
        )
    return "\n".join(lines) + "\n"


def held_out_reference_review(held_out: dict, old_passages, new_passages, artifact, alignments):
    """Inspect only frozen pins and references, never questions, answers or claims."""
    old, new = ({p.id: p for p in passages} for passages in (old_passages, new_passages))
    old_ranges, new_ranges = (window_ranges(p) for p in (old_passages, new_passages))
    rows = []
    for case in held_out["cases"]:
        for i, ref in enumerate(case["references"]):
            before = old[ref["passage_id"]]
            key = (before.document_id, before.paragraph)
            mapped_start, mapped_end = old_ranges[before.id]
            try:
                mapped_start = boundary(mapped_start, alignments[key])
                mapped_end = boundary(mapped_end, alignments[key])
            except ValueError:
                targets = []
            else:
                targets = [
                    p
                    for p in new_passages
                    if (p.document_id, p.paragraph) == key
                    and new_ranges[p.id][0] < mapped_end
                    and new_ranges[p.id][1] > mapped_start
                ]
            same_location = bool(targets) and all(
                (p.document_id, p.paragraph, p.source_section, p.source_locator)
                == (
                    ref["source_id"],
                    ref["paragraph"],
                    ref["source_section"],
                    ref["source_locator"],
                )
                for p in targets
            )
            ids = [p.id for p in targets]
            if not same_location:
                status = "unmappable"
            elif ids != [before.id]:
                status = "ID changed"
            elif new[before.id].text != before.text:
                status = "text changed"
            else:
                status = "unchanged"
            rows.append(
                {
                    "case_id": case["id"],
                    "reference_index": i,
                    "status": status,
                    "old_passage_id": before.id,
                    "proposed_passage_ids": ids,
                    "same_source_location": same_location,
                    "same_id_exists": before.id in new,
                    "same_id_text_changed": before.id in new and new[before.id].text != before.text,
                    "source_id": before.document_id,
                    "paragraph": before.paragraph,
                    "section": before.source_section,
                    "locator": before.source_locator,
                }
            )
    versions = {s["source_id"]: s for s in held_out["source_versions"]}
    source_versions_match = set(versions) == {p.document_id for p in new_passages} and all(
        (
            versions[p.document_id]["source_sha256"],
            versions[p.document_id]["doi"],
            versions[p.document_id]["publication_date"],
        )
        == (p.attribution.source_sha256, p.attribution.doi, p.attribution.publication_date)
        for p in new_passages
    )
    return {
        "approved_span_occurrences": 0,
        "reference_occurrences": len(rows),
        "counts": dict(Counter(r["status"] for r in rows)),
        "references": rows,
        "freeze_check": {
            "frozen_corpus_sha256": held_out["corpus_sha256"],
            "candidate_corpus_sha256": artifact["source_sha256"],
            "corpus_pin_matches": held_out["corpus_sha256"] == artifact["source_sha256"],
            "source_versions_match": source_versions_match,
            "owner_decision": (
                "Adoption requires a new held-out dataset version and owner approval."
            ),
        },
        "notes": (
            "Held-out has references only. Every reference was checked offline by source "
            "paragraph alignment and candidate window coverage. ID changed takes precedence "
            "when the old window's content now requires different or multiple IDs. Text changed "
            "means the same ID covers the aligned range but its passage text differs. "
            "Questions, answers and claims did not guide rendering. No held-out retrieval ran."
        ),
    }


def build_remapping(destination: Path, canonical, proposed, alignments) -> dict:
    from researchlens.formula_prototype import digest

    artifact, passages = load_artifact(
        destination / "index.json", source=destination / "documents.json"
    )
    old_passages = chunk_documents(canonical)
    baseline_artifact = {
        **artifact,
        "source_sha256": digest(ROOT / "data/technical/documents.json"),
        "passages": [p.model_dump(mode="json") for p in old_passages],
    }
    records = []
    outputs = {}
    label_paths = [ROOT / "evaluation/labels/technical-development.json"]
    datasets = [
        load_dataset(ROOT / "evaluation/datasets" / f"{name}.json")
        for name in ("technical-development",)
    ]
    for dataset in datasets:
        candidate_dataset = dataset.model_copy(deep=True)
        candidate_dataset.corpus_sha256 = artifact["source_sha256"]
        candidate_dataset.status = "draft"
        for case in candidate_dataset.cases:
            case.review_status, case.reviewer, case.review_date = "unreviewed", None, None
        # Reference IDs identify paragraph windows, not approved exact spans. Retain only
        # valid locations; any missing reference requires an explicit offline review.
        validate_dataset_references(candidate_dataset, artifact)
        dataset_path = destination / f"{dataset.split}-dataset.json"
        dataset_path.write_bytes(encoded(candidate_dataset.model_dump(mode="json")))
        matches = []
        for path in label_paths:
            labels = EvidenceLabels.model_validate_json(path.read_bytes())
            if (
                labels.dataset_sha256 == dataset_digest(dataset)
                and labels.review_status == "approved"
            ):
                matches.append((path, labels))
        if len(matches) > 1:
            raise ValueError("Multiple approved label files for one dataset")
        for path, labels in matches:
            validate_labels(labels, dataset, baseline_artifact, old_passages)
            candidate, rows = remap_labels(
                labels.model_dump(mode="json"), old_passages, passages, alignments
            )
            candidate.update(
                dataset_sha256=dataset_digest(candidate_dataset),
                corpus_sha256=artifact["source_sha256"],
                shared_passage_sha256=passage_identity(artifact, passages),
            )
            if not any(r["status"] == "cannot map" for r in rows):
                validate_labels(
                    EvidenceLabels.model_validate(candidate), candidate_dataset, artifact, passages
                )
            output = destination / f"{dataset.split}-labels.json"
            output.write_bytes(encoded(candidate))
            for row in rows:
                row["split"] = dataset.split
            records.extend(rows)
            outputs[dataset.split] = {
                "approved_labels_file": str(path.relative_to(ROOT)),
                "approved_labels_sha256": digest(path),
                "candidate_labels_sha256": digest(output),
                "candidate_dataset_sha256": digest(dataset_path),
                "counts": dict(Counter(r["status"] for r in rows)),
            }
    held_out_path = ROOT / "evaluation/datasets/held-out.json"
    inventory = held_out_reference_review(
        json.loads(held_out_path.read_bytes()), old_passages, passages, artifact, alignments
    )
    inventory["dataset_sha256"] = digest(held_out_path)
    report = {
        "schema_version": 1,
        "outputs": outputs,
        "held_out_inventory": inventory,
        "records": records,
    }
    (destination / "remapping.json").write_bytes(encoded(report))
    (destination / "remapping-review.md").write_text(
        review_markdown(records, inventory), encoding="utf-8"
    )
    return {
        "outputs": outputs,
        "held_out_inventory": inventory,
        "total": len(records),
        "counts": dict(Counter(r["status"] for r in records)),
    }
