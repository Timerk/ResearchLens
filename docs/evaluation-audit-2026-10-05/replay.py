"""Replay development rankings through the existing scorer, without model inference.

Approved inputs are read-only. An optional unreviewed overlay is a sensitivity
analysis, never an approved EvidenceLabels replacement. No held-out file is read.
"""

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from pydantic import TypeAdapter  # noqa: E402
from researchlens.answers import prepare_answer_context  # noqa: E402
from researchlens.artifacts import canonical_hash, passage_identity  # noqa: E402
from researchlens.evaluation import validate_dataset_references  # noqa: E402
from researchlens.evaluation_evidence import (  # noqa: E402
    CaseEvidence,
    EvidenceLabels,
    EvidenceSpan,
    TextRange,
    dataset_digest,
    evidence_coverage,
    ranking_metrics,
    validate_labels,
)
from researchlens.evaluation_metrics import cutoff_summary  # noqa: E402
from researchlens.evaluation_schema import Dataset  # noqa: E402
from researchlens.ingest import CHUNKING, chunk_documents  # noqa: E402
from researchlens.models import Document, Passage, SearchHit  # noqa: E402
from researchlens.retrieval_analysis import minimal_supports  # noqa: E402


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_equal(actual, expected, location):
    if isinstance(expected, dict):
        for key, value in expected.items():
            assert key in actual, f"Missing field at {location}.{key}"
            assert_equal(actual[key], value, f"{location}.{key}")
    elif isinstance(expected, float):
        assert math.isclose(actual, expected, abs_tol=1e-12), location
    else:
        assert actual == expected, location


def load_inputs():
    source = ROOT / "data/technical/documents.json"
    dataset_path = ROOT / "evaluation/datasets/technical-development.json"
    labels_path = ROOT / "evaluation/labels/technical-development.json"
    dataset = Dataset.model_validate_json(dataset_path.read_bytes())
    assert dataset.split == "development"
    documents = TypeAdapter(list[Document]).validate_json(source.read_bytes())
    passages = chunk_documents(documents)
    artifact = {
        "schema_version": 2,
        "source_sha256": file_hash(source),
        "chunking": CHUNKING,
        "passages": [p.model_dump(mode="json") for p in passages],
    }
    validate_dataset_references(dataset, artifact)
    labels = EvidenceLabels.model_validate_json(labels_path.read_bytes())
    entries = validate_labels(labels, dataset, artifact, passages)
    assert set(entries) == {c.id for c in dataset.cases if not c.expected_abstention}
    assert len(dataset.cases) == 50 and len(entries) == 36 and len(passages) == 204
    spans = [s for e in labels.cases for g in e.groups for a in g.alternatives for s in a]
    manifest = json.loads((ROOT / "data/technical/manifest.json").read_bytes())
    originals = {}
    for item in manifest["sources"]:
        actual_hash = file_hash(ROOT / "data/technical" / item["original_file"])
        assert actual_hash == item["source_sha256"], "Original XML hash differs"
        originals[item["id"]] = actual_hash
    identity = {
        "dataset_file_sha256": file_hash(dataset_path),
        "dataset_digest": dataset_digest(dataset),
        "dataset_canonical_hash": canonical_hash(dataset.model_dump(mode="json")),
        "labels_file_sha256": file_hash(labels_path),
        "labels_canonical_hash": canonical_hash(labels.model_dump(mode="json")),
        "corpus_sha256": artifact["source_sha256"],
        "shared_passage_sha256": passage_identity(artifact, passages),
        "original_xml_hashes": originals,
        "document_count": len(documents),
        "passage_count": len(passages),
        "answerable_cases": len(entries),
        "negative_cases": len(dataset.cases) - len(entries),
        "groups": sum(len(e.groups) for e in entries.values()),
        "alternatives": sum(len(g.alternatives) for e in entries.values() for g in e.groups),
        "span_occurrences_verified": len(spans),
        "unique_spans_verified": len({(s.passage_id, s.start, s.end) for s in spans}),
        "validation": (
            "Existing validators verified references, source identity, offsets and exact quotes; "
            "semantic sufficiency is reviewed separately."
        ),
    }
    return dataset, entries, passages, identity


def archived_runs(identity):
    """Use only explicitly named development archives with saved first-four IDs."""
    archives = [
        ("retrieval-improvements", "docs/retrieval-improvement-results.json"),
        ("vulkan-reranking", "docs/vulkan-reranking-results.json"),
    ]
    for family, path in archives:
        data = json.loads((ROOT / path).read_bytes())
        contract = data.get("evaluation_contract", data.get("protocol"))
        assert contract["evidence_labels_sha256"] == identity["labels_canonical_hash"]
        dataset_hash = data.get("dataset_sha256", data.get("protocol", {}).get("dataset_sha256"))
        assert dataset_hash in (identity["dataset_digest"], identity["dataset_canonical_hash"])
        runs = data["runs"]
        for name, run in runs.items() if isinstance(runs, dict) else ((r["name"], r) for r in runs):
            assert run["corpus"]["source_sha256"] == identity["corpus_sha256"]
            assert run["corpus"]["shared_passage_sha256"] == identity["shared_passage_sha256"]
            yield family, name, run, path


def apply_changes(entries, changes, cases, by_id):
    revised = {cid: e.model_dump(mode="json") for cid, e in entries.items()}
    # Validate proposed alternatives before a scope proposal removes their group.
    # The independent scenarios still show each proposal's effect on that group.
    for change in sorted(changes, key=lambda c: c["action"] == "remove_group"):
        cid = change["case_id"]
        groups = revised[cid]["groups"]
        group = next(g for g in groups if g["id"] == change["group_id"])
        if change["action"] == "remove_group":
            groups.remove(group)
        elif change["action"] == "add_alternative":
            spans = [EvidenceSpan.model_validate(s) for s in change["spans"]]
            for span in spans:
                passage = by_id[span.passage_id]
                assert passage.document_id in cases[cid].expected_source_ids
                assert passage.text[span.start : span.end] == span.quote
                assert span.end <= len(passage.text)
            group["alternatives"].append([s.model_dump(mode="json") for s in spans])
        else:
            raise ValueError("Unsupported proposed change action")
    return {cid: CaseEvidence.model_validate(e) for cid, e in revised.items()}


def summarize_rows(dataset, rows):
    result = cutoff_summary({"dataset": dataset.model_dump(mode="json"), "results": rows}, 4)
    positives = [
        r["metrics_at_k"]["4"] for r in rows if r["metrics_at_k"]["4"]["source_recall"] is not None
    ]
    result["any_evidence_hit_cases"] = sum(m["first_relevant_rank"] is not None for m in positives)
    result["any_evidence_hit_rate"] = result["any_evidence_hit_cases"] / len(positives)
    result["negative_cases_unscored"] = len(rows) - len(positives)
    return result


def score_rows(archived, dataset, entries, by_id):
    cases = {c.id: c for c in dataset.cases}
    assert len(archived) == 50 and {r["case_id"] for r in archived} == set(cases)
    result = []
    for row in archived:
        cid = row["case_id"]
        ids = row.get("passage_ids", row.get("first_four_passage_ids"))
        assert len(ids) <= 4 and len(set(ids)) == len(ids)
        hits = [by_id[pid] for pid in ids]
        error = row.get("error")
        scored_hits = [] if error and error["stage"] == "retrieval" else hits
        metrics = ranking_metrics(cases[cid], scored_hits, entries.get(cid))
        prepared = prepare_answer_context([SearchHit(**p.model_dump(), score=0) for p in hits])
        context = evidence_coverage(
            entries.get(cid),
            {
                pid: [TextRange(start=0, end=length)]
                for pid, length in prepared.diagnostics.visible_chars.items()
                if length
            },
        )
        result.append(
            {
                "case_id": cid,
                "retrieved_passage_ids": ids,
                "error": error,
                "metrics_at_k": {"4": metrics},
                "context_complete_evidence": context["complete_evidence"],
                "context_truncation_loses_evidence": metrics["complete_evidence"] is True
                and context["complete_evidence"] is not True,
            }
        )
    return result


def verify_raw(run_root, family, name, archive, dataset, entries, by_id):
    relative = {
        "retrieval-improvements": "retrieval-improvements-2026-10-02",
        "vulkan-reranking": "vulkan-rerankers-cache-off-2026-10-02",
    }[family] + f"/{name}/run.json"
    path = run_root / relative
    expected_hash = archive.get("raw_run_sha256", archive.get("run_sha256"))
    if not path.exists() and family == "vulkan-reranking":
        for directory in ("vulkan-rerankers-resume-2026-10-02", "vulkan-rerankers-2026-10-02"):
            candidate = run_root / directory / name / "run.json"
            if (
                candidate.exists()
                and canonical_hash(json.loads(candidate.read_bytes())) == expected_hash
            ):
                path = candidate
                relative = path.relative_to(run_root).as_posix()
                break
    run = json.loads(path.read_bytes())
    assert run["dataset"]["split"] == "development"
    actual_hash = file_hash(path) if family == "retrieval-improvements" else canonical_hash(run)
    assert actual_hash == expected_hash, f"Archived run hash mismatch: {relative}"
    assert Dataset.model_validate(run["dataset"]) == dataset
    cases = {c.id: c for c in dataset.cases}
    assert len(run["results"]) == 50 and {r["case_id"] for r in run["results"]} == set(cases)
    checked = 0
    for row in run["results"]:
        cid = row["case_id"]
        hits = [by_id[pid] for pid in row["retrieved_passage_ids"]]
        assert [Passage.model_validate(p) for p in row["retrieved_passages"]] == hits
        if row["error"] and row["error"]["stage"] == "retrieval":
            hits = []
        for k, metrics in row["metrics_at_k"].items():
            assert_equal(
                ranking_metrics(cases[cid], hits[: int(k)], entries.get(cid)),
                metrics,
                f"{relative}/{cid}@{k}",
            )
            checked += 1
    return {
        "path_relative_to_runs": relative,
        "file_sha256": file_hash(path),
        "archived_sha256": expected_hash,
        "archived_hash_method": "file-bytes"
        if family == "retrieval-improvements"
        else "canonical-json",
        "case_cutoffs_verified": checked,
    }


def pool_diagnostics(entries, revisions, cases, identity):
    path = ROOT / "docs/selection-diagnostics-results.json"
    archive = json.loads(path.read_bytes())["oracles"]
    assert archive["manifest"]["dataset_sha256"] == identity["dataset_canonical_hash"]
    assert archive["manifest"]["labels_sha256"] == identity["labels_canonical_hash"]
    assert {r["case_id"] for r in archive["cases"]} == set(entries)
    summaries = {}
    for scenario, labels in {"original": entries, **revisions}.items():
        pools = {}
        for row in archive["cases"]:
            cid = row["case_id"]
            supports = minimal_supports(labels[cid])
            for name, pool in row["pools"].items():
                possible = any(len(s) <= 4 and s <= set(pool["ids"]) for s in supports)
                if scenario == "original":
                    assert possible == pool["complete"]
                state = pools.setdefault(
                    name,
                    {
                        "complete_cases": [],
                        "incomplete_cases": [],
                        "reference_recall_ceiling_sum": 0.0,
                    },
                )
                state["complete_cases" if possible else "incomplete_cases"].append(cid)
                refs = {r.passage_id for r in cases[cid].references}
                state["reference_recall_ceiling_sum"] += min(4, len(refs & set(pool["ids"]))) / len(
                    refs
                )
        for state in pools.values():
            state["complete_count"] = len(state["complete_cases"])
            state["reference_recall_ceiling_at4"] = state.pop("reference_recall_ceiling_sum") / len(
                entries
            )
        summaries[scenario] = pools
    return {
        "archive_sha256": file_hash(path),
        "label_assisted_oracle_not_retrieval_quality": True,
        "scenarios": summaries,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument(
        "--raw-runs-root",
        type=Path,
        help="Optional read-only verification of original saved development runs",
    )
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new review artifact")
    dataset, entries, passages, identity = load_inputs()
    by_id = {p.id: p for p in passages}
    cases = {c.id: c for c in dataset.cases}
    scenarios = {}
    overlay = None
    if args.overlay:
        overlay = json.loads(args.overlay.read_bytes())
        assert overlay["schema_version"] == 1 and overlay["review_status"] == "unreviewed"
        changes = overlay["changes"]
        assert len({c["id"] for c in changes}) == len(changes)
        scenarios.update({f"individual:{c['id']}": [c] for c in changes})
        for category in sorted({c["category"] for c in changes}):
            scenarios[f"{category}-only"] = [c for c in changes if c["category"] == category]
        for decision_kind in sorted({c["decision_kind"] for c in changes if "decision_kind" in c}):
            scenarios[f"decision-kind:{decision_kind}"] = [
                c for c in changes if c.get("decision_kind") == decision_kind
            ]
        scenarios["combined"] = changes
    revisions = {
        name: apply_changes(entries, changes, cases, by_id) for name, changes in scenarios.items()
    }
    positives = [c for c in dataset.cases if not c.expected_abstention]
    reference_limits = [
        {
            "case_id": c.id,
            "reference_ids": len({r.passage_id for r in c.references}),
            "four_slot_ceiling": min(4, len({r.passage_id for r in c.references}))
            / len({r.passage_id for r in c.references}),
        }
        for c in positives
    ]
    result = {
        "schema_version": 1,
        "audit_status": "AI-assisted, unreviewed sensitivity analysis",
        "scope": (
            "Development-only cached ranking replay, no retrieval inference or answer generation"
        ),
        "inputs": identity,
        "existing_scorer_sha256": {
            name: file_hash(ROOT / "backend/researchlens" / name)
            for name in (
                "evaluation.py",
                "evaluation_evidence.py",
                "evaluation_metrics.py",
                "retrieval_analysis.py",
            )
        },
        "original_contract": {
            "metrics_version": 2,
            "primary_k": 4,
            "evidence_labels_sha256": identity["labels_canonical_hash"],
        },
        "proposed_contract": None
        if overlay is None
        else {
            "status": "unreviewed",
            "overlay_sha256": file_hash(args.overlay),
            "scenarios": {name: [c["id"] for c in changes] for name, changes in scenarios.items()},
            "not_a_replacement_for_historical_results": True,
        },
        "corpus_reference_recall_ceiling_at4": sum(r["four_slot_ceiling"] for r in reference_limits)
        / len(positives),
        "reference_ceiling_cases_below_one": [
            r for r in reference_limits if r["four_slot_ceiling"] < 1
        ],
        "minimum_approved_passage_count_distribution": dict(
            sorted(Counter(min(map(len, minimal_supports(e))) for e in entries.values()).items())
        ),
        "candidate_pool_diagnostics": pool_diagnostics(entries, revisions, cases, identity),
        "runs": [],
    }
    for family, name, archive, path in archived_runs(identity):
        original = score_rows(archive["cases"], dataset, entries, by_id)
        for old, replayed in zip(archive["cases"], original, strict=True):
            stored = old.get("metrics_at4", old.get("metrics_at_k", {}).get("4"))
            assert_equal(replayed["metrics_at_k"]["4"], stored, f"{family}/{name}/{old['case_id']}")
        summary = summarize_rows(dataset, original)
        if "cutoffs" in archive:
            assert_equal(summary, archive["cutoffs"]["4"], f"{family}/{name}/summary")
        else:
            assert summary["complete_evidence_cases"] == archive["complete_count"]
            for field, saved in (
                ("mrr", "primary_k4_mrr"),
                ("mean_group_coverage", "primary_k4_group_coverage"),
                ("complete_evidence_rate", "primary_k4_complete_evidence_rate"),
            ):
                assert_equal(summary[field], archive["summary"][saved], f"{family}/{name}/{field}")
        item = {
            "family": family,
            "name": name,
            "archive": path,
            "archive_sha256": file_hash(ROOT / path),
            "saved_run_sha256": archive.get("raw_run_sha256", archive.get("run_sha256")),
            "saved_run_hash_method": "file-bytes"
            if family == "retrieval-improvements"
            else "canonical-json",
            "retrieval_limit_in_original_run": archive["retrieval"]["limit"],
            "historical_query_median_ms": archive["summary"]["query_median_ms"],
            "original_summary": summary,
            "original_case_metrics_and_rankings": original,
            "proposed_scenarios": {},
        }
        if args.raw_runs_root:
            item["raw_verification"] = verify_raw(
                args.raw_runs_root, family, name, archive, dataset, entries, by_id
            )
        for scenario, revised in revisions.items():
            after = score_rows(archive["cases"], dataset, revised, by_id)
            gains, losses, changed = [], [], []
            for before, proposed in zip(original, after, strict=True):
                bm, pm = (r["metrics_at_k"]["4"] for r in (before, proposed))
                if bm["complete_evidence"] is False and pm["complete_evidence"] is True:
                    gains.append(before["case_id"])
                if bm["complete_evidence"] is True and pm["complete_evidence"] is False:
                    losses.append(before["case_id"])
                if bm != pm:
                    changed.append(
                        {
                            "case_id": before["case_id"],
                            "before": bm,
                            "proposed": pm,
                            "proposed_context_complete_evidence": proposed[
                                "context_complete_evidence"
                            ],
                        }
                    )
            item["proposed_scenarios"][scenario] = {
                "summary": summarize_rows(dataset, after),
                "gains": gains,
                "losses": losses,
                "remaining_incomplete": [
                    r["case_id"]
                    for r in after
                    if r["metrics_at_k"]["4"]["complete_evidence"] is False
                ],
                "changed_cases": changed,
            }
        result["runs"].append(item)
    incumbent = next(r for r in result["runs"] if r["name"] == "bge-m3-bge-rerank20")
    proposed = {
        row["case_id"]: row["proposed"]
        for row in incumbent["proposed_scenarios"].get("combined", {}).get("changed_cases", [])
    }
    original_pool_complete = set(
        result["candidate_pool_diagnostics"]["scenarios"]["original"]["bge20"]["complete_cases"]
    )
    result["incumbent_original_failures"] = []
    for row in incumbent["original_case_metrics_and_rankings"]:
        cid, original_metrics = row["case_id"], row["metrics_at_k"]["4"]
        if original_metrics["complete_evidence"] is not False:
            continue
        proposed_metrics = proposed.get(cid, original_metrics)
        result["incumbent_original_failures"].append(
            {
                "case_id": cid,
                "retrieved_passage_ids": row["retrieved_passage_ids"],
                "original_uncovered_group_ids": [
                    g["group_id"] for g in original_metrics["groups"] if g["covered"] is False
                ],
                "original_bge20_diagnosis": "selection-failure"
                if cid in original_pool_complete
                else "candidate-pool-failure",
                "proposed_combined_complete": proposed_metrics["complete_evidence"]
                if overlay is not None
                else None,
                "proposed_remaining_uncovered_group_ids": [
                    g["group_id"] for g in proposed_metrics["groups"] if g["covered"] is False
                ]
                if overlay is not None
                else None,
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                "runs_replayed": len(result["runs"]),
                "case_rankings_replayed": sum(
                    len(r["original_case_metrics_and_rankings"]) for r in result["runs"]
                ),
                "span_occurrences_verified": identity["span_occurrences_verified"],
                "original_summary_mismatches": 0,
                "proposed_scenarios": len(scenarios),
            }
        )
    )


if __name__ == "__main__":
    main()
