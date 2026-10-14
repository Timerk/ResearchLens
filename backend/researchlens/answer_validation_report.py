"""Verify sealed owner grades and publish one frozen validation comparison."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from researchlens.answer_judge_freeze import assert_frozen
from researchlens.answer_judge_review import REVIEW, agreement, load_grades
from researchlens.artifacts import canonical_hash


def verified_grades(path):
    frozen = assert_frozen()
    record = (REVIEW / "owner-review.md").read_text(encoding="utf-8")
    match = re.search(r"Sealed validation CSV SHA-256: ([a-f0-9]{64})", record)
    if not match:
        raise ValueError("Owner review has no sealed validation checksum")
    expected = match.group(1)
    measured = hashlib.sha256(path.read_bytes()).hexdigest()
    if measured != expected:
        raise ValueError("Sealed validation grades do not match owner-review.md")
    key = json.loads((REVIEW / "scoring-key.json").read_bytes())
    grades = load_grades(path, key, "validation")
    return frozen, key, grades, measured


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grades", required=True, type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Validation result already exists; do not evaluate twice")
    frozen, key, grades, digest = verified_grades(args.grades)
    items = [item for item in key["items"] if item["half"] == "validation"]
    result = {
        "validation_sha256": digest,
        "frozen_contract_sha256": canonical_hash(frozen["contract"]),
        "items": len(grades),
        "owner_uncertain": sum(row["verdict"] == "UNCERTAIN" for row in grades.values()),
    }
    if args.predictions:
        predictions = json.loads(args.predictions.read_bytes())
        if predictions.keys() != grades.keys():
            raise ValueError("Frozen predictions must match every validation item exactly once")
        result.update(
            archived_baseline=agreement(
                items, grades, {item["id"]: item["prediction"] for item in items}
            ),
            frozen_judge=agreement(items, grades, predictions),
            validation_evaluation_count=1,
            uncertainty_policy=(
                "UNCERTAIN and unknown get no success credit in all-item accuracy; "
                "kappa uses decidable binary pairs with exclusions reported."
            ),
        )
        result["reliable_types"] = [
            kind for kind, metric in result["frozen_judge"].items() if metric["acceptance_bar_met"]
        ]
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
