"""Run disjoint development case groups through the guarded answer executor."""

import json
from concurrent.futures import ThreadPoolExecutor
from copy import copy
from pathlib import Path
from threading import Event

from researchlens.answer_evaluation import save, spot_check_template
from researchlens.artifacts import canonical_hash


def merged_results(parts, expected):
    rows = [row for part in parts for row in part["results"]]
    by_id = {row["case_id"]: row for row in rows}
    if len(rows) != len(by_id) or set(by_id) != set(expected):
        raise ValueError("Worker results must cover every development case exactly once")
    if any(row.get("error") or "answer_quality" not in row for row in rows):
        raise ValueError("Do not report incomplete worker results")
    result = parts[0].copy()
    result["execution"] = parts[0]["execution"].copy()
    result["results"] = [by_id[cid] for cid in expected]
    result["execution"]["answer_workers"] = len(parts)
    return result


def execute_parallel(args, dataset, entries, runs, plan, prices):
    from researchlens.answer_evaluation import execute

    if not args.study_ledger:
        raise ValueError("Parallel paid runs require a shared --study-ledger")
    resuming = getattr(args, "resume", False)
    if args.jobs > len(dataset.cases):
        raise ValueError("Workers cannot outnumber development cases")
    groups = [[case.id for case in dataset.cases][i :: args.jobs] for i in range(args.jobs)]
    execution = {
        "workers": args.jobs,
        "case_groups": groups,
        "max_cost_usd": args.max_cost_usd,
        "study_ledger": str(Path(args.study_ledger).resolve()),
    }
    execution_path = args.output / "parallel-execution.json"
    if resuming:
        if canonical_hash(json.loads((args.output / "plan.json").read_bytes())) != canonical_hash(
            plan
        ):
            raise ValueError("Resume requires the exact approved plan")
        if not execution_path.exists():
            raise ValueError("Resume requires the original parallel execution record")
        if json.loads(execution_path.read_bytes()) != execution:
            raise ValueError("Resume cannot change the cost cap, shared ledger or worker layout")
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        save(args.output / "plan.json", plan)
        save(execution_path, execution)
    stop = Event()

    def worker(index):
        child = copy(args)
        child.jobs = 1
        child.case_ids = set(groups[index])
        child.output = args.output / "workers" / str(index)
        child.resume = resuming and child.output.exists()
        child.stop_event = stop
        try:
            execute(child, dataset, entries, runs, plan, prices)
        except Exception:
            stop.set()
            raise

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(worker, range(args.jobs)))
    expected = [case.id for case in dataset.cases]
    for estimate in plan["configurations"]:
        name = estimate["configuration"]
        parts = [
            json.loads((args.output / "workers" / str(index) / name / "run.json").read_bytes())
            for index in range(args.jobs)
        ]
        result = merged_results(parts, expected)
        folder = args.output / name
        folder.mkdir(exist_ok=resuming)
        save(folder / "run.json", result)
        save(folder / "spot-check.json", spot_check_template(result))
    reserved = sum(
        json.loads((args.output / "workers" / str(index) / "cost-ledger.json").read_bytes())[
            "reserved_usd"
        ]
        for index in range(args.jobs)
    )
    save(
        args.output / "cost-ledger.json",
        {"reserved_usd": reserved, "max_cost_usd": args.max_cost_usd},
    )
