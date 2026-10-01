import json
import subprocess
from unittest.mock import Mock

import pytest
from researchlens.compare_retrieval import compare
from researchlens.ingest import ROOT, TECHNICAL_CORPUS

DATASET = ROOT / "evaluation/datasets/technical-development.json"
OTHER = ROOT / "evaluation/datasets/held-out.json"


def test_comparison_delegates_to_existing_runner_in_fresh_processes(tmp_path, monkeypatch):
    process = Mock(
        return_value=Mock(returncode=0, stdout=b"private child output", stderr=b"secret")
    )
    monkeypatch.setattr("researchlens.compare_retrieval.subprocess.run", process)
    output = tmp_path / "comparison"
    manifest = compare(
        output, models=["minilm"], source=TECHNICAL_CORPUS, dataset=DATASET, other_split=OTHER
    )
    calls = [call.args[0] for call in process.call_args_list]
    assert [call[2] for call in calls] == [
        "researchlens.ingest",
        "researchlens.evaluation",
        "researchlens.ingest",
        "researchlens.evaluation",
        "researchlens.evaluation",
        "researchlens.evaluation",
    ]
    assert "hybrid" in calls[4] and "embeddings" in calls[3]
    assert all("--measure-memory" in calls[i] for i in (1, 3, 4))
    assert manifest["api_calls"] == 0 and manifest["generation"] == "none"
    assert "secret" not in (output / "manifest.json").read_text()
    assert all(call.kwargs["timeout"] == 3600 for call in process.call_args_list)
    assert not any("--mode" in call for call in calls)
    with pytest.raises(FileExistsError):
        compare(
            output, models=["minilm"], source=TECHNICAL_CORPUS, dataset=DATASET, other_split=OTHER
        )
    assert process.call_count == 6


def test_failed_ingestion_is_recorded_and_not_retried(tmp_path, monkeypatch):
    process = Mock(side_effect=[subprocess.TimeoutExpired("local", 1), Mock(returncode=1)])
    monkeypatch.setattr("researchlens.compare_retrieval.subprocess.run", process)
    output = tmp_path / "failed"
    manifest = compare(
        output,
        models=["minilm"],
        source=TECHNICAL_CORPUS,
        dataset=DATASET,
        other_split=OTHER,
        stage_timeout=1,
    )
    assert process.call_count == 2
    assert [stage["status"] for stage in manifest["stages"]] == ["timeout", "process_failed"]
    assert json.loads((output / "manifest.json").read_text()) == manifest


def test_comparison_rejects_held_out_and_unknown_models_before_work(tmp_path, monkeypatch):
    process = Mock()
    monkeypatch.setattr("researchlens.compare_retrieval.subprocess.run", process)
    with pytest.raises(ValueError, match="development"):
        compare(
            tmp_path / "held-out",
            models=["minilm"],
            source=TECHNICAL_CORPUS,
            dataset=OTHER,
            other_split=DATASET,
        )
    with pytest.raises(ValueError, match="supported"):
        compare(
            tmp_path / "unknown",
            models=["remote-api"],
            source=TECHNICAL_CORPUS,
            dataset=DATASET,
            other_split=OTHER,
        )
    process.assert_not_called()
