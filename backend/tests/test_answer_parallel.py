import json
from types import SimpleNamespace

import pytest
from researchlens.answer_parallel import merged_results
from researchlens.artifacts import canonical_hash


def test_worker_merge_rejects_duplicate_missing_and_failed_cases():
    def part(cid, error=None):
        return {
            "execution": {},
            "results": [{"case_id": cid, "error": error, "answer_quality": {}}],
        }

    parts = [part("b"), part("a")]
    merged = merged_results(parts, ["a", "b"])
    assert [row["case_id"] for row in merged["results"]] == ["a", "b"]
    assert parts[0]["execution"] == {}
    with pytest.raises(ValueError, match="exactly once"):
        merged_results([part("a"), part("a")], ["a", "b"])
    with pytest.raises(ValueError, match="exactly once"):
        merged_results([part("a")], ["a", "b"])
    with pytest.raises(ValueError, match="incomplete"):
        merged_results([part("a", "failed"), part("b")], ["a", "b"])


@pytest.mark.parametrize("changed", ["plan", "cap", "jobs", "serial", "ledger", "cases"])
def test_parallel_resume_rejects_changes_before_writes_or_workers(tmp_path, monkeypatch, changed):
    from researchlens import answer_evaluation as module

    execute = module.execute
    plan = {"total_reserved_usd": 0.1}
    dataset = SimpleNamespace(cases=[SimpleNamespace(id=str(i)) for i in range(4)])
    args = SimpleNamespace(
        approve_plan_sha256=canonical_hash(plan),
        max_cost_usd=3,
        output=tmp_path / "answers",
        study_ledger=tmp_path / "study.json",
        jobs=2,
        resume=False,
    )

    def interrupted_worker(*args):
        raise RuntimeError("interrupted")

    monkeypatch.setattr(module, "execute", interrupted_worker)
    with pytest.raises(RuntimeError, match="interrupted"):
        execute(args, dataset, None, None, plan, None)
    saved = {path.name: path.read_bytes() for path in args.output.iterdir()}
    assert set(saved) == {"plan.json", "parallel-execution.json"}
    args.resume = True
    if changed == "plan":
        plan = {**plan, "changed": True}
        args.approve_plan_sha256 = canonical_hash(plan)
    elif changed == "cap":
        args.max_cost_usd = 2
    elif changed == "jobs":
        args.jobs = 3
    elif changed == "serial":
        args.jobs = 1
    elif changed == "ledger":
        args.study_ledger = tmp_path / "other-study.json"
    else:
        dataset.cases.reverse()
    monkeypatch.setattr(module, "execute", lambda *args: pytest.fail("Worker started"))
    monkeypatch.setattr(module, "OpenAI", lambda **kwargs: pytest.fail("Paid client constructed"))
    with pytest.raises(ValueError, match="Resume"):
        execute(args, dataset, None, None, plan, None)
    assert {path.name: path.read_bytes() for path in args.output.iterdir()} == saved


def test_parallel_resume_requires_execution_record_before_workers(tmp_path, monkeypatch):
    from researchlens import answer_evaluation as module
    from researchlens.answer_parallel import execute_parallel

    plan = {"total_reserved_usd": 0.1}
    output = tmp_path / "answers"
    output.mkdir()
    original = json.dumps(plan).encode()
    (output / "plan.json").write_bytes(original)
    args = SimpleNamespace(
        output=output, study_ledger=tmp_path / "study.json", jobs=2, max_cost_usd=3, resume=True
    )
    dataset = SimpleNamespace(cases=[SimpleNamespace(id=str(i)) for i in range(4)])
    monkeypatch.setattr(module, "execute", lambda *args: pytest.fail("Worker started"))
    with pytest.raises(ValueError, match="original parallel execution record"):
        execute_parallel(args, dataset, None, None, plan, None, execute=module.execute)
    assert (output / "plan.json").read_bytes() == original


def test_legacy_parallel_output_cannot_resume_as_serial(tmp_path, monkeypatch):
    from researchlens import answer_evaluation as module

    output = tmp_path / "answers"
    (output / "workers").mkdir(parents=True)
    plan = {"total_reserved_usd": 0.1}
    original = json.dumps(plan).encode()
    (output / "plan.json").write_bytes(original)
    args = SimpleNamespace(
        output=output, approve_plan_sha256=canonical_hash(plan), max_cost_usd=3, resume=True, jobs=1
    )
    monkeypatch.setattr(module, "OpenAI", lambda **kwargs: pytest.fail("Paid client constructed"))
    with pytest.raises(ValueError, match="parallel worker layout"):
        module.execute(args, None, None, None, plan, None)
    assert (output / "plan.json").read_bytes() == original


def test_parallel_resume_preserves_disjoint_worker_assignments(tmp_path, monkeypatch):
    from researchlens import answer_evaluation as module
    from researchlens import answer_parallel
    from researchlens.answer_evaluation import save

    execute = module.execute
    plan = {"total_reserved_usd": 0.1, "configurations": [{"configuration": "tfidf4"}]}
    dataset = SimpleNamespace(cases=[SimpleNamespace(id=str(i)) for i in range(4)])
    args = SimpleNamespace(
        approve_plan_sha256=canonical_hash(plan),
        max_cost_usd=3,
        output=tmp_path / "answers",
        study_ledger=tmp_path / "study.json",
        jobs=2,
        resume=False,
    )
    assignments = []

    def checkpoint_worker(child, *unused):
        assignments.append((frozenset(child.case_ids), child.resume))
        child.output.mkdir(parents=True, exist_ok=child.resume)
        folder = child.output / "tfidf4"
        folder.mkdir(exist_ok=child.resume)
        save(
            folder / "run.json",
            {
                "execution": {},
                "results": [
                    {"case_id": cid, "error": None, "answer_quality": {}} for cid in child.case_ids
                ],
            },
        )
        save(child.output / "cost-ledger.json", {"reserved_usd": 0.01})

    monkeypatch.setattr(module, "execute", checkpoint_worker)
    monkeypatch.setattr(answer_parallel, "spot_check_template", lambda result: {})
    execute(args, dataset, None, None, plan, None)
    saved = (args.output / "parallel-execution.json").read_bytes()
    args.resume = True
    execute(args, dataset, None, None, plan, None)
    assert set(assignments) == {
        (frozenset({"0", "2"}), False),
        (frozenset({"1", "3"}), False),
        (frozenset({"0", "2"}), True),
        (frozenset({"1", "3"}), True),
    }
    assert (args.output / "parallel-execution.json").read_bytes() == saved
    result = json.loads((args.output / "tfidf4/run.json").read_bytes())
    assert [row["case_id"] for row in result["results"]] == ["0", "1", "2", "3"]
    assert result["execution"]["answer_workers"] == 2
