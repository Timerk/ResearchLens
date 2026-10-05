"""Post-replay, owner-unresolved sensitivity for the shortcut question only.

Uses replay.py's adapters and the existing scorer. Does not change the main
proposal snapshot or classify this post-outcome judgment as an approved correction.
"""

import argparse
import json
from pathlib import Path

import replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new exploratory artifact")
    directory = Path(__file__).resolve().parent
    overlay_path = directory / "proposed-revisions.json"
    results_path = directory / "replay-results.json"
    protected = {str(p.name): replay.file_hash(p) for p in (overlay_path, results_path)}
    overlay = json.loads(overlay_path.read_bytes())
    previous = json.loads(results_path.read_bytes())
    assert len(overlay["changes"]) == 13
    assert previous["proposed_contract"]["overlay_sha256"] == protected[overlay_path.name]
    dataset, entries, passages, identity = replay.load_inputs()
    by_id = {p.id: p for p in passages}
    cases = {c.id: c for c in dataset.cases}
    cid = "tech-too-many-shortcuts"
    change = {
        "id": "post-replay-shortcut-narrow-empirical-answer",
        "case_id": cid,
        "group_id": "residual-purpose",
        "action": "remove_group",
        "category": "exploratory-question-scope",
        "status": "owner-unresolved",
        "rubric_dependency": (
            "The explicit residual-discrimination qualification would be conditional on an "
            "answer adding that mechanism. P16 does not support the unchanged residual-purpose "
            "claim. Owner adjudication must decide whether a narrow empirical answer suffices."
        ),
    }
    main_entries = replay.apply_changes(entries, overlay["changes"], cases, by_id)
    exploratory_entries = replay.apply_changes(entries, [*overlay["changes"], change], cases, by_id)
    _, _, archive, archive_path = next(
        row for row in replay.archived_runs(identity) if row[1] == "bge-m3-bge-rerank20"
    )
    original_rows = replay.score_rows(archive["cases"], dataset, entries, by_id)
    main_rows = replay.score_rows(archive["cases"], dataset, main_entries, by_id)
    exploratory_rows = replay.score_rows(archive["cases"], dataset, exploratory_entries, by_id)
    previous_run = next(r for r in previous["runs"] if r["name"] == "bge-m3-bge-rerank20")
    replay.assert_equal(
        replay.summarize_rows(dataset, main_rows),
        previous_run["proposed_scenarios"]["combined"]["summary"],
        "main sensitivity summary",
    )
    summaries = {}
    for name, rows in (
        ("approved-original", original_rows),
        ("main-13-change-snapshot", main_rows),
        ("post-replay-exploratory-shortcut-scope", exploratory_rows),
    ):
        summaries[name] = {
            "summary": replay.summarize_rows(dataset, rows),
            "remaining_incomplete": [
                r["case_id"] for r in rows if r["metrics_at_k"]["4"]["complete_evidence"] is False
            ],
            "shortcut_case": next(r for r in rows if r["case_id"] == cid),
        }
    changed = [
        before["case_id"]
        for before, after in zip(main_rows, exploratory_rows, strict=True)
        if before["metrics_at_k"] != after["metrics_at_k"]
    ]
    assert changed == [cid]
    pool_counts = replay.pool_diagnostics(
        entries,
        {"main": main_entries, "exploratory": exploratory_entries},
        cases,
        identity,
    )
    core_group = next(g for g in entries[cid].groups if g.id == "part-1")
    quotes = [s.model_dump(mode="json") for s in core_group.alternatives[0]]
    result = {
        "schema_version": 1,
        "status": "AI-assisted, post-outcome exploratory, owner-unresolved",
        "not_an_approved_correction_or_retrieval_quality_result": True,
        "order_disclosure": (
            "The main first-pass semantic audit treated the residual-purpose qualification as "
            "necessary. After replay exposed the remaining failure, follow-up AI adjudication "
            "considered whether the narrower empirical explanation already answers the visible "
            "why question. This judgment was made after observing retrieval outcomes."
        ),
        "protected_main_snapshot_hashes": protected,
        "cached_archive": archive_path,
        "cached_archive_sha256": replay.file_hash(replay.ROOT / archive_path),
        "case_id": cid,
        "visible_question": cases[cid].question,
        "proposed_change": change,
        "source": {
            "passage_id": "pmc11121878:p16:w0",
            "source_url": by_id["pmc11121878:p16:w0"].source_url,
            "source_locator": by_id["pmc11121878:p16:w0"].source_locator,
            "source_section": by_id["pmc11121878:p16:w0"].source_section,
            "exact_canonical_quotes": quotes,
        },
        "acceptable_narrow_answer_if_owner_adopts_scope": (
            "The authors found that two strategically placed skip connections worked best in "
            "their experiments; connecting every layer partly reconstructed the defects."
        ),
        "claim_not_established_by_p16_or_p16_plus_p17": (
            "Partial defect reconstruction reduces residual-based discrimination."
        ),
        "scenarios": summaries,
        "changed_cases_from_main": changed,
        "bge20_oracle_complete_counts": {
            name: pool["bge20"]["complete_count"] for name, pool in pool_counts["scenarios"].items()
        },
        "qwen40_oracle_complete_counts": {
            name: pool["qwen40"]["complete_count"]
            for name, pool in pool_counts["scenarios"].items()
        },
        "recommendation": (
            "Owner should adjudicate required causal depth from the visible question before "
            "adopting any score change. Keep the approved 26/36 and main unreviewed 28/36 "
            "snapshot; do not claim that this sensitivity meets the original 29/36 target."
        ),
    }
    assert protected == {str(p.name): replay.file_hash(p) for p in (overlay_path, results_path)}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {name: value["summary"]["complete_evidence_cases"] for name, value in summaries.items()}
        )
    )


if __name__ == "__main__":
    main()
