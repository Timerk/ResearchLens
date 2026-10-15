"""Encoding/fusion contract tests; real model quality is measured by the evaluation runner."""

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, nullcontext
from threading import Barrier, Lock
from time import sleep
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from researchlens.api import create_app
from researchlens.config import Settings
from researchlens.embedding_models import (
    MODELS,
    QUERY_INSTRUCTION,
    TorchEncoder,
    encoding_metadata,
    model_for_encoding,
)
from researchlens.embeddings import validate_vectors
from researchlens.ingest import CORPUS, TECHNICAL_CORPUS, build_index, chunk_documents
from researchlens.models import Document, SearchHit
from researchlens.retrieval import EmbeddingRetriever, HybridRetriever, load_retriever


@pytest.fixture
def guarded_torch_encoder():
    class Tensor:
        def __init__(self, values):
            self.values = np.asarray(values, dtype=np.float32)
            self.shape = self.values.shape

        def __getitem__(self, key):
            return Tensor(self.values[key])

        def sum(self, *, dim):
            return self.values.sum(axis=dim).astype(int)

        def float(self):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return self.values

    active = Lock()
    calls = []

    @contextmanager
    def guard(operation):
        if not active.acquire(blocking=False):
            raise RuntimeError("Already borrowed")
        try:
            calls.append(operation)
            sleep(0.01)
            yield
        finally:
            active.release()

    def tokenize(texts, **kwargs):
        with guard("tokenizer"):
            if kwargs.get("return_tensors") == "pt":
                return {"attention_mask": Tensor([[1, 1]] * len(texts))}
            return {
                "input_ids": [1, 2],
                "offset_mapping": [(0, len(texts)), (0, 0)],
                "special_tokens_mask": [0, 1],
            }

    def model(**inputs):
        with guard("model"):
            return SimpleNamespace(
                last_hidden_state=Tensor([[[1, 0], [0, 1]]] * inputs["attention_mask"].shape[0])
            )

    encoder = TorchEncoder.__new__(TorchEncoder)
    encoder._lock = Lock()
    encoder.encoding = {**encoding_metadata("qwen3-0.6b"), "dimensions": 2}
    encoder.tokenizer = Mock(side_effect=tokenize, is_fast=True)
    encoder.model = model
    encoder.torch = SimpleNamespace(
        inference_mode=nullcontext,
        arange=np.arange,
        nn=SimpleNamespace(functional=SimpleNamespace(normalize=lambda tensor, **kwargs: tensor)),
    )
    return encoder, calls


@pytest.mark.parametrize(
    "operations", [("encode",), ("measure_documents",), ("encode", "measure_documents")]
)
def test_torch_encoder_serializes_shared_tokenizer_and_model(guarded_torch_encoder, operations):
    encoder, calls = guarded_torch_encoder
    start = Barrier(8)

    def run(index):
        start.wait(timeout=10)
        operation = operations[index % len(operations)]
        return getattr(encoder, operation)(["alpha beta", "gamma delta"])

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(run, range(8)))
    for index, result in enumerate(results):
        if operations[index % len(operations)] == "encode":
            assert np.array_equal(result, [[0, 1], [0, 1]])
        else:
            assert len(result) == 2
            assert all(row["input_tokens"] == 2 and not row["truncated"] for row in result)
    assert calls.count("model") == sum(
        2 for index in range(8) if operations[index % len(operations)] == "encode"
    )


def test_concurrent_ask_uses_shared_encoder(guarded_torch_encoder):
    encoder, calls = guarded_torch_encoder
    start = Barrier(24)

    def search(question, limit):
        encoder.encode([question])
        return []

    retriever = SimpleNamespace(search=search)
    with TestClient(create_app(retriever, settings=Settings())) as client:

        def ask(index):
            start.wait(timeout=10)
            return client.post("/api/ask", json={"question": f"Question number {index}?"})

        with ThreadPoolExecutor(max_workers=24) as pool:
            responses = list(pool.map(ask, range(24)))
    assert all(response.status_code == 200 for response in responses)
    assert all(response.json()["status"] == "no_matches" for response in responses)
    assert calls.count("model") == 24


@pytest.mark.parametrize(
    "operation,component",
    [("encode", "tokenizer"), ("encode", "model"), ("measure_documents", "tokenizer")],
)
def test_torch_encoder_propagates_errors_and_releases_lock(
    guarded_torch_encoder, operation, component
):
    encoder, _ = guarded_torch_encoder
    original = getattr(encoder, component)
    setattr(encoder, component, Mock(side_effect=RuntimeError("inference failed")))
    with pytest.raises(RuntimeError, match="inference failed"):
        getattr(encoder, operation)(["alpha beta"])
    assert encoder._lock.acquire(blocking=False)
    encoder._lock.release()
    setattr(encoder, component, original)
    assert len(getattr(encoder, operation)(["alpha beta"])) == 1


@pytest.mark.parametrize("name", list(MODELS))
def test_pinned_model_contract(name):
    metadata = encoding_metadata(name)
    assert len(metadata["revision"]) == 40
    assert model_for_encoding(metadata) == name
    assert metadata["device"] == "cpu"
    assert metadata["quantization"] == "none"
    assert metadata["document_prefix"] == ""
    assert metadata["max_tokens"] <= MODELS[name].max_tokens
    assert metadata["query_prefix"] == (QUERY_INSTRUCTION if name.startswith("qwen") else "")
    for field, value in (("revision", "a" * 40), ("dimensions", 7), ("query_prefix", "changed")):
        with pytest.raises(ValueError):
            model_for_encoding({**metadata, field: value})


def test_query_instruction_and_non_minilm_dimensions():
    metadata = encoding_metadata("qwen3-0.6b")
    document = Document(
        id="test", title="Test", source_url=None, license="CC0", kind="synthetic", text="Evidence"
    )
    passages = chunk_documents([document])
    vectors = np.zeros((1, 1024), dtype=np.float32)
    vectors[0, 0] = 1
    encoder = Mock()
    encoder.encode.return_value = vectors
    retriever = EmbeddingRetriever(passages, vectors, encoder, metadata)
    assert retriever.search("Question")[0].id == passages[0].id
    encoder.encode.assert_called_once_with([QUERY_INSTRUCTION + "Question"])
    with pytest.raises(ValueError, match="dimensions"):
        validate_vectors(vectors, 1)


def test_rrf_promotes_agreement_and_preserves_unique_full_passages(tmp_path):
    index = tmp_path / "index.json"
    build_index(CORPUS, index)
    passages = load_retriever("tfidf", index).passages
    fake = Mock()
    fake.passages = passages
    hybrid = HybridRetriever(fake, lexical_candidates=3, embedding_candidates=3, rrf_k=60)

    def hit(index):
        return SearchHit(**passages[index].model_dump(), score=0.5)

    hybrid.lexical = Mock()
    hybrid.lexical.search.return_value = [hit(0), hit(1), hit(2)]
    fake.search.return_value = [hit(3), hit(1), hit(2)]
    results = hybrid.search("Question", 4)
    assert [h.id for h in results] == [passages[i].id for i in (1, 2, 0, 3)]
    assert results[0].score == pytest.approx(2 / 62)
    assert len({h.id for h in results}) == 4
    assert results[0].model_dump(exclude={"score"}) == passages[1].model_dump()
    hybrid.lexical.search.assert_called_once_with("Question", 3)
    fake.search.assert_called_once_with("Question", 3)
    with pytest.raises(ValueError, match="positive"):
        hybrid.search("Question", 0)
    with pytest.raises(ValueError):
        HybridRetriever(fake, fusion_method="weighted-score")


def test_model_mismatch_fails_before_encoder_loading(tmp_path, monkeypatch):
    encoder = Mock()
    encoder.encoding = encoding_metadata()
    vectors = np.zeros((6, 384), dtype=np.float32)
    vectors[:, 0] = 1
    encoder.encode.return_value = vectors
    factory = Mock(return_value=encoder)
    monkeypatch.setattr("researchlens.embedding_models.create_encoder", factory)
    monkeypatch.setattr("researchlens.retrieval.create_encoder", factory)
    index = tmp_path / "index.json"
    build_index(CORPUS, index, retrieval="embeddings")
    with pytest.raises(ValueError, match="mismatch"):
        load_retriever("embeddings", index, expected_model="bge-m3")
    assert factory.call_count == 1


def test_technical_embedding_ingestion_preserves_all_attribution(tmp_path, monkeypatch):
    encoder = Mock()
    encoder.encoding = encoding_metadata("bge-m3")

    def vectors(texts):
        matrix = np.zeros((len(texts), 1024), dtype=np.float32)
        matrix[:, 0] = 1
        return matrix

    encoder.encode.side_effect = vectors
    monkeypatch.setattr("researchlens.embedding_models.create_encoder", Mock(return_value=encoder))
    baseline, embedded = tmp_path / "baseline.json", tmp_path / "embedded.json"
    build_index(TECHNICAL_CORPUS, baseline)
    build_index(TECHNICAL_CORPUS, embedded, retrieval="embeddings", embedding_model="bge-m3")
    first, second = json.loads(baseline.read_bytes()), json.loads(embedded.read_bytes())
    assert first["passages"] == second["passages"]
    assert all(p["attribution"] and p["source_locator"] for p in second["passages"])


@pytest.mark.parametrize("name", ["bge-m3", "qwen3-0.6b"])
def test_torch_pooling_excludes_right_padding(name):
    torch = pytest.importorskip("torch")
    encoder = TorchEncoder.__new__(TorchEncoder)
    encoder.torch = torch
    encoder._lock = Lock()
    encoder.encoding = encoding_metadata(name)
    encoder.tokenizer = Mock(
        return_value={
            "input_ids": torch.tensor([[1, 2, 0], [3, 4, 5]]),
            "attention_mask": torch.tensor([[1, 1, 0], [1, 1, 1]]),
        }
    )
    hidden = torch.tensor(
        [[[1.0, 0.0], [0.0, 2.0], [999.0, 999.0]], [[1.0, 0.0], [0.0, 2.0], [2.0, 0.0]]]
    )
    encoder.model = Mock(return_value=Mock(last_hidden_state=hidden))
    encoder.encoding["batch_size"] = 2
    vectors = encoder.encode(["first", "second"])
    expected = [[1.0, 0.0], [1.0, 0.0]] if name == "bge-m3" else [[0.0, 1.0], [1.0, 0.0]]
    assert np.allclose(vectors, expected)
    if name.startswith("qwen"):
        assert encoder.model.call_args.kwargs["use_cache"] is False
