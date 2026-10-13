"""Offline tier selection and startup contracts; no model downloads or searches."""

import json
import os
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from researchlens.api import create_app
from researchlens.config import RETRIEVAL_TIERS, ROOT, Settings
from researchlens.embedding_models import create_encoder, encoding_metadata
from researchlens.ingest import CORPUS, build_index, build_tier_index
from researchlens.memory import GIB, available_memory_gib
from researchlens.retrieval import EmbeddingRetriever
from researchlens.retrieval_tiers import load_configured_retriever


@pytest.fixture
def tier_setup(tmp_path, monkeypatch):
    loader = Mock(return_value=Mock())
    monkeypatch.setattr("researchlens.retrieval_tiers.load_retriever", loader)
    monkeypatch.setattr("researchlens.memory.available_memory_gib", lambda: 20)
    monkeypatch.setattr("researchlens.retrieval_tiers.available_memory_gib", lambda: 20)
    for name in RETRIEVAL_TIERS:
        (tmp_path / f"{name}.json").write_text("{}")
    return Settings(retrieval_tier="auto", tier_index_dir=tmp_path), loader


@pytest.mark.parametrize(
    ("available", "expected"),
    [
        (20, "full"),
        (10, "full"),
        (9.99, "standard"),
        (5, "standard"),
        (4.99, "light"),
        (2.5, "light"),
        (2.49, "minimal"),
        (0.25, "minimal"),
    ],
)
def test_auto_chooses_best_fitting_tier(tier_setup, monkeypatch, available, expected, caplog):
    settings, loader = tier_setup
    monkeypatch.setattr("researchlens.retrieval_tiers.available_memory_gib", lambda: available)
    with caplog.at_level("INFO"):
        retriever, active, tier = load_configured_retriever(settings)
    assert tier == expected
    assert retriever is loader.return_value
    spec = RETRIEVAL_TIERS[expected]
    assert active.retrieval == spec.backend
    assert active.embedding_model == spec.model
    assert active.index_path == settings.tier_index_dir / f"{expected}.json"
    assert active.answer_context_mode == "characters"
    assert active.answer_context_chars == spec.context_chars
    assert active.answer_context_candidates == 40
    assert loader.call_args.kwargs["expected_model"] == spec.model
    assert f"Selected retrieval tier {expected}" in caplog.text


def test_auto_skips_missing_artifacts(tier_setup):
    settings, loader = tier_setup
    for name in ("full", "standard"):
        (settings.tier_index_dir / f"{name}.json").unlink()
    assert load_configured_retriever(settings)[2] == "light"
    loader.assert_called_once()


@pytest.mark.parametrize("available", [0.24, 20])
def test_auto_fails_when_no_tier_is_usable(tier_setup, monkeypatch, available):
    settings, loader = tier_setup
    monkeypatch.setattr("researchlens.retrieval_tiers.available_memory_gib", lambda: available)
    if available == 20:
        for path in settings.tier_index_dir.iterdir():
            path.unlink()
    with pytest.raises(RuntimeError, match="No retrieval tier.*--tier minimal"):
        load_configured_retriever(settings)
    loader.assert_not_called()


@pytest.mark.parametrize("name", RETRIEVAL_TIERS)
def test_explicit_tier_fails_before_loading_when_ram_is_insufficient(tier_setup, monkeypatch, name):
    settings, loader = tier_setup
    settings = Settings(retrieval_tier=name, tier_index_dir=settings.tier_index_dir)
    required = RETRIEVAL_TIERS[name].required_gib
    monkeypatch.setattr("researchlens.retrieval_tiers.available_memory_gib", lambda: 0.1)
    with pytest.raises(RuntimeError) as error:
        load_configured_retriever(settings)
    assert f"tier {name}" in str(error.value)
    assert f"needs {required:.2f} GiB" in str(error.value)
    assert "available 0.10 GiB" in str(error.value)
    names = list(RETRIEVAL_TIERS)
    if name != "minimal":
        assert f"RETRIEVAL_TIER={names[names.index(name) + 1]}" in str(error.value)
    else:
        assert "Free physical RAM" in str(error.value)
    loader.assert_not_called()


def test_explicit_missing_artifact_has_build_command(tier_setup):
    settings, loader = tier_setup
    (settings.tier_index_dir / "full.json").unlink()
    with pytest.raises(RuntimeError, match="Missing.*full.*--tier full"):
        load_configured_retriever(
            Settings(retrieval_tier="full", tier_index_dir=settings.tier_index_dir)
        )
    loader.assert_not_called()


@pytest.mark.parametrize(
    "error", [MemoryError("OOM"), RuntimeError("allocator"), ValueError("stale")]
)
def test_auto_falls_back_after_load_failure(tier_setup, error, caplog):
    settings, loader = tier_setup
    loader.side_effect = [error, loader.return_value]
    assert load_configured_retriever(settings)[2] == "standard"
    assert [call.kwargs["expected_model"] for call in loader.call_args_list] == [
        "qwen3-4b",
        "bge-m3",
    ]
    assert "Skipping retrieval tier full after load failure" in caplog.text


@pytest.mark.parametrize("error", [MemoryError("OOM"), RuntimeError("allocator")])
def test_explicit_tier_never_silently_falls_back(tier_setup, error):
    settings, loader = tier_setup
    loader.side_effect = error
    with pytest.raises(RuntimeError, match="tier full failed"):
        load_configured_retriever(
            Settings(retrieval_tier="full", tier_index_dir=settings.tier_index_dir)
        )
    loader.assert_called_once()


@pytest.fixture
def clean_env(monkeypatch):
    for name in os.environ:
        if name.startswith(("RETRIEVAL_", "EMBEDDING_", "ANSWER_", "OPENAI_", "HYBRID_")):
            monkeypatch.delenv(name)


@pytest.mark.parametrize(
    "override",
    [
        "RETRIEVAL_BACKEND=tfidf",
        "RETRIEVAL_BACKEND=hybrid",
        "EMBEDDING_MODEL=qwen3-0.6b",
        "EMBEDDING_MODEL=minilm",
    ],
)
def test_explicit_environment_override_takes_precedence(tier_setup, tmp_path, clean_env, override):
    _, loader = tier_setup
    env = tmp_path / ".env"
    env.write_text(f"RETRIEVAL_TIER=full\n{override}\nRETRIEVAL_INDEX=data/custom.json\n")
    settings = Settings.from_env(env)
    _, active, tier = load_configured_retriever(settings)
    assert tier is None
    assert active is settings
    assert loader.call_args.args == (settings.retrieval, settings.index_path)
    assert loader.call_args.kwargs["expected_model"] == settings.embedding_model


def test_process_override_beats_tier_in_env_file(tier_setup, tmp_path, clean_env, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("RETRIEVAL_TIER=full\n")
    monkeypatch.setenv("RETRIEVAL_BACKEND", "tfidf")
    assert load_configured_retriever(Settings.from_env(env))[2] is None


def test_unset_tier_preserves_defaults(tier_setup, tmp_path, clean_env, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("")
    settings = Settings.from_env(env)
    monkeypatch.setattr(
        "researchlens.retrieval_tiers.available_memory_gib", Mock(side_effect=AssertionError)
    )
    _, active, tier = load_configured_retriever(settings)
    assert active is settings
    assert tier is None
    assert active.retrieval == "tfidf"
    assert active.embedding_model == "minilm"
    assert active.answer_context_mode == "passages"
    app = create_app(settings=settings)
    with TestClient(app) as client:
        assert app.state.retrieval_limit == 4
        assert client.get("/api/health").json()["retrieval_tier"] is None


def test_health_reports_actual_fallback_and_context(tier_setup):
    settings, loader = tier_setup
    loader.side_effect = [MemoryError(), loader.return_value]
    app = create_app(settings=settings)
    with TestClient(app) as client:
        assert client.get("/api/health").json()["retrieval_tier"] == "standard"
        assert app.state.retrieval_limit == 40


def test_available_memory_uses_available_not_total_or_swap(monkeypatch):
    monkeypatch.setattr(
        "researchlens.memory.psutil.virtual_memory",
        lambda: SimpleNamespace(available=3 * GIB, total=64 * GIB, free=GIB),
    )
    assert available_memory_gib() == 3


@pytest.mark.parametrize("model", ["minilm", "bge-m3", "qwen3-0.6b", "qwen3-4b"])
def test_ram_check_precedes_encoder_construction(monkeypatch, model):
    monkeypatch.setattr("researchlens.memory.available_memory_gib", lambda: 0.1)
    local, torch = Mock(), Mock()
    monkeypatch.setattr("researchlens.embedding_models.LocalEncoder", local)
    monkeypatch.setattr("researchlens.embedding_models.TorchEncoder", torch)
    with pytest.raises(RuntimeError, match="needs.*available 0.10 GiB.*RETRIEVAL_TIER="):
        create_encoder(model)
    local.assert_not_called()
    torch.assert_not_called()


@pytest.mark.parametrize("tier", RETRIEVAL_TIERS)
def test_ingest_helper_uses_tier_model_and_distinct_artifact(tmp_path, monkeypatch, tier):
    spec = RETRIEVAL_TIERS[tier]
    factory = Mock()
    if spec.backend == "embeddings":
        encoding = encoding_metadata(spec.model)
        encoder = factory.return_value
        encoder.encoding = encoding

        def encode(texts):
            vectors = np.zeros((len(texts), encoding["dimensions"]), dtype=np.float32)
            vectors[:, 0] = 1
            return vectors

        encoder.encode.side_effect = encode
    monkeypatch.setattr("researchlens.embedding_models.create_encoder", factory)
    path = build_tier_index(tier, CORPUS, tmp_path)
    assert path == tmp_path / f"{tier}.json"
    saved = json.loads(path.read_text())
    baseline = tmp_path / "baseline.json"
    build_index(CORPUS, baseline)
    assert saved["passages"] == json.loads(baseline.read_text())["passages"]
    if spec.backend == "embeddings":
        factory.assert_called_once()
        assert factory.call_args.args == (spec.model,)
        assert saved["embeddings"]["encoding"] == encoding
        # A tier cannot silently query vectors from another model.
        loader = Mock()
        monkeypatch.setattr("researchlens.retrieval.create_encoder", loader)
        with pytest.raises(ValueError, match="configuration/artifact mismatch"):
            EmbeddingRetriever.from_path(path, expected_model="minilm")
        loader.assert_not_called()
    else:
        factory.assert_not_called()
        assert "embeddings" not in saved


@pytest.mark.parametrize("error", [MemoryError(), RuntimeError("allocation failure")])
def test_model_load_failures_have_memory_and_next_tier_message(tmp_path, monkeypatch, error):
    encoding = encoding_metadata()
    vectors = np.zeros((1, encoding["dimensions"]), dtype=np.float32)
    vectors[:, 0] = 1
    encoder = Mock(encoding=encoding)
    encoder.encode.side_effect = lambda texts: np.repeat(vectors, len(texts), axis=0)
    monkeypatch.setattr("researchlens.embedding_models.create_encoder", Mock(return_value=encoder))
    path = tmp_path / "index.json"
    build_index(CORPUS, path, retrieval="embeddings")
    monkeypatch.setattr("researchlens.retrieval.create_encoder", Mock(side_effect=error))
    monkeypatch.setattr("researchlens.memory.available_memory_gib", lambda: 1.25)
    with pytest.raises(RuntimeError, match="minilm.*needs at least 0.50 GiB.*available 1.25 GiB"):
        EmbeddingRetriever.from_path(path)


def test_invalid_tier_is_rejected():
    with pytest.raises(ValueError, match="RETRIEVAL_TIER must be"):
        Settings(retrieval_tier="unknown")


def test_minimal_ingest_cli_and_real_auto_startup(tmp_path, monkeypatch, clean_env):
    environment = {
        **os.environ,
        "RETRIEVAL_TIER_INDEX_DIR": str(tmp_path),
        "RETRIEVAL_CORPUS": str(CORPUS),
    }
    result = subprocess.run(
        [sys.executable, "-m", "researchlens.ingest", "--tier", "minimal"],
        cwd=ROOT / "backend",
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "tier minimal" in result.stdout
    monkeypatch.setattr("researchlens.retrieval_tiers.available_memory_gib", lambda: 20)
    settings = Settings(retrieval_tier="auto", tier_index_dir=tmp_path, corpus_path=CORPUS)
    app = create_app(settings=settings)
    with TestClient(app) as client:
        assert client.get("/api/health").json()["retrieval_tier"] == "minimal"
        response = client.post("/api/ask", json={"question": "dust"})
        assert response.status_code == 200
        assert response.json()["passages"]


def test_tier_ingest_cli_rejects_model_override(tmp_path, clean_env):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "researchlens.ingest",
            "--tier",
            "full",
            "--embedding-model",
            "minilm",
            "--tier-index-dir",
            str(tmp_path),
        ],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "--tier uses fixed model/runtime settings" in result.stderr
    assert not (tmp_path / "full.json").exists()
