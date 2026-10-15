import json
import os
import stat
import sys
from types import SimpleNamespace

import pytest
from researchlens import artifacts
from researchlens.answer_evaluation import CostGuard, execute, save
from researchlens.answer_study_budget import StudyBudget
from researchlens.artifacts import canonical_hash


def test_save_preserves_write_text_bytes(tmp_path):
    value = {"text": "Grüße", "nested": [1, None]}
    expected = tmp_path / "expected.json"
    expected.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
    path = tmp_path / "state.json"
    save(path, value)
    assert path.read_bytes() == expected.read_bytes()


def test_save_serialization_failure_keeps_previous_file(tmp_path):
    path = tmp_path / "state.json"
    save(path, {"previous": True})
    previous = path.read_bytes()
    with pytest.raises(ValueError, match="JSON compliant"):
        save(path, {"invalid": float("nan")})
    assert path.read_bytes() == previous
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("operation", ["fsync", "replace"])
@pytest.mark.parametrize("error", [OSError, KeyboardInterrupt])
def test_save_failure_keeps_previous_file_and_cleans_temporary(
    tmp_path, monkeypatch, operation, error
):
    path = tmp_path / "state.json"
    save(path, {"previous": True})
    previous = path.read_bytes()

    def fail(*args):
        raise error("interrupted write")

    monkeypatch.setattr(artifacts.os, operation, fail)
    with pytest.raises(error, match="interrupted write"):
        save(path, {"replacement": True})
    assert path.read_bytes() == previous
    assert list(tmp_path.iterdir()) == [path]


def test_save_syncs_same_directory_temporary_before_replace(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    events = []
    original_fsync, original_replace = os.fsync, os.replace

    def sync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            assert events == ["sync", "replace"]
            assert os.fstat(fd) == os.stat(tmp_path)
            events.append("directory sync")
            original_fsync(fd)
            return
        events.append("sync")
        # Reading the file sees the text only after the buffered handle is flushed.
        temporary = next(tmp_path.iterdir())
        assert json.loads(temporary.read_bytes()) == {"new": True}
        original_fsync(fd)

    def replace(source, destination):
        assert source.parent == path.parent
        assert destination == path
        assert events == ["sync"]
        original_replace(source, destination)
        events.append("replace")

    monkeypatch.setattr(artifacts.os, "fsync", sync)
    monkeypatch.setattr(artifacts.os, "replace", replace)
    save(path, {"new": True})
    expected = ["sync", "replace"]
    if os.name != "nt":
        expected.append("directory sync")
    assert events == expected
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.skipif(os.name == "nt", reason="POSIX file permissions")
def test_atomic_write_new_file_uses_umask_default_mode(tmp_path, monkeypatch):
    expected = tmp_path / "expected.txt"
    expected.write_text("reference", encoding="utf-8")

    def unexpected_umask(*args):
        pytest.fail("atomic writes must not read or change the process-wide umask")

    monkeypatch.setattr(artifacts.os, "umask", unexpected_umask)
    path = tmp_path / "new.txt"
    artifacts.atomic_write_text(path, "new")
    assert stat.S_IMODE(path.stat().st_mode) == stat.S_IMODE(expected.stat().st_mode)


@pytest.mark.skipif(os.name == "nt", reason="POSIX file permissions")
def test_atomic_write_preserves_existing_mode(tmp_path):
    path = tmp_path / "existing.txt"
    path.write_text("old", encoding="utf-8")
    path.chmod(0o640)
    artifacts.atomic_write_text(path, "new")
    assert path.read_text(encoding="utf-8") == "new"
    assert stat.S_IMODE(path.stat().st_mode) == 0o640


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory fsync")
def test_atomic_write_directory_sync_failure_closes_descriptor(tmp_path, monkeypatch):
    original_fsync = os.fsync
    directories = []

    def sync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            directories.append(fd)
            raise OSError("directory sync failed")
        original_fsync(fd)

    monkeypatch.setattr(artifacts.os, "fsync", sync)
    path = tmp_path / "state.txt"
    with pytest.raises(OSError, match="directory sync failed"):
        artifacts.atomic_write_text(path, "published")
    assert path.read_text(encoding="utf-8") == "published"
    assert list(tmp_path.iterdir()) == [path]
    assert len(directories) == 1
    with pytest.raises(OSError):
        os.fstat(directories[0])


def test_cost_guard_journal_is_accepted_by_resume(tmp_path, monkeypatch):
    from researchlens import answer_evaluation as module

    plan = {"total_reserved_usd": 0.1, "configurations": []}
    save(tmp_path / "plan.json", plan)
    guard = CostGuard(1)
    guard.journal = tmp_path / "cost-ledger.json"
    guard.reserve(0.02)
    guard.reserve(0.03)
    previous = guard.journal.read_bytes()
    monkeypatch.setattr(module.Settings, "from_env", lambda _: SimpleNamespace(api_key="offline"))
    monkeypatch.setattr(module, "OpenAI", lambda **_: SimpleNamespace(close=lambda: None))
    args = SimpleNamespace(
        output=tmp_path,
        approve_plan_sha256=canonical_hash(plan),
        max_cost_usd=1,
        resume=True,
        env_file=tmp_path / "unused.env",
    )
    execute(args, SimpleNamespace(cases=[]), {}, [], plan, None)
    assert guard.journal.read_bytes() == previous
    assert json.loads(previous) == {"reserved_usd": 0.05, "max_cost_usd": 1}


def test_study_budget_failure_preserves_ledger_and_lf_bytes(tmp_path, monkeypatch):
    prices = SimpleNamespace(model_dump=lambda: {"model": "offline"})
    path = tmp_path / "study.json"
    budget = StudyBudget(path, 1, prices)
    budget.reserve("first", 0.1)
    previous = path.read_bytes()
    assert b"\r" not in previous

    def fail(*args):
        raise OSError("replace failed")

    monkeypatch.setattr(artifacts.os, "replace", fail)
    with pytest.raises(OSError, match="replace failed"):
        budget.reserve("second", 0.1)
    assert path.read_bytes() == previous
    assert list(tmp_path.iterdir()) == [path]
    assert StudyBudget(path, 1, prices).read()["calls"][0]["id"] == "first"


def test_freeze_publishes_complete_lf_contract_and_refuses_overwrite(tmp_path, monkeypatch):
    from researchlens_eval import answer_judge_freeze as freeze

    path = tmp_path / "frozen.json"
    monkeypatch.setattr(freeze, "FREEZE", path)
    monkeypatch.setattr(sys, "argv", ["freeze", "--revision", "test-revision"])
    freeze.main()
    saved = path.read_bytes()
    assert b"\r" not in saved
    assert json.loads(saved)["contract"] == freeze.current_contract()
    with pytest.raises(ValueError, match="Never overwrite"):
        freeze.main()
    assert path.read_bytes() == saved


def test_freeze_failed_replace_leaves_no_partial_contract(tmp_path, monkeypatch):
    from researchlens_eval import answer_judge_freeze as freeze

    path = tmp_path / "frozen.json"
    monkeypatch.setattr(freeze, "FREEZE", path)
    monkeypatch.setattr(sys, "argv", ["freeze", "--revision", "test-revision"])

    def fail(*args):
        raise OSError("replace failed")

    monkeypatch.setattr(artifacts.os, "replace", fail)
    with pytest.raises(OSError, match="replace failed"):
        freeze.main()
    assert not path.exists()
    assert list(tmp_path.iterdir()) == []
