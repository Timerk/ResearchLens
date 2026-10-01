import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"


def retrieval_environment(path: Path = ENV_FILE) -> dict:
    """Ingestion reads retrieval settings without requiring answer-provider credentials.

    Relative environment paths are repository-relative, independent of the launch directory.
    """
    values = {**dotenv_values(path), **os.environ}

    def configured_path(name: str, default: str) -> Path:
        selected = Path((values.get(name) or default).strip())
        return selected if selected.is_absolute() else ROOT / selected

    return {
        "retrieval": (values.get("RETRIEVAL_BACKEND") or "tfidf").strip(),
        "embedding_model": (values.get("EMBEDDING_MODEL") or "minilm").strip(),
        "index_path": configured_path("RETRIEVAL_INDEX", "data/index.json"),
        "corpus_path": configured_path("RETRIEVAL_CORPUS", "data/technical/documents.json"),
    }


@dataclass(frozen=True)
class Settings:
    provider: Literal["local", "openai"] = "local"
    api_key: str = field(default="", repr=False)
    model: str = "gpt-6-luna"
    retrieval: Literal["tfidf", "embeddings", "hybrid"] = "tfidf"
    embedding_model: str = "minilm"
    index_path: Path = ROOT / "data" / "index.json"
    corpus_path: Path = ROOT / "data" / "technical" / "documents.json"
    reranker: Literal["none", "minilm"] = "none"
    reranking_candidates: int = 40
    retrieval_diversity: float = 0.0
    hybrid_lexical_weight: float = 1.0
    hybrid_embedding_weight: float = 1.0
    hybrid_candidates: int = 20

    def __post_init__(self) -> None:
        if self.retrieval not in ("tfidf", "embeddings", "hybrid"):
            raise ValueError("RETRIEVAL_BACKEND must be tfidf, embeddings or hybrid")
        if self.embedding_model not in ("minilm", "bge-m3", "qwen3-0.6b", "qwen3-4b"):
            raise ValueError("EMBEDDING_MODEL must be minilm, bge-m3, qwen3-0.6b or qwen3-4b")
        if self.provider not in ("local", "openai"):
            raise ValueError("ANSWER_PROVIDER must be local or openai")
        if self.provider == "openai" and (not self.api_key.strip() or not self.model.strip()):
            raise ValueError("OpenAI mode requires OPENAI_API_KEY and OPENAI_MODEL")
        if self.reranker not in ("none", "minilm") or not 4 <= self.reranking_candidates <= 100:
            raise ValueError(
                "Select RETRIEVAL_RERANKER none/minilm and 4..100 reranking candidates"
            )
        weights = (self.hybrid_lexical_weight, self.hybrid_embedding_weight)
        if (
            any(not math.isfinite(w) or not 0 <= w <= 1 for w in weights)
            or sum(weights) == 0
            or not 1 <= self.hybrid_candidates <= 100
        ):
            raise ValueError(
                "Hybrid weights need finite 0..1 values, a positive sum and 1..100 candidates"
            )
        if not math.isfinite(self.retrieval_diversity) or not 0 <= self.retrieval_diversity <= 1:
            raise ValueError("RETRIEVAL_DIVERSITY must be finite and within 0..1")
        if (self.reranker != "none" and self.retrieval == "tfidf") or (
            self.retrieval_diversity and self.reranker == "none"
        ):
            raise ValueError(
                "Reranking needs embeddings/hybrid; diversity needs an enabled reranker"
            )

    def retriever_options(self) -> dict:
        options = {}
        if self.retrieval == "hybrid":
            options["hybrid_settings"] = {
                "lexical_candidates": self.hybrid_candidates,
                "embedding_candidates": self.hybrid_candidates,
                "lexical_weight": self.hybrid_lexical_weight,
                "embedding_weight": self.hybrid_embedding_weight,
            }
        if self.reranker != "none":
            from researchlens.reranking import reranker_metadata

            options["reranker_settings"] = {
                **reranker_metadata(),
                "candidates": self.reranking_candidates,
                "diversity": self.retrieval_diversity,
            }
        return options

    @classmethod
    def from_env(cls, path: Path = ENV_FILE) -> "Settings":
        # Process settings take precedence; reading a file does not modify global environment.
        values = {**dotenv_values(path), **os.environ}
        try:
            retrieval_options = {
                "reranker": (values.get("RETRIEVAL_RERANKER") or "none").strip(),
                "reranking_candidates": int(values.get("RETRIEVAL_RERANK_CANDIDATES") or "40"),
                "retrieval_diversity": float(values.get("RETRIEVAL_DIVERSITY") or "0"),
                "hybrid_lexical_weight": float(values.get("HYBRID_LEXICAL_WEIGHT") or "1"),
                "hybrid_embedding_weight": float(values.get("HYBRID_EMBEDDING_WEIGHT") or "1"),
                "hybrid_candidates": int(values.get("HYBRID_CANDIDATES") or "20"),
            }
        except ValueError:
            raise ValueError("Invalid numeric retrieval settings; check .env.example") from None
        return cls(
            provider=(values.get("ANSWER_PROVIDER") or "local").strip(),
            api_key=(values.get("OPENAI_API_KEY") or "").strip(),
            model=(values.get("OPENAI_MODEL", "gpt-6-luna") or "").strip(),
            **retrieval_environment(path),
            **retrieval_options,
        )
