"""Archive the runner summary and freeze the development-selected context configuration."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from researchlens.artifacts import canonical_hash  # noqa: E402
from researchlens.evaluation import encoded  # noqa: E402
from researchlens.ingest import ROOT  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    args = parser.parse_args()
    args.study = args.study.resolve()
    summary = json.loads((args.study / "summary.json").read_bytes())
    for entry in summary["runs"].values():
        provenance = entry["archive_provenance"]
        if (
            hashlib.sha256((ROOT / provenance["path"]).read_bytes()).hexdigest()
            != provenance["sha256"]
        ):
            raise ValueError("Run archive changed since summarization")
    for name, expected in summary["manifest"]["source_sha256"].items():
        if (
            hashlib.sha256((ROOT / "backend/researchlens" / name).read_bytes()).hexdigest()
            != expected
        ):
            raise ValueError("Executable study source changed since measurement")
    selected = summary["runs"]["qwen3-4b-dense"]
    budget = next(
        int(b)
        for b, s in selected["summaries"].items()
        if s["all_groups"]["complete_evidence_cases"] >= 29
    )
    retrieval = json.loads((ROOT / "docs/development-selected-retrieval.json").read_bytes())
    retrieval["limit"] = 40
    if retrieval["artifact_sha256"] != selected["corpus"]["artifact_sha256"]:
        raise ValueError("Incumbent retrieval does not match measured artifact")
    summary["archive_provenance"] = {
        "format": "research-summary-v1",
        "full_archive_sha256": hashlib.sha256(
            (args.study / "summary.json").read_bytes()
        ).hexdigest(),
        "path": str((args.study / "summary.json").relative_to(ROOT)),
        "scope": (
            "Summary and per-question token estimates; "
            "full context/group records remain in run archives."
        ),
    }
    for entry in summary["runs"].values():
        cases = entry.pop("cases")
        entry["cases_archived_count"] = len(cases)
        entry["per_question_input_tokens_estimate"] = {
            c["case_id"]: {b: p["input_tokens_estimate"] for b, p in c["budgets"].items()}
            for c in cases
        }
    config = {
        "schema_version": 1,
        "selection_date": "2026-10-13",
        "status": "development-selected; application default remains four passages pending review",
        "selection_rule": (
            "retain incumbent Qwen dense; smallest tested budget "
            "reaching 29/36 all-group complete evidence"
        ),
        "retrieval": retrieval,
        "answer_context": {
            "mode": "characters",
            "max_context_chars": budget,
            "max_passage_chars": 3000,
            "retrieval_candidates": 40,
            "serialization": "json.dumps passage-item list, ensure_ascii=True, default separators",
            "overflow_policy": "stop before first item exceeding serialized cap",
        },
        "scoring_view": "all_groups",
        "asked_groups_view": "diagnostic only; official target decision remains with owner",
        "dataset_sha256": summary["manifest"]["dataset_sha256"],
        "evidence_labels_sha256": summary["manifest"]["evidence_labels_sha256"],
        "corpus_sha256": selected["corpus"]["source_sha256"],
        "shared_passage_sha256": selected["corpus"]["shared_passage_sha256"],
        "study_summary_sha256": canonical_hash(summary),
        "development_result": selected["summaries"][str(budget)]["all_groups"],
        "held_out_searches": False,
        "answer_quality_measured": False,
    }
    for path, value in (
        (ROOT / "docs/context-budget-results.json", summary),
        (ROOT / "docs/development-selected-context-budget.json", config),
    ):
        with path.open("xb") as stream:
            stream.write(encoded(value))
    print(f"Archived development selection: {budget} serialized characters")


if __name__ == "__main__":
    main()
