"""Cutoff summaries and paired changes; no model-quality inference for negatives."""

import math
from collections import Counter


def percentile_nearest_rank(samples: list[float], fraction: float) -> float | None:
    if not samples:
        return None
    return sorted(samples)[max(0, math.ceil(fraction * len(samples)) - 1)]


def cutoff_summary(run: dict, k: int) -> dict:
    cases = {c["id"]: c for c in run["dataset"]["cases"]}
    rows = [r for r in run["results"] if not cases[r["case_id"]]["expected_abstention"]]
    metrics = [r.get("metrics_at_k", {}).get(str(k)) for r in rows]
    if any(m is None for m in metrics):
        return {"answerable_cases": len(rows), "available": False}
    labeled = [m for m in metrics if m["group_coverage"] is not None]
    return {
        "answerable_cases": len(rows),
        "available": True,
        "mrr": sum(m["reciprocal_rank"] for m in metrics) / len(rows) if rows else None,
        "source_recall": sum(m["source_recall"] for m in metrics) / len(rows) if rows else None,
        "passage_recall": sum(m["passage_recall"] for m in metrics) / len(rows) if rows else None,
        "evidence_labeled_cases": len(labeled),
        "mean_group_coverage": sum(m["group_coverage"] for m in labeled) / len(labeled)
        if labeled
        else None,
        "complete_evidence_cases": sum(m["complete_evidence"] is True for m in labeled),
        "complete_evidence_rate": sum(m["complete_evidence"] is True for m in labeled)
        / len(labeled)
        if labeled
        else None,
    }


def paired_changes(baseline: dict, candidate: dict, k: int = 4) -> list[dict]:
    """Caller first checks controlled-comparison identities, including evidence labels."""
    original = {r["case_id"]: r for r in baseline["results"]}
    changed = {r["case_id"]: r for r in candidate["results"]}
    if len(original) != len(baseline["results"]) or original.keys() != changed.keys():
        raise ValueError("Paired comparison requires exactly the same case IDs")
    if len(changed) != len(candidate["results"]):
        raise ValueError("Paired comparison case IDs must be unique")
    result = []
    for cid, before in original.items():
        after = changed[cid]
        first, second = (r.get("metrics_at_k", {}).get(str(k)) for r in (before, after))
        deltas = {}
        if first is not None and second is not None:
            for field in ("group_coverage", "reciprocal_rank", "source_recall"):
                if first[field] is not None and second[field] is not None:
                    deltas[field] = second[field] - first[field]
        if after["error"] or before["error"]:
            outcome = (
                "both-failed"
                if after["error"] and before["error"]
                else ("failed" if after["error"] else "recovered")
            )
        elif first is None or second is None:
            outcome = "unavailable"
        elif not deltas:
            outcome = "not-scored"
        else:
            higher = any(d > 1e-12 for d in deltas.values())
            lower = any(d < -1e-12 for d in deltas.values())
            outcome = (
                "mixed"
                if higher and lower
                else ("improved" if higher else "worsened" if lower else "unchanged")
            )
        result.append(
            {
                "case_id": cid,
                "k": k,
                "outcome": outcome,
                "deltas": deltas,
                "baseline_error": before["error"],
                "candidate_error": after["error"],
                "baseline_passage_ids": before["retrieved_passage_ids"][:k],
                "candidate_passage_ids": after["retrieved_passage_ids"][:k],
                "baseline_metrics": first,
                "candidate_metrics": second,
            }
        )
    return result


def comparison_details(runs: list[dict]) -> list[str]:
    if not any("evaluation_contract" in run for run in runs):
        return []
    lines = [
        "",
        "## Ranking and evidence by cutoff",
        "",
        "k=4 is the primary application measure. Other cutoffs are ranking diagnostics. "
        "These are prefixes of the recorded ranking, not separate queries at each k. "
        "Query latency measures the configured retrieval limit. "
        "Missing cutoffs remain unavailable.",
        "",
        "| Run | k | MRR | Source recall | Passage recall | Labeled cases | "
        "Group coverage | Complete evidence |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for run in runs:
        for k in (1, 4, 10):
            summary = cutoff_summary(run, k)
            if not summary["available"]:
                lines.append(f"| {run['run_id']} | {k} | unavailable | | | | | |")
                continue
            values = [
                summary[key]
                for key in (
                    "mrr",
                    "source_recall",
                    "passage_recall",
                    "evidence_labeled_cases",
                    "mean_group_coverage",
                    "complete_evidence_rate",
                )
            ]
            lines.append(f"| {run['run_id']} | {k} | " + " | ".join(map(str, values)) + " |")
    for candidate in runs[1:]:
        lines.extend(
            [
                "",
                f"## Paired changes against {runs[0]['run_id']}",
                "",
                f"Candidate: {candidate['run_id']}. Positive deltas favor the candidate. "
                "Mixed changes retain ranking/coverage regressions; negatives are not scored.",
            ]
        )
        for k in (1, 4, 10):
            changes = paired_changes(runs[0], candidate, k)
            lines.extend(
                [
                    "",
                    f"k={k} outcomes: {dict(Counter(c['outcome'] for c in changes))}",
                    "",
                    "| Case | Outcome | Group coverage delta | Reciprocal rank delta | "
                    "Source recall delta | Errors |",
                    "| --- | --- | --- | --- | --- | --- |",
                ]
            )
            for change in changes:
                delta = change["deltas"]
                errors = (change["baseline_error"], change["candidate_error"])
                lines.append(
                    f"| {change['case_id']} | {change['outcome']} | "
                    f"{delta.get('group_coverage')} | {delta.get('reciprocal_rank')} | "
                    f"{delta.get('source_recall')} | {errors} |"
                )
    return lines
