"""Keep research summaries in Git; full case records belong in evaluation/runs.

Run from the repository root:
    python evaluation/scripts/compact_results.py INPUT OUTPUT

The original file's hash is retained. For an existing Git archive, pass
--source-commit and --source-path to record an immutable recovery link.
This does not change evaluation scores or create a runnable evaluation artifact.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

DETAIL_LISTS = {"cases", "selection", "measurements", "candidate_metrics"}


def paired_summary(rows: list[dict]) -> dict:
    """Retain outcome counts and case identities without duplicate passage/group rows."""
    outcomes = Counter(row["outcome"] for row in rows)
    changes = {}
    for direction, predicate in (
        ("complete_gains", lambda before, after: before is False and after is True),
        ("complete_losses", lambda before, after: before is True and after is False),
    ):
        changes[direction] = [
            row["case_id"]
            for row in rows
            if predicate(
                (row.get("baseline_metrics") or {}).get(
                    "complete_evidence", row.get("complete_before")
                ),
                (row.get("candidate_metrics") or {}).get(
                    "complete_evidence", row.get("complete_after")
                ),
            )
        ]
    return {
        "case_count": len(rows),
        "outcomes": dict(sorted(outcomes.items())),
        "changed_case_ids": {
            outcome: [row["case_id"] for row in rows if row["outcome"] == outcome]
            for outcome in sorted(outcomes)
            if outcome not in {"unchanged", "not-scored", "unavailable"}
        },
        **changes,
    }


def compact(value):
    """Preserve manifests, metrics, costs, pins and summary denominators verbatim."""
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if (
                isinstance(child, list)
                and child
                and all(
                    isinstance(row, dict) and {"case_id", "outcome", "deltas"} <= row.keys()
                    for row in child
                )
            ):
                result[key + "_summary"] = paired_summary(child)
            elif key in DETAIL_LISTS and isinstance(child, list):
                result[key + "_archived_count"] = len(child)
            else:
                result[key] = compact(child)
        return result
    if isinstance(value, list):
        return [compact(child) for child in value]
    return value


def compact_archive(
    raw: bytes, *, source_commit: str | None = None, source_path: str | None = None
):
    archive = compact(json.loads(raw))
    if not isinstance(archive, dict):
        raise ValueError("Research archive must be a JSON object")
    archive["archive_provenance"] = {
        "format": "research-summary-v1",
        "full_archive_sha256": hashlib.sha256(raw).hexdigest(),
        "scope": "Summary only; per-case scoring and inference records are in the full archive.",
    }
    if source_commit is not None:
        if source_path is None:
            raise ValueError("--source-path is required with --source-commit")
        archive["archive_provenance"].update(
            {
                "source_commit": source_commit,
                "source_path": source_path,
                "full_archive_url": (
                    f"https://github.com/Timerk/ResearchLens/blob/{source_commit}/{source_path}"
                ),
            }
        )
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-commit")
    parser.add_argument("--source-path")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Use a separate output file to preserve the full archive")
    archive = compact_archive(
        args.input.read_bytes(), source_commit=args.source_commit, source_path=args.source_path
    )
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(archive, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
