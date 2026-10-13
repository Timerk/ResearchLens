"""Offline scoring of the exact provider serialization, without answer generation."""

from statistics import mean, median

from researchlens.answers import INSTRUCTIONS, prepare_answer_context, serialize_answer_input
from researchlens.evaluation_evidence import CaseEvidence, TextRange, evidence_coverage
from researchlens.evaluation_metrics import binomial_ci, exact_mcnemar
from researchlens.models import SearchHit

STANDARD_BUDGETS = [4, 8000, 12000, 16000]
TOKEN_SCOPE = (
    "o200k_base estimate of instructions plus exact question/passages JSON; "
    "excludes Responses framing, output schema and provider-internal tokens; not billed usage"
)


def context_profile(question: str, hits: list[SearchHit], entry: CaseEvidence | None, budget: int):
    if budget not in STANDARD_BUDGETS:
        raise ValueError("Use four passages or 8000/12000/16000 serialized characters")
    prepared = prepare_answer_context(
        hits,
        mode="passages" if budget == 4 else "characters",
        max_context_chars=16000 if budget == 4 else budget,
    )
    visible = {
        pid: [TextRange(start=0, end=n)]
        for pid, n in prepared.diagnostics.visible_chars.items()
        if n
    }
    import tiktoken

    tokenizer = tiktoken.get_encoding("o200k_base")
    payload = serialize_answer_input(question, prepared.items)
    return {
        "context": prepared.diagnostics.model_dump(),
        "all_groups": evidence_coverage(entry, visible),
        "asked_groups": evidence_coverage(entry, visible, asked_only=True),
        "input_tokens_estimate": len(tokenizer.encode(INSTRUCTIONS, disallowed_special=()))
        + len(tokenizer.encode(payload, disallowed_special=())),
        "token_count_scope": TOKEN_SCOPE,
    }


def context_summary(run: dict, budget: int, view: str = "all_groups") -> dict:
    cases = {c["id"]: c for c in run["dataset"]["cases"]}
    all_rows = run["results"]
    rows = [r for r in all_rows if not cases[r["case_id"]]["expected_abstention"]]
    profiles = [r.get("context_profiles", {}).get(str(budget)) for r in rows]
    if any(p is None for p in profiles):
        return {"available": False}

    def coverage(selected):
        metrics = [p[view] for p in selected if p[view]["complete_evidence"] is not None]
        successes = sum(m["complete_evidence"] is True for m in metrics)
        return {
            "labeled_cases": len(metrics),
            "complete_evidence_cases": successes,
            "complete_evidence_rate": successes / len(metrics) if metrics else None,
            "complete_evidence_ci95": binomial_ci(successes, len(metrics)),
            "mean_group_coverage": mean(m["group_coverage"] for m in metrics) if metrics else None,
        }

    cohorts = sorted({cases[r["case_id"]].get("query_style") or "unspecified" for r in all_rows})
    tokens = [p["input_tokens_estimate"] for p in profiles]
    return {
        "available": True,
        "total_cases": len(all_rows),
        "unscored_abstention_cases": len(all_rows) - len(rows),
        **coverage(profiles),
        "cohorts": {
            cohort: {
                "case_count": sum(
                    (cases[r["case_id"]].get("query_style") or "unspecified") == cohort
                    for r in all_rows
                ),
                **coverage(
                    [
                        p
                        for r, p in zip(rows, profiles, strict=True)
                        if (cases[r["case_id"]].get("query_style") or "unspecified") == cohort
                    ]
                ),
            }
            for cohort in cohorts
        },
        "input_tokens_estimate": {
            "mean": mean(tokens) if tokens else None,
            "median": median(tokens) if tokens else None,
            "min": min(tokens) if tokens else None,
            "max": max(tokens) if tokens else None,
            "scope": TOKEN_SCOPE,
            "population": "answerable development questions",
        },
        "mean_passages": mean(len(p["context"]["passage_ids"]) for p in profiles)
        if profiles
        else None,
        "mean_serialized_chars": mean(p["context"]["serialized_chars"] for p in profiles)
        if profiles
        else None,
    }


def context_paired(
    baseline: dict, candidate: dict, before_budget: int, after_budget: int, view="all_groups"
):
    def states(run, budget):
        return {
            r["case_id"]: r.get("context_profiles", {})
            .get(str(budget), {})
            .get(view, {})
            .get("complete_evidence")
            for r in run["results"]
        }

    return exact_mcnemar(states(baseline, before_budget), states(candidate, after_budget))


def context_report_details(runs: list[dict]) -> list[str]:
    if not any(r.get("context_budgets") for r in runs):
        return []
    lines = [
        "",
        "## Serialized provider context",
        "",
        TOKEN_SCOPE,
        "",
        "| Run | Budget | View | Complete | 95% binomial CI | Group coverage | Mean input tokens |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for run in runs:
        for budget in run.get("context_budgets", []):
            for view in ("all_groups", "asked_groups"):
                s = context_summary(run, budget, view)
                if s["available"]:
                    lines.append(
                        f"| {run['run_id']} | {budget} | {view} | "
                        f"{s['complete_evidence_cases']}/{s['labeled_cases']} | "
                        f"{s['complete_evidence_ci95']} | {s['mean_group_coverage']} | "
                        f"{s['input_tokens_estimate']['mean']} |"
                    )
            cohorts = context_summary(run, budget)["cohorts"]
            lines.append(f"\nCohorts for {run['run_id']} / {budget}: {cohorts}\n")
            if budget != 4:
                for view in ("all_groups", "asked_groups"):
                    lines.append(
                        f"Paired 4 to {budget}, {view}: {context_paired(run, run, 4, budget, view)}"
                    )
    for candidate in runs[1:]:
        for budget in candidate.get("context_budgets", []):
            if budget not in (runs[0].get("context_budgets") or []):
                continue
            for view in ("all_groups", "asked_groups"):
                lines.append(
                    f"Paired {runs[0]['run_id']} to {candidate['run_id']}, {budget}, {view}: "
                    f"{context_paired(runs[0], candidate, budget, budget, view)}"
                )
    return lines
