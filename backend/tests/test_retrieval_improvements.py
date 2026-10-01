"""Offline ranking, configuration and actual-tokenizer visibility checks."""

import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from researchlens.config import Settings
from researchlens.embedding_models import TorchEncoder, encoding_metadata
from researchlens.embeddings import LocalEncoder
from researchlens.encoding_diagnostics import measurement
from researchlens.evaluation import default_retrieval_config
from researchlens.evaluation_evidence import (
    EncodingDiagnostics,
    validate_encoding_diagnostics,
    validate_pair_diagnostics,
)
from researchlens.evaluation_schema import RetrievalConfig
from researchlens.ingest import CORPUS, build_index, chunk_documents
from researchlens.models import Document, Passage, SearchHit
from researchlens.reranking import LocalReranker, RerankedRetriever, reranker_metadata
from researchlens.retrieval import EmbeddingRetriever, HybridRetriever, load_retriever


def sample_hits():
    passages = chunk_documents(
        [
            Document(
                id="doc",
                title="Document",
                source_url=None,
                license="CC0",
                kind="synthetic",
                text="alpha beta\n\nalpha beta again\n\ngamma delta",
            )
        ]
    )
    return [SearchHit(**passage.model_dump(), score=0.5) for passage in passages]


def test_weighted_fusion_zero_component_and_invalid_weights():
    hits = sample_hits()
    dense = SimpleNamespace(
        passages=[Passage.model_validate(hit.model_dump(exclude={"score"})) for hit in hits],
        search=Mock(return_value=hits[::-1]),
    )
    hybrid = HybridRetriever(dense, lexical_weight=0, embedding_weight=1)
    hybrid.lexical.search = Mock(
        side_effect=AssertionError("zero-weight component must not search")
    )
    assert [hit.id for hit in hybrid.search("question", 3)] == [hit.id for hit in hits[::-1]]
    for lexical, embedding in ((0, 0), (-0.1, 1), (1, 2), (float("nan"), 1), (1, float("inf"))):
        with pytest.raises(ValueError, match="Fusion weights"):
            HybridRetriever(dense, lexical_weight=lexical, embedding_weight=embedding)


def test_reranking_dedicated_pool_preserves_passages_and_stable_ties():
    hits = sample_hits()
    base = SimpleNamespace(passages=hits, search=Mock(return_value=hits[::-1]))
    scorer = SimpleNamespace(
        metadata=reranker_metadata(),
        score=Mock(return_value=np.array([5, 1, 5])),
        last_diagnostics=[],
    )
    retriever = RerankedRetriever(base, scorer, candidates=20)
    result = retriever.search("question", 2)
    # Equal logits use artifact order, regardless of candidate order.
    assert [hit.id for hit in result] == [hits[0].id, hits[2].id]
    assert result[0].model_dump(exclude={"score"}) == hits[0].model_dump(exclude={"score"})
    base.search.assert_called_once_with("question", 20)
    assert result[0].score == 5
    with pytest.raises(ValueError, match="candidate count"):
        retriever.search("question", 21)
    scorer.score.return_value = np.array([1, np.nan, 3])
    with pytest.raises(ValueError, match="logits"):
        retriever.search("question")


def test_redundancy_penalty_promotes_distinct_passage_without_labels():
    hits = sample_hits()
    base = SimpleNamespace(
        passages=hits,
        search=lambda q, limit: hits,
        matrix=np.array([[1, 0], [1, 0], [0, 1]], dtype=np.float32),
    )
    scorer = SimpleNamespace(
        metadata=reranker_metadata(), score=lambda q, p: np.array([3, 2, 1]), last_diagnostics=[]
    )
    retriever = RerankedRetriever(base, scorer, candidates=20, diversity=0.5)
    assert [hit.id for hit in retriever.search("question", 3)] == [hits[i].id for i in (0, 2, 1)]
    # Changing search limits only slices the fixed ranking.
    assert retriever.search("question", 1)[0].id == hits[0].id


def test_minilm_measurements_use_offsets_and_leave_live_tokenizer_unchanged():
    tokenizers = pytest.importorskip("tokenizers")
    tokenizer = tokenizers.Tokenizer(
        tokenizers.models.WordLevel(
            {
                "[UNK]": 0,
                "[CLS]": 1,
                "[SEP]": 2,
                "alpha": 3,
                "beta": 4,
                "gamma": 5,
                "delta": 6,
                "epsilon": 7,
            },
            unk_token="[UNK]",
        )
    )
    tokenizer.pre_tokenizer = tokenizers.pre_tokenizers.Whitespace()
    tokenizer.post_processor = tokenizers.processors.TemplateProcessing(
        single="[CLS] $A [SEP]",
        special_tokens=[("[CLS]", 1), ("[SEP]", 2)],
    )
    tokenizer.enable_truncation(max_length=5)
    encoder = LocalEncoder.__new__(LocalEncoder)
    encoder.tokenizer = tokenizer
    before = tokenizer.to_str()
    rows = encoder.measure_documents(["alpha beta gamma delta epsilon", "α β  "])
    assert rows[0]["input_tokens"] == 7
    assert rows[0]["encoded_tokens"] == 5
    assert rows[0]["retained_ranges"] == [{"start": 0, "end": 16}]
    assert rows[0]["truncated"] is True
    assert rows[1]["retained_ranges"] == [{"start": 0, "end": 5}]
    assert rows[1]["truncated"] is False
    assert tokenizer.to_str() == before


def test_torch_measurements_count_special_tokens_and_actual_character_offsets():
    tokenizer = Mock()
    tokenizer.is_fast = True
    tokenizer.side_effect = [
        {"input_ids": [0, 1, 2, 3, 4]},
        {
            "input_ids": [0, 1, 4],
            "offset_mapping": [(0, 0), (0, 2), (0, 0)],
            "special_tokens_mask": [1, 0, 1],
        },
    ]
    encoder = TorchEncoder.__new__(TorchEncoder)
    encoder.tokenizer, encoder.encoding = tokenizer, {"max_tokens": 3}
    row = encoder.measure_documents(["αβ γδ"])[0]
    assert row == measurement("αβ γδ", 5, 3, 2)
    assert tokenizer.call_args.kwargs["return_offsets_mapping"] is True
    assert tokenizer.call_args.kwargs["max_length"] == 3


def test_diagnostics_bind_exact_artifact_and_are_cached(tmp_path, monkeypatch):
    encoder = Mock()
    encoder.encoding = encoding_metadata()
    matrix = np.zeros((6, 384), dtype=np.float32)
    matrix[:, 0] = 1
    encoder.encode.return_value = matrix
    encoder.measure_documents.side_effect = lambda texts: [
        measurement(text, 4, 4, len(text)) for text in texts
    ]
    monkeypatch.setattr("researchlens.embedding_models.create_encoder", lambda *a, **k: encoder)
    monkeypatch.setattr("researchlens.retrieval.create_encoder", lambda *a, **k: encoder)
    path = tmp_path / "index.json"
    build_index(CORPUS, path, retrieval="embeddings")
    retriever = EmbeddingRetriever.from_path(path, source=CORPUS)
    diagnostics = retriever.get_encoding_diagnostics()
    artifact = json.loads(path.read_bytes())
    validated = validate_encoding_diagnostics(
        EncodingDiagnostics.model_validate(diagnostics), artifact, retriever.passages
    )
    assert len(validated) == 6
    assert retriever.get_encoding_diagnostics() is diagnostics
    encoder.measure_documents.assert_called_once()
    changed = {**artifact, "source_sha256": "0" * 64}
    with pytest.raises(ValueError, match="match embedding artifact"):
        validate_encoding_diagnostics(
            EncodingDiagnostics.model_validate(diagnostics), changed, retriever.passages
        )


def test_configured_model_validation_reads_index_and_loads_encoder_once(tmp_path, monkeypatch):
    import researchlens.retrieval as retrieval

    encoder = Mock()
    encoder.encoding = encoding_metadata()
    matrix = np.zeros((6, 384), dtype=np.float32)
    matrix[:, 0] = 1
    encoder.encode.return_value = matrix
    monkeypatch.setattr("researchlens.embedding_models.create_encoder", lambda *a, **k: encoder)
    path = tmp_path / "index.json"
    build_index(CORPUS, path, retrieval="embeddings")
    loader = Mock(wraps=retrieval._load_artifact)
    factory = Mock(return_value=encoder)
    monkeypatch.setattr(retrieval, "_load_artifact", loader)
    monkeypatch.setattr(retrieval, "create_encoder", factory)
    load_retriever("embeddings", path, source=CORPUS, expected_model="minilm")
    loader.assert_called_once_with(path, CORPUS)
    factory.assert_called_once()


def test_reranker_measurements_reject_stale_text_and_out_of_bounds_ranges():
    hits = sample_hits()
    row = {"passage_id": hits[0].id, **measurement(hits[0].text, 7, 7, len(hits[0].text))}
    assert validate_pair_diagnostics([row], hits, 512)[0] == row
    for changed in (
        {**row, "text_sha256": "0" * 64},
        {**row, "encoded_tokens": 513},
        {**row, "retained_ranges": [{"start": 0, "end": 999}]},
    ):
        with pytest.raises(ValueError):
            validate_pair_diagnostics([changed], hits, 512)


def test_reranker_startup_is_pinned_cache_only_and_hides_upstream_errors(monkeypatch):
    download = Mock(return_value="cached-file")
    tokenizer = Mock()
    session = Mock()
    session.get_inputs.return_value = []
    options = SimpleNamespace()
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(hf_hub_download=download))
    monkeypatch.setitem(sys.modules, "tokenizers", SimpleNamespace(Tokenizer=tokenizer))
    monkeypatch.setitem(
        sys.modules,
        "onnxruntime",
        SimpleNamespace(
            SessionOptions=lambda: options,
            InferenceSession=Mock(return_value=session),
        ),
    )
    LocalReranker()
    assert download.call_count == 2
    assert all(
        call.kwargs["local_files_only"] and call.kwargs["token"] is False
        for call in download.call_args_list
    )
    assert all(
        call.kwargs["revision"] == reranker_metadata()["revision"]
        for call in download.call_args_list
    )
    LocalReranker(download=True)
    assert download.call_args.kwargs["local_files_only"] is False
    download.side_effect = RuntimeError("private upstream credential")
    with pytest.raises(ValueError, match="researchlens.reranking") as error:
        LocalReranker()
    assert "private upstream" not in str(error.value)


def test_optional_settings_and_evaluation_metadata_are_explicit(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "RETRIEVAL_BACKEND=hybrid\nRETRIEVAL_RERANKER=minilm\nHYBRID_LEXICAL_WEIGHT=0.25\nHYBRID_EMBEDDING_WEIGHT=0.75\nHYBRID_CANDIDATES=40\n",
        encoding="utf-8",
    )
    settings = Settings.from_env(env)
    assert settings.retriever_options()["hybrid_settings"]["lexical_weight"] == 0.25
    assert (
        settings.retriever_options()["reranker_settings"]["revision"]
        == reranker_metadata()["revision"]
    )
    assert Settings().reranker == "none"
    with pytest.raises(ValueError, match="Reranking needs"):
        Settings(reranker="minilm")
    with pytest.raises(ValueError, match="diversity needs"):
        Settings(retrieval="embeddings", retrieval_diversity=0.2)
    path = tmp_path / "index.json"
    build_index(CORPUS, path)
    config = default_retrieval_config("tfidf", json.loads(path.read_bytes()), "baseline")
    assert config.reranker is None
    with pytest.raises(ValueError, match="enough candidates"):
        RetrievalConfig(
            implementation="adapter",
            version="1",
            backend="embeddings",
            limit=41,
            reranker={**reranker_metadata(), "candidates": 40},
        )
    encoder = Mock()
    monkeypatch.setattr("researchlens.retrieval.create_encoder", encoder)
    with pytest.raises(ValueError, match="incompatible"):
        load_retriever("embeddings", path, reranker_settings={"revision": "changed"})
    encoder.assert_not_called()
