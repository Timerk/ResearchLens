"""Development-only audit metadata. No retrieval, scoring, or held-out JSON parsing."""

import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main():
    dataset = read("evaluation/datasets/technical-development.json")
    labels = read("evaluation/labels/technical-development.json")
    positives = [case for case in dataset["cases"] if not case["expected_abstention"]]
    support = {
        case["case_id"]: {
            span["passage_id"]
            for group in case["groups"]
            for alternative in group["alternatives"]
            for span in alternative
        }
        for case in labels["cases"]
    }
    overlapping = [
        {
            "case_ids": [left, right],
            "shared_approved_passage_ids": sorted(support[left] & support[right]),
        }
        for left, right in itertools.combinations(support, 2)
        if support[left] & support[right]
    ]
    tracked = subprocess.check_output(
        [
            "git",
            "ls-files",
            "data/technical",
            "evaluation/datasets",
            "evaluation/labels",
            "evaluation/reviews",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    # Hash bytes only. Never parse or print held-out questions, including mixed archives.
    hashes = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in tracked}
    result = {
        "audit_date": "2026-10-05",
        "base_commit": "0542fb8aa1ac87b96d0e6b91320a48e2f4328889",
        "reviewer": "Codex / GPT-6-Astra, AI-assisted audit, no independent human sign-off",
        "method": (
            "Development questions and primary-source audit; prior review entries filtered to "
            "development; held-out JSON never parsed by this script."
        ),
        "boundary_incident": (
            "An earlier schema probe called list() on rejected-cases.json, which is a list rather "
            "than a mapping, and emitted rejected held-out draft records. It was stopped. The "
            "frozen held-out dataset was not opened or queried. No rejected draft was used to "
            "propose changes. This exposure means the overall session must not be described as "
            "having zero held-out-related text exposure."
        ),
        "case_count": len(dataset["cases"]),
        "answerable_count": len(positives),
        "negative_count": len(dataset["cases"]) - len(positives),
        "query_styles": dict(Counter(case["query_style"] for case in dataset["cases"])),
        "positive_source_incidence": dict(
            Counter(source for case in positives for source in case["expected_source_ids"])
        ),
        "positive_pairs": len(positives) * (len(positives) - 1) // 2,
        "positive_pairs_sharing_approved_passages": len(overlapping),
        "passage_overlap_interpretation": (
            "Shared accepted passages indicate dependence, not identical factual targets. This is "
            "a within-development calculation, not a split-leakage audit."
        ),
        "overlapping_case_pairs": overlapping,
        "protected_file_sha256": hashes,
    }
    target = OUT / "input-audit.json"
    if target.exists():
        before = json.loads(target.read_text(encoding="utf-8"))["protected_file_sha256"]
        if before != hashes:
            raise ValueError("Protected input hashes changed since the initial audit snapshot")
    target.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "case_count",
                    "answerable_count",
                    "negative_count",
                    "query_styles",
                    "positive_source_incidence",
                    "positive_pairs",
                    "positive_pairs_sharing_approved_passages",
                )
            },
            indent=2,
        )
    )
    print(f"Verified {len(hashes)} protected byte hashes; no held-out content parsed.")


if __name__ == "__main__":
    main()
