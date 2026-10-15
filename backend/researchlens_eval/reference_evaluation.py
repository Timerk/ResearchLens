"""Score archived retrieval using passage references, without issuing searches."""

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

from researchlens.answers import prepare_answer_context
from researchlens.evaluation_metrics import binomial_ci, exact_mcnemar
from researchlens.models import SearchHit

TARGETS = {
    "passage_recall_at_4": 0.8,
    "context_hit": 0.9,
    "complete_evidence": 0.8,
    "both_documents": 0.9,
    "mrr_at_4": 0.65,
}


def reference_scores(case: dict, row: dict, budget: int) -> dict:
    """All expected-abstention cases are unscored, including related references."""
    if case["expected_abstention"]:
        return {"case_id": case["id"], "scored": False}
    references = {r["passage_id"] for r in case["references"]}
    if not references:
        raise ValueError("Answerable cases need passage references")
    hits = [] if row["error"] else [SearchHit.model_validate(p) for p in row["retrieved_passages"]]
    prepared = prepare_answer_context(
        hits,
        mode="passages" if budget == 4 else "characters",
        max_context_chars=16000 if budget == 4 else budget,
    )
    context = [p for p in prepared.supplied if prepared.diagnostics.visible_chars[p.id] > 0]
    ranked_ids = [p.id for p in hits]
    context_ids = [p.id for p in context]

    def rr(ids):
        return next((1 / i for i, pid in enumerate(ids, 1) if pid in references), 0.0)

    sources = set(case["expected_source_ids"])
    return {
        "case_id": case["id"],
        "scored": True,
        "passage_recall_at_4": len(references & set(ranked_ids[:4])) / len(references),
        "mrr_at_4": rr(ranked_ids[:4]),
        "context_hit": bool(references & set(context_ids)),
        "complete_evidence": references <= set(context_ids),
        "both_documents": sources <= {p.document_id for p in context} if len(sources) > 1 else None,
        "context_passage_recall": len(references & set(context_ids)) / len(references),
        "context_mrr": rr(context_ids),
        "reference_count": len(references),
        "references_found_at_4": len(references & set(ranked_ids[:4])),
        "context": prepared.diagnostics.model_dump(),
    }


def summarize_references(run: dict, budget: int) -> tuple[dict, list[dict]]:
    cases = {c["id"]: c for c in run["dataset"]["cases"]}
    rows = run["results"]
    if len(rows) != len(cases) or {r["case_id"] for r in rows} != cases.keys():
        raise ValueError("Archive must contain each dataset case exactly once")
    records = [reference_scores(cases[r["case_id"]], r, budget) for r in rows]
    positives = [r for r in records if r["scored"]]
    metrics = {}
    for key in [*TARGETS, "context_passage_recall", "context_mrr"]:
        values = [r[key] for r in positives if r[key] is not None]
        n = len(values)
        estimate = mean(values) if n else None
        binary = key in ("context_hit", "complete_evidence", "both_documents")
        radius = math.sqrt(math.log(40) / (2 * n)) if n else None
        interval = (
            binomial_ci(sum(values), n)
            if binary
            else [max(0, estimate - radius), min(1, estimate + radius)]
            if n
            else None
        )
        metrics[key] = {
            "estimate": estimate,
            "denominator": n,
            "successes": sum(values) if binary else None,
            "ci95": interval,
            "interval_method": "Clopper-Pearson" if binary else "Hoeffding bounded mean",
            "target": TARGETS.get(key),
            "pass": estimate >= TARGETS[key] if key in TARGETS and n else None,
        }
    total_refs = sum(r["reference_count"] for r in positives)
    found = sum(r["references_found_at_4"] for r in positives)
    return {
        "budget": budget,
        "total_cases": len(records),
        "answerable_cases": len(positives),
        "excluded_abstention_cases": len(records) - len(positives),
        "technical_errors": sum(bool(r["error"]) for r in rows),
        "metrics": metrics,
        "micro_recall_at_4": {
            "successes": found,
            "denominator": total_refs,
            "estimate": found / total_refs if total_refs else None,
            "ci95": binomial_ci(found, total_refs),
            "caveat": "Dependent references within cases; diagnostic only, not macro target",
        },
    }, records


def compare_references(profiles: list[tuple[str, dict, list[dict]]]) -> list[dict]:
    comparisons = []
    baseline = profiles[0][2]
    for name, _, records in profiles[1:]:
        for metric in ("complete_evidence", "context_hit", "both_documents"):

            def states(rows, metric=metric):
                return {r["case_id"]: r.get(metric) for r in rows}

            comparisons.append(
                {
                    "candidate": name,
                    "baseline": profiles[0][0],
                    "metric": metric,
                    **exact_mcnemar(states(baseline), states(records)),
                }
            )
    running = 0.0
    for rank, row in enumerate(sorted(comparisons, key=lambda r: r["p_two_sided"])):
        running = max(running, min(1.0, (len(comparisons) - rank) * row["p_two_sided"]))
        row["p_holm"] = running
    return comparisons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile", action="append", nargs=3, required=True, metavar=("NAME", "RUN_JSON", "BUDGET")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    profiles, provenance = [], {}
    for name, path, budget in args.profile:
        raw = Path(path).read_bytes()
        run = json.loads(raw)
        summary, records = summarize_references(run, int(budget))
        profiles.append((name, summary, records))
        provenance[name] = {
            "path": path,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "run_id": run["run_id"],
            "retrieval": run["retrieval"],
            "code": run.get("code"),
        }
    # Paired inference requires identical frozen datasets, not merely matching IDs.
    datasets = [json.loads(Path(p[1]).read_bytes())["dataset"] for p in args.profile]
    if any(d != datasets[0] for d in datasets[1:]):
        parser.error("Profiles must use identical datasets")
    result = {
        "schema_version": 1,
        "scoring": "passage-reference-presence",
        "source_sha256": hashlib.sha256(
            Path(__file__).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        "provenance": provenance,
        "profiles": {name: summary for name, summary, _ in profiles},
        "comparisons": compare_references(profiles),
        "case_scores": {name: records for name, _, records in profiles},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
