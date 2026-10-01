import json
import subprocess
from unittest.mock import Mock

import pytest
from researchlens.compare_retrieval import compare
from researchlens.ingest import ROOT, TECHNICAL_CORPUS

DATASET = ROOT / "evaluation/datasets/technical-development.json"
OTHER = ROOT / "evaluation/datasets/held-out.json"
LABELS = ROOT / "evaluation/labels/technical-development.json"


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


def test_comparison_uses_same_evidence_and_cutoffs_for_every_mode(tmp_path, monkeypatch):
    process = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr("researchlens.compare_retrieval.subprocess.run", process)
    manifest = compare(
        tmp_path / "labeled",
        models=["minilm"],
        source=TECHNICAL_CORPUS,
        dataset=DATASET,
        other_split=OTHER,
        evidence_labels=LABELS,
        limit=10,
        cutoffs=[10, 4, 1, 4],
    )
    calls = [call.args[0] for call in process.call_args_list]
    for call in (calls[1], calls[3], calls[4]):
        assert call[call.index("--evidence-labels") + 1] == str(LABELS.resolve())
        assert call[call.index("--cutoffs") + 1 :] == ["1", "4", "10"]
        assert call[call.index("--limit") + 1] == "10"
    assert "--paired-output" in calls[-1]
    assert manifest["cutoffs"] == [1, 4, 10]
    assert len(manifest["evidence_labels_sha256"]) == 64


def test_stale_labels_and_unavailable_cutoffs_fail_before_ingestion(tmp_path, monkeypatch):
    process = Mock()
    monkeypatch.setattr("researchlens.compare_retrieval.subprocess.run", process)
    labels = json.loads(LABELS.read_bytes())
    labels["dataset_sha256"] = "0" * 64
    stale = tmp_path / "stale.json"
    stale.write_text(json.dumps(labels), encoding="utf-8")
    for options, message in (
        ({"evidence_labels": stale}, "do not match"),
        ({"cutoffs": [1, 4, 10]}, "cutoffs"),
        ({"repeats": 101}, "limits"),
    ):
        with pytest.raises(ValueError, match=message):
            compare(
                tmp_path / "invalid",
                models=["minilm"],
                source=TECHNICAL_CORPUS,
                dataset=DATASET,
                other_split=OTHER,
                **options,
            )
    process.assert_not_called()
    assert not (tmp_path / "invalid").exists()


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
