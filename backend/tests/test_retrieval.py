"""Offline contract tests, not evidence of semantic retrieval quality."""

import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from researchlens.answers import INSTRUCTIONS, OpenAIProvider
from researchlens.api import create_app
from researchlens.config import ROOT, Settings, retrieval_environment
from researchlens.embedding_models import encoding_metadata
from researchlens.embeddings import DIMENSIONS, ENCODING, LocalEncoder
from researchlens.ingest import CORPUS, build_index
from researchlens.models import GeneratedAnswer
from researchlens.retrieval import EmbeddingRetriever, Retriever, TfidfRetriever, load_retriever


def unit_vectors(count):
    matrix = np.zeros((count, DIMENSIONS), dtype=np.float32)
    matrix[:, 0] = 1
    return matrix


@pytest.fixture
def encoder(monkeypatch):
    instance = Mock()
    instance.encode.side_effect = lambda texts: unit_vectors(len(texts))
    factory = Mock(return_value=instance)
    instance.encoding = encoding_metadata()
    monkeypatch.setattr("researchlens.embedding_models.create_encoder", factory)
    monkeypatch.setattr("researchlens.retrieval.create_encoder", factory)
    return factory, instance


@pytest.fixture
def embedding_index(tmp_path, encoder):
    path = tmp_path / "index.json"
    build_index(CORPUS, path, retrieval="embeddings")
    return path


def test_ingestion_encodes_once_and_preserves_metadata(embedding_index, encoder, tmp_path):
    lexical = tmp_path / "lexical.json"
    build_index(CORPUS, lexical)
    baseline = json.loads(lexical.read_text())
    artifact = json.loads(embedding_index.read_text())
    assert artifact["passages"] == baseline["passages"]
    assert artifact["chunking"] == baseline["chunking"]
    assert artifact["source_sha256"] == hashlib.sha256(CORPUS.read_bytes()).hexdigest()
    assert artifact["embeddings"]["encoding"] == encoder[1].encoding
    assert encoder[0].call_args.kwargs["download"] is True
    encoder[1].encode.assert_called_once_with([p["text"] for p in artifact["passages"]])


def test_compatible_baseline_and_embedding_search(embedding_index, encoder):
    baseline = Retriever.from_path(embedding_index)
    assert isinstance(baseline, TfidfRetriever)
    semantic = EmbeddingRetriever.from_path(embedding_index)
    assert [p.model_dump() for p in baseline.passages] == [
        p.model_dump() for p in semantic.passages
    ]
    # Ties use original artifact order, and metadata/IDs survive unchanged.
    hits = semantic.search("A query", 2)
    assert [h.id for h in hits] == [p.id for p in semantic.passages[:2]]
    for hit, passage in zip(hits, semantic.passages, strict=False):
        assert hit.model_dump(exclude={"score"}) == passage.model_dump()
    assert len(semantic.search("Another query", 999)) == len(semantic.passages)
    assert semantic.search("  ") == []
    for retriever in (baseline, semantic):
        with pytest.raises(ValueError, match="positive"):
            retriever.search("query", 0)
    # One encoder per ingestion/startup, never per search; no document re-encoding at startup.
    assert encoder[0].call_count == 2
    assert not encoder[0].call_args.kwargs.get("download", False)
    assert [call.args[0] for call in encoder[1].encode.call_args_list[1:]] == [
        ["A query"],
        ["Another query"],
    ]


def test_cosine_ranking_does_not_claim_answerability(embedding_index, encoder):
    semantic = EmbeddingRetriever.from_path(embedding_index)
    semantic.matrix[0] = -semantic.matrix[0]
    hits = semantic.search("Unrelated question", 999)
    assert hits[-1].id == semantic.passages[0].id
    assert hits[-1].score == -1.0
    assert hits[0].score == 1.0
    # No arbitrary cutoff that pretends to prove relevance or answerability.
    assert len(hits) == len(semantic.passages)


@pytest.mark.parametrize("backend", ["tfidf", "embeddings"])
def test_api_loads_once_and_keeps_limits(embedding_index, encoder, backend):
    settings = Settings(retrieval=backend, index_path=embedding_index, corpus_path=CORPUS)
    with TestClient(create_app(settings=settings)) as client:
        for _ in range(2):
            response = client.post(
                "/api/ask", json={"question": "Does dust cause false positives?"}
            )
            assert response.status_code == 200
            answer = response.json()
            assert answer["mode"] == "local_preview"
            assert len(answer["passages"]) <= 4
            assert answer["sections"] == []
            assert answer["estimated_api_cost_usd"] == 0
            assert "cannot determine whether they answer" in answer["message"]
        assert client.post("/api/ask", json={"question": "x" * 2001}).status_code == 422
    assert encoder[0].call_count == (2 if backend == "embeddings" else 1)


@pytest.mark.parametrize("backend", ["tfidf", "embeddings"])
def test_unrelated_query_preserves_provider_abstention(embedding_index, backend):
    sdk = Mock()
    sdk.responses.parse.return_value = SimpleNamespace(
        status="completed",
        usage=None,
        output_parsed=GeneratedAnswer(status="insufficient_evidence", sections=[]),
    )
    settings = Settings(provider="openai", api_key="fake-test-key", retrieval=backend)
    provider = OpenAIProvider(settings, client=sdk)
    retriever = load_retriever(backend, embedding_index)
    with TestClient(create_app(retriever, settings, provider)) as client:
        answer = client.post(
            "/api/ask", json={"question": "Who composed Beethoven symphonies?"}
        ).json()
    assert answer["sections"] == []
    if backend == "tfidf":
        assert answer["status"] == "no_matches"
        sdk.responses.parse.assert_not_called()
    else:
        assert answer["status"] == "insufficient_evidence"
        assert len(answer["passages"]) == 4
        sdk.responses.parse.assert_called_once()
        arguments = sdk.responses.parse.call_args.kwargs
        assert arguments["instructions"] == INSTRUCTIONS
        assert arguments["model"] == "gpt-6-luna"
        assert arguments["reasoning"] == {"effort": "medium"}
        assert arguments["max_output_tokens"] == 2000
        assert len(json.loads(arguments["input"])["passages"]) == 4


@pytest.mark.parametrize(
    "damage",
    [
        "schema",
        "hash",
        "chunking",
        "passage_text",
        "passage_id",
        "passage_order",
        "revision",
        "pooling",
        "ids",
        "row_count",
        "dimensions",
        "nan",
        "zero",
        "not_normalized",
        "checksum",
        "no_embeddings",
        "malformed",
    ],
)
def test_rejects_invalid_artifact_before_loading_model(embedding_index, encoder, damage):
    saved = json.loads(embedding_index.read_text())
    vectors = saved["embeddings"]["vectors"]
    if damage == "schema":
        saved["schema_version"] = 99
    elif damage == "hash":
        saved["source_sha256"] = "stale"
    elif damage == "chunking":
        saved["chunking"]["max_words"] = 999
    elif damage == "passage_text":
        saved["passages"][0]["text"] += " changed"
    elif damage == "passage_id":
        saved["passages"][0]["id"] = "changed"
    elif damage == "passage_order":
        saved["passages"].reverse()
    elif damage in ("revision", "pooling"):
        saved["embeddings"]["encoding"][damage] = "incompatible"
    elif damage == "ids":
        saved["embeddings"]["passage_ids"].reverse()
    elif damage == "row_count":
        vectors.pop()
    elif damage == "dimensions":
        vectors[0].pop()
    elif damage == "nan":
        vectors[0][0] = float("nan")
    elif damage == "zero":
        vectors[0][0] = 0
    elif damage == "not_normalized":
        vectors[0][0] = 2
    elif damage == "checksum":
        vectors[0][0] = -1  # Still a unit vector; checksum catches the change.
    elif damage == "no_embeddings":
        saved.pop("embeddings")
    elif damage == "malformed":
        saved = None
    embedding_index.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="Rebuild.*researchlens.ingest.*--retrieval embeddings"):
        EmbeddingRetriever.from_path(embedding_index, source=CORPUS)
    assert encoder[0].call_count == 1


@pytest.mark.parametrize("backend", ["tfidf", "embeddings"])
def test_detects_changed_source_and_missing_artifact(embedding_index, tmp_path, backend):
    changed = tmp_path / "source.json"
    changed.write_bytes(CORPUS.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="stale"):
        load_retriever(backend, embedding_index, source=changed)
    with pytest.raises(ValueError, match="Rebuild"):
        load_retriever(backend, tmp_path / "missing.json")
    with pytest.raises(RuntimeError, match="researchlens.ingest"):
        with TestClient(create_app(settings=Settings(retrieval=backend, index_path=changed))):
            pass


def test_schema_one_baseline_remains_readable(tmp_path):
    path = tmp_path / "old.json"
    build_index(CORPUS, path)
    saved = json.loads(path.read_text())
    saved["schema_version"] = 1
    path.write_text(json.dumps(saved))
    assert Retriever.from_path(path).search("dust")[0].id == "fixture-dark-field:p2:w0"
    with pytest.raises(ValueError, match="Rebuild"):
        EmbeddingRetriever.from_path(path)


def test_failed_ingestion_preserves_existing_artifact(embedding_index, encoder):
    before = embedding_index.read_bytes()
    encoder[1].encode.side_effect = RuntimeError("model failure")
    with pytest.raises(RuntimeError, match="model failure"):
        build_index(CORPUS, embedding_index, retrieval="embeddings")
    assert embedding_index.read_bytes() == before


def test_retrieval_configuration(tmp_path, monkeypatch):
    for name in ("RETRIEVAL_BACKEND", "RETRIEVAL_INDEX", "RETRIEVAL_CORPUS"):
        monkeypatch.delenv(name, raising=False)
    env = tmp_path / ".env"
    env.write_text("RETRIEVAL_BACKEND=embeddings\nRETRIEVAL_INDEX=data/custom.json\n")
    assert retrieval_environment(env)["index_path"] == ROOT / "data" / "custom.json"
    assert Settings.from_env(env).retrieval == "embeddings"
    monkeypatch.setenv("RETRIEVAL_BACKEND", "tfidf")
    assert Settings.from_env(env).retrieval == "tfidf"
    monkeypatch.setenv("RETRIEVAL_BACKEND", "remote")
    with pytest.raises(ValueError, match="RETRIEVAL_BACKEND"):
        Settings.from_env(env)


def test_encoder_masked_pooling_and_identical_plain_text_encoding():
    encoder = LocalEncoder.__new__(LocalEncoder)
    encoder.batch_size = 32
    encoder.tokenizer = Mock()
    encoder.tokenizer.encode_batch.return_value = [
        SimpleNamespace(ids=[101, 102, 0], attention_mask=[1, 1, 0], type_ids=[0, 0, 0])
    ]
    encoder.session = Mock()
    hidden = np.zeros((1, 3, DIMENSIONS), dtype=np.float32)
    hidden[0, 0, 0] = 2
    hidden[0, 1, 1] = 2
    hidden[0, 2, 2] = 999  # Padding must not contribute to pooling.
    encoder.session.run.return_value = [hidden]
    encoder.input_names = {"input_ids", "attention_mask", "token_type_ids"}
    vector = encoder.encode(["Plain question or passage"])[0]
    encoder.tokenizer.encode_batch.assert_called_once_with(["Plain question or passage"])
    assert np.allclose(vector[:3], [2**-0.5, 2**-0.5, 0])
    assert np.isclose(np.linalg.norm(vector), 1)
    assert encoder.session.run.call_args.args[1]["input_ids"].dtype == np.int64


def test_encoder_pinned_download_and_cache_only_startup(monkeypatch, tmp_path):
    import sys

    download = Mock(return_value=str(tmp_path / "cached-file"))
    tokenizer = Mock()
    session = Mock()
    session.get_inputs.return_value = []
    session_factory = Mock(return_value=session)
    options = SimpleNamespace()
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(hf_hub_download=download))
    monkeypatch.setitem(sys.modules, "tokenizers", SimpleNamespace(Tokenizer=tokenizer))
    monkeypatch.setitem(
        sys.modules,
        "onnxruntime",
        SimpleNamespace(SessionOptions=lambda: options, InferenceSession=session_factory),
    )
    LocalEncoder()
    assert download.call_count == 2
    assert all(call.kwargs["local_files_only"] for call in download.call_args_list)
    assert all(call.kwargs["revision"] == ENCODING["revision"] for call in download.call_args_list)
    assert all(call.kwargs["token"] is False for call in download.call_args_list)
    assert session_factory.call_args.kwargs["providers"] == ["CPUExecutionProvider"]
    tokenizer.from_file.return_value.enable_truncation.assert_called_once_with(max_length=256)
    LocalEncoder(download=True)
    assert download.call_args.kwargs["local_files_only"] is False
    download.side_effect = RuntimeError("sensitive upstream error")
    with pytest.raises(ValueError, match="researchlens.ingest") as error:
        LocalEncoder()
    assert "sensitive" not in str(error.value)
