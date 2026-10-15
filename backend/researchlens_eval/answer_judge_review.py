"""Offline agreement measurements for the frozen owner-grading sample."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from researchlens_eval.answer_grading import ROOT, TYPES

REVIEW = ROOT / "evaluation/reviews/2026-10-14-answer-judge"


def load_grades(path, key, half):
    expected = {item["id"] for item in key["items"] if item["half"] == half}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(expected) or {row["item_id"] for row in rows} != expected:
        raise ValueError("Grades must contain each item in this half exactly once")
    if any(row["verdict"] not in ("PASS", "FAIL", "UNCERTAIN") for row in rows):
        raise ValueError("Invalid owner verdict")
    if any(not row["notes"].strip() for row in rows):
        raise ValueError("Owner grades require notes")
    return {row["item_id"]: row for row in rows}


def agreement(items, grades, predictions):
    result = {}
    for kind in TYPES:
        selected = [item for item in items if item["type"] == kind]
        binary = []
        uncertain = unknown = agreed = 0
        for item in selected:
            verdict = grades[item["id"]]["verdict"]
            predicted = predictions[item["id"]]
            uncertain += verdict == "UNCERTAIN"
            unknown += predicted is None
            if verdict != "UNCERTAIN" and predicted is not None:
                human = verdict == "PASS"
                binary.append((human, predicted))
                agreed += human == predicted
        counts = Counter(binary)
        total = len(binary)
        observed = sum(human == predicted for human, predicted in binary) / total if total else None
        expected = (
            sum(
                sum(human == value for human, _ in binary)
                * sum(predicted == value for _, predicted in binary)
                for value in (False, True)
            )
            / total**2
            if total
            else None
        )
        kappa = (
            (observed - expected) / (1 - expected)
            if expected is not None and expected < 1
            else None
        )
        accuracy = agreed / len(selected) if selected else None
        result[kind] = {
            "items": len(selected),
            "agreed": agreed,
            "accuracy_all_items": accuracy,
            "binary_pairs": total,
            "accuracy_decidable_pairs": observed,
            "owner_uncertain": uncertain,
            "judge_unknown": unknown,
            "confusion": {
                "human_pass_judge_pass": counts[(True, True)],
                "human_pass_judge_fail": counts[(True, False)],
                "human_fail_judge_pass": counts[(False, True)],
                "human_fail_judge_fail": counts[(False, False)],
            },
            "cohens_kappa": kappa,
            "kappa_undefined_reason": (
                "No decidable pairs"
                if not total
                else "Both raters assign the same single class"
                if kappa is None
                else None
            ),
            "acceptance_bar_met": bool(
                accuracy is not None and accuracy >= 0.8 and kappa is not None and kappa >= 0.6
            ),
        }
    return result


def baseline(output):
    key = json.loads((REVIEW / "scoring-key.json").read_bytes())
    path = REVIEW / "calibration-grades.csv"
    grades = load_grades(path, key, "calibration")
    items = [item for item in key["items"] if item["half"] == "calibration"]
    result = {
        "judge": "Archived #16 predictions, including deterministic status and quote checks",
        "half": "calibration",
        "grades_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "key_sha256": hashlib.sha256((REVIEW / "scoring-key.json").read_bytes()).hexdigest(),
        "uncertain_policy": (
            "UNCERTAIN owner grades and unknown judge predictions get no agreement credit in "
            "the all-item accuracy. Kappa uses decidable binary pairs only; exclusions are counted."
        ),
        "metrics": agreement(items, grades, {item["id"]: item["prediction"] for item in items}),
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    baseline(args.output)


if __name__ == "__main__":
    main()
