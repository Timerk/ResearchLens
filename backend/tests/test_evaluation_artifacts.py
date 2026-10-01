import hashlib
import json
import sys
from copy import deepcopy

import numpy as np
import pytest
from pydantic import ValidationError
from researchlens.artifacts import canonical_hash, load_artifact, validate_passage_artifact
from researchlens.evaluation import (
    comparison_report,
    default_retrieval_config,
    load_dataset,
    main,
    review_template,
    run_evaluation,
    summarize,
    validate_artifact,
    validate_splits,
)
from researchlens.evaluation_schema import ExecutionConfig, RetrievalConfig
from researchlens.ingest import CORPUS, ROOT, TECHNICAL_CORPUS, build_index
from researchlens.models import SearchHit
from researchlens.retrieval import Retriever


@pytest.fixture
def inputs(tmp_path):
    index = tmp_path / "index.json"
    build_index(CORPUS, index)
    artifact = json.loads(index.read_bytes())
    dataset = load_dataset(ROOT / "evaluation/datasets/development.json")
    return dataset, artifact, Retriever.from_path(index)


def embedding_artifact(artifact, *, model="test/model-a", dimensions=3):
    result = deepcopy(artifact)
    result["schema_version"] = 2
    matrix = np.zeros((len(artifact["passages"]), dimensions), dtype=np.float32)
    matrix[:, 0] = 1
    result["embeddings"] = {
        "encoding": {
            "model": model,
            "revision": "a" * 40,
            "dimensions": dimensions,
            "max_tokens": 256,
            "pooling": "mean",
            "normalization": "l2",
            "query_prefix": "",
            "document_prefix": "",
            "text": "passage-text-only",
            "encoding_version": 1,
            "runtime": "mock",
            "runtime_version": "test",
            "backend": "mock-cpu",
            "device": "cpu",
            "precision": "float32",
            "quantization": "none",
            "truncation": "longest-first",
            "batch_size": 32,
        },
        "passage_ids": [p["id"] for p in artifact["passages"]],
        "vectors": matrix.tolist(),
        "vectors_sha256": hashlib.sha256(matrix.astype("<f4").tobytes()).hexdigest(),
    }
    return result


def test_schema_two_can_compare_different_models_with_same_passages(inputs):
    dataset, artifact, retriever = inputs
    first = embedding_artifact(artifact)
    second = embedding_artifact(artifact, model="test/model-b", dimensions=5)
    runs = [
        run_evaluation(
            dataset, candidate, retriever, default_retrieval_config("embeddings", candidate, "mock")
        )
        for candidate in (first, second)
    ]
    assert runs[0]["corpus"]["shared_passage_sha256"] == runs[1]["corpus"]["shared_passage_sha256"]
    assert (
        runs[0]["corpus"]["embedding_artifact_sha256"]
        != runs[1]["corpus"]["embedding_artifact_sha256"]
    )
    assert runs[0]["retrieval"]["model"] != runs[1]["retrieval"]["model"]
    assert "test/model-b" in comparison_report(runs, [None, None])
    lexical = run_evaluation(
        dataset, artifact, retriever, RetrievalConfig(implementation="tfidf", version="test")
    )
    assert "Shared passage identity" in comparison_report([lexical, runs[0]], [None, None])


@pytest.mark.parametrize(
    "field",
    [
        "text",
        "id",
        "source_url",
        "license",
        "source_locator",
        "source_section",
        "attribution",
        "order",
        "chunking",
    ],
)
def test_comparison_rejects_changed_shared_inputs(inputs, field):
    dataset, artifact, retriever = inputs
    baseline = run_evaluation(
        dataset, artifact, retriever, RetrievalConfig(implementation="tfidf", version="test")
    )
    changed = deepcopy(artifact)
    if field == "chunking":
        changed["chunking"]["max_words"] = 179
    elif field == "order":
        changed["passages"].reverse()
    elif field == "attribution":
        changed["passages"][0][field] = dict(
            authors=["Test author"],
            publication_date="2024-01-01",
            doi="test",
            license_url="https://creativecommons.org/licenses/by/4.0/",
            copyright="test",
            changes="test",
            source_sha256="0" * 64,
        )
    else:
        changed["passages"][0][field] = "changed"
    candidate = run_evaluation(
        dataset, changed, retriever, RetrievalConfig(implementation="tfidf", version="test")
    )
    with pytest.raises(ValueError, match="same dataset"):
        comparison_report([baseline, candidate], [None, None])


@pytest.mark.parametrize(
    "change",
    ["row-order", "checksum", "dimensions", "nan", "zero", "norm", "credentials", "unpinned"],
)
def test_malformed_embedding_artifacts_fail_closed(inputs, change):
    artifact = embedding_artifact(inputs[1])
    saved = artifact["embeddings"]
    if change == "row-order":
        saved["passage_ids"].reverse()
    elif change == "checksum":
        saved["vectors_sha256"] = "0" * 64
    elif change == "dimensions":
        saved["encoding"]["dimensions"] = 4
    elif change == "nan":
        saved["vectors"][0][0] = float("nan")
    elif change == "zero":
        saved["vectors"][0] = [0, 0, 0]
    elif change == "norm":
        saved["vectors"][0] = [2, 0, 0]
    elif change == "credentials":
        saved["encoding"]["api_key"] = "test-secret"
    else:
        saved["encoding"]["revision"] = "main"
    with pytest.raises((ValueError, KeyError)):
        validate_passage_artifact(artifact)


def test_shared_loader_validates_source_content_not_just_ids(inputs, tmp_path):
    dataset, artifact, _ = inputs
    artifact["passages"][0]["text"] = "tampered"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(ValueError, match="Passages do not match"):
        load_artifact(path, source=CORPUS)
    artifact["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash differs"):
        validate_artifact(dataset, artifact)


def test_retrieval_config_cannot_mislabel_saved_encoding(inputs):
    candidate = embedding_artifact(inputs[1])
    config = default_retrieval_config("embeddings", candidate, "mock")
    bad = config.model_copy(update={"query_instruction": "different instructions"})
    with pytest.raises(ValueError, match="settings differ"):
        run_evaluation(inputs[0], candidate, inputs[2], bad)
    with pytest.raises(ValidationError):
        RetrievalConfig(implementation="mock", version="1", api_key="test-secret")
    with pytest.raises(ValidationError):
        RetrievalConfig(implementation="mock", version="1", backend="hybrid")
    assert (
        RetrievalConfig(
            implementation="hybrid",
            version="1",
            backend="hybrid",
            lexical_candidates=20,
            embedding_candidates=20,
            fusion_method="rrf",
            rrf_k=60,
        ).rrf_k
        == 60
    )


def test_mrr_distinguishes_first_and_third_rank_and_excludes_unanswerable(inputs):
    dataset, artifact, _ = inputs
    dataset = dataset.model_copy(update={"cases": [dataset.cases[0], dataset.cases[2]]})
    relevant = "fixture-dark-field:p2:w0"
    passages = validate_passage_artifact(artifact)

    class Ranked:
        def __init__(self, rank):
            self.rank = rank

        def search(self, question, limit=4):
            result = [p for p in passages if p.id != relevant][:2]
            result.insert(self.rank - 1, next(p for p in passages if p.id == relevant))
            return [SearchHit(**p.model_dump(), score=1 / (i + 1)) for i, p in enumerate(result)]

    runs = [
        run_evaluation(
            dataset,
            artifact,
            Ranked(rank),
            RetrievalConfig(implementation="ranked", version="test"),
        )
        for rank in (1, 3)
    ]
    assert runs[0]["results"][0]["first_relevant_passage_rank"] == 1
    assert runs[1]["results"][0]["first_relevant_passage_rank"] == 3
    assert summarize(runs[0])["mrr_at_k_with_failures"] == 1
    assert summarize(runs[1])["mrr_at_k_with_failures"] == pytest.approx(1 / 3)
    assert runs[1]["results"][1]["reciprocal_rank_at_k"] is None
    assert (
        summarize(runs[0])["mean_source_recall_at_k"]
        == summarize(runs[1])["mean_source_recall_at_k"]
    )


def test_repeated_timings_separate_warmups_setup_and_failures(inputs, monkeypatch):
    dataset, artifact, retriever = inputs
    monkeypatch.setattr("researchlens.evaluation.process_peak_rss_bytes", lambda: 123456)
    run = run_evaluation(
        dataset,
        artifact,
        retriever,
        RetrievalConfig(implementation="tfidf", version="test"),
        execution=ExecutionConfig(
            repeats=3, warmups=1, measure_memory=True, ingestion_time_ms=10, index_load_time_ms=2
        ),
    )
    summary = summarize(run)
    assert summary["query_timing_samples"] == 9
    assert summary["ingestion_time_ms"] == 10
    assert summary["index_load_time_ms"] == 2
    assert summary["process_peak_rss_bytes"] == 123456
    assert all(r["warmup_latency_ms"] is not None for r in run["results"])
    assert all(r["ranking_stable_across_repeats"] for r in run["results"])
    assert all(c.status == "not-applicable" for c in review_template(run).cases)

    class FailsOnSecond:
        calls = 0

        def search(self, question, limit=4):
            self.calls += 1
            if self.calls == 2:
                raise RuntimeError("private credential")
            return retriever.search(question, limit)

    failure = run_evaluation(
        dataset,
        artifact,
        FailsOnSecond(),
        RetrievalConfig(implementation="test", version="1"),
        execution=ExecutionConfig(repeats=3),
    )
    assert failure["results"][0]["retrieved_passage_ids"]
    assert failure["results"][0]["error"]
    assert len(failure["results"][0]["retrieval_attempts"]) == 2
    assert "private credential" not in json.dumps(failure)
    assert summarize(failure)["errors"] == 1


def test_technical_drafts_pin_originals_and_locations(tmp_path):
    path = tmp_path / "technical.json"
    build_index(TECHNICAL_CORPUS, path)
    artifact = json.loads(path.read_bytes())
    dataset = load_dataset(ROOT / "evaluation/datasets/technical-development.json")
    held_out = load_dataset(ROOT / "evaluation/datasets/held-out.json")
    validate_splits(dataset, held_out)
    assert len(dataset.source_versions) == 4
    assert {c.query_style for c in dataset.cases} == {
        "exact-terminology",
        "paraphrase",
        "cross-document",
        "unrelated",
        "missing-evidence",
    }
    assert all(c.review_status == "unreviewed" and c.reviewer is None for c in dataset.cases)
    assert all(r.source_locator and r.source_section for c in dataset.cases for r in c.references)
    validate_artifact(dataset, artifact)
    assert not held_out.cases
    with pytest.raises(ValueError, match="pending"):
        validate_artifact(held_out, artifact)
    changed = dataset.model_copy(deep=True)
    changed.source_versions[0].source_sha256 = "0" * 64
    with pytest.raises(ValueError, match="Original source version"):
        validate_artifact(changed, artifact)


def test_cli_delegates_schema_two_selection_to_retrieval_factory(inputs, tmp_path, monkeypatch):
    artifact = embedding_artifact(inputs[1])
    path = tmp_path / "embedding.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    output = tmp_path / "selected"
    selected = []

    def factory(backend, index, *, source):
        selected.append((backend, index, source))
        return inputs[2]  # Explicit mocked integration, not a real model quality result.

    monkeypatch.setattr("researchlens.evaluation.load_retriever", factory)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "evaluation",
            "run",
            "--dataset",
            str(ROOT / "evaluation/datasets/development.json"),
            "--other-split",
            str(ROOT / "evaluation/datasets/held-out.json"),
            "--index",
            str(path),
            "--source",
            str(CORPUS),
            "--retriever",
            "embeddings",
            "--output",
            str(output),
            "--repeats",
            "2",
        ],
    )
    main()
    assert selected == [("embeddings", path, CORPUS)]
    run = json.loads((output / "run.json").read_bytes())
    assert run["retrieval"]["backend"] == "embeddings"
    assert run["retrieval"]["device"] == "cpu"
    assert run["execution"]["index_load_time_ms"] >= 0
    assert run["corpus"]["embedding_artifact_sha256"] == canonical_hash(artifact)


def test_legacy_reports_remain_strict_and_cannot_mix_with_new_runs(inputs):
    current = run_evaluation(*inputs, RetrievalConfig(implementation="tfidf", version="test"))
    legacy = deepcopy(current)
    legacy["schema_version"] = 1
    legacy["corpus"].pop("shared_passage_sha256")
    assert "Evaluation comparison" in comparison_report([legacy, deepcopy(legacy)], [None, None])
    changed = deepcopy(legacy)
    changed["corpus"]["artifact_sha256"] = "different"
    with pytest.raises(ValueError, match="same dataset"):
        comparison_report([legacy, changed], [None, None])
    with pytest.raises(ValueError, match="legacy"):
        comparison_report([legacy, current], [None, None])
