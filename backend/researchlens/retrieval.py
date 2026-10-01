import hashlib
import math
from pathlib import Path
from typing import Protocol

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from researchlens.artifacts import load_artifact
from researchlens.embedding_models import create_encoder, model_for_encoding
from researchlens.embeddings import ENCODING, Encoder, validate_vectors
from researchlens.ingest import CHUNKING
from researchlens.models import Passage, SearchHit


class PassageRetriever(Protocol):
    def search(self, question: str, limit: int = 4) -> list[SearchHit]: ...


def _rebuild_error(reason: str, backend: str) -> ValueError:
    dependencies = (
        "Enable the selected model's dependencies first: uv sync --locked --extra embeddings "
        "for MiniLM, or uv sync --locked --extra embedding-models for BGE/Qwen. "
        if backend in ("embeddings", "hybrid")
        else ""
    )
    return ValueError(
        f"{reason}. {dependencies}"
        "Rebuild with the configured RETRIEVAL_CORPUS, RETRIEVAL_INDEX and EMBEDDING_MODEL: "
        "uv run --no-sync --directory backend python -m researchlens.ingest "
        f"--retrieval {backend} (or supply --source and --destination for custom paths)."
    )


def _load_artifact(path: Path, source: Path | None) -> tuple[dict, list[Passage]]:
    artifact, passages = load_artifact(path, source=source)
    if artifact["chunking"] != CHUNKING:
        raise ValueError("Incompatible chunking metadata")
    return artifact, passages


class TfidfRetriever:
    """Lexical preview using word TF-IDF and cosine similarity.

    A positive score indicates word overlap, not sufficient evidence to answer.
    Refit deterministically from the saved passages when the server starts.
    """

    def __init__(self, passages: list[Passage]) -> None:
        self.passages = passages
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([passage.text for passage in passages])

    @classmethod
    def from_path(cls, path: Path, *, source: Path | None = None) -> "TfidfRetriever":
        try:
            _, passages = _load_artifact(path, source)
            return cls(passages)
        except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
            raise _rebuild_error("Missing, stale or incompatible TF-IDF artifact", "tfidf") from exc

    def search(self, question: str, limit: int = 4) -> list[SearchHit]:
        if limit < 1:
            raise ValueError("limit must be positive")
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.matrix).ravel()
        ranked = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        return [
            SearchHit(**self.passages[index].model_dump(), score=float(scores[index]))
            for index in ranked[:limit]
            if scores[index] > 0
        ]


# Keep existing constructor, from_path and search callers working as the lexical baseline.
Retriever = TfidfRetriever


class EmbeddingRetriever:
    """Exact cosine ranking in memory; nearest neighbors are not evidence of answerability."""

    def __init__(
        self,
        passages: list[Passage],
        vectors: np.ndarray,
        encoder: Encoder,
        encoding: dict = ENCODING,
    ) -> None:
        self.passages = passages
        self.encoding = encoding
        self.matrix = validate_vectors(vectors, len(passages), encoding["dimensions"])
        self.encoder = encoder
        self._diagnostics = None
        self._artifact = None

    @classmethod
    def from_path(cls, path: Path, *, source: Path | None = None) -> "EmbeddingRetriever":
        try:
            artifact, passages = _load_artifact(path, source)
            if artifact["schema_version"] != 2:
                raise ValueError("Embeddings require schema version 2")
            saved = artifact["embeddings"]
            encoding = saved["encoding"]
            model = model_for_encoding(encoding)
            if saved["passage_ids"] != [passage.id for passage in passages]:
                raise ValueError("Embedding rows do not match passage identities")
            vectors = validate_vectors(saved["vectors"], len(passages), encoding["dimensions"])
            if (
                saved["vectors_sha256"]
                != hashlib.sha256(vectors.astype("<f4").tobytes()).hexdigest()
            ):
                raise ValueError("Embedding vector checksum mismatch")
        except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
            raise _rebuild_error(
                "Missing, stale or incompatible embedding artifact", "embeddings"
            ) from exc
        # Startup is cache-only. Only explicit ingestion can download model files.
        encoder = create_encoder(
            model,
            max_tokens=encoding["max_tokens"],
            batch_size=encoding["batch_size"],
            threads=encoding["intra_op_threads"],
            precision=encoding["precision"],
        )
        retriever = cls(passages, vectors, encoder, encoding)
        retriever._artifact = artifact
        return retriever

    def get_encoding_diagnostics(self) -> dict | None:
        from researchlens.encoding_diagnostics import diagnostic_artifact

        measure = getattr(self.encoder, "measure_documents", None)
        if self._artifact is None or not callable(measure):
            return None
        if self._diagnostics is None:
            rows = measure([passage.text for passage in self.passages])
            self._diagnostics = diagnostic_artifact(self._artifact, rows)
        return self._diagnostics

    def search(self, question: str, limit: int = 4) -> list[SearchHit]:
        if limit < 1:
            raise ValueError("limit must be positive")
        if not question.strip():
            return []
        query_text = self.encoding["query_prefix"] + question
        query = validate_vectors(self.encoder.encode([query_text]), 1, self.encoding["dimensions"])[
            0
        ]
        scores = np.clip(self.matrix @ query, -1.0, 1.0)
        ranked = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        return [
            SearchHit(**self.passages[index].model_dump(), score=float(scores[index]))
            for index in ranked[:limit]
        ]


HYBRID_DEFAULTS = {
    "lexical_candidates": 20,
    "embedding_candidates": 20,
    "fusion_method": "rrf",
    "rrf_k": 60,
    "lexical_weight": 1.0,
    "embedding_weight": 1.0,
}


class HybridRetriever:
    """Reciprocal rank fusion of lexical and dense candidates, deduplicated by passage ID."""

    def __init__(
        self,
        embeddings: EmbeddingRetriever,
        *,
        lexical_candidates: int = 20,
        embedding_candidates: int = 20,
        fusion_method: str = "rrf",
        rrf_k: int = 60,
        lexical_weight: float = 1.0,
        embedding_weight: float = 1.0,
    ) -> None:
        if min(lexical_candidates, embedding_candidates, rrf_k) < 1 or fusion_method != "rrf":
            raise ValueError(
                "Hybrid retrieval requires positive candidate counts/RRF k and rrf fusion"
            )
        if (
            any(
                not math.isfinite(weight) or not 0 <= weight <= 1
                for weight in (lexical_weight, embedding_weight)
            )
            or lexical_weight + embedding_weight == 0
        ):
            raise ValueError("Fusion weights must be finite, within 0..1 and not both zero")
        self.embeddings = embeddings
        self.lexical = TfidfRetriever(embeddings.passages)
        self.passages = embeddings.passages
        self.retrieval_settings = {
            "lexical_candidates": lexical_candidates,
            "embedding_candidates": embedding_candidates,
            "fusion_method": fusion_method,
            "rrf_k": rrf_k,
            "lexical_weight": lexical_weight,
            "embedding_weight": embedding_weight,
        }

    def get_encoding_diagnostics(self) -> dict | None:
        return self.embeddings.get_encoding_diagnostics()

    def search(self, question: str, limit: int = 4) -> list[SearchHit]:
        if limit < 1:
            raise ValueError("limit must be positive")
        scores: dict[str, float] = {}
        for retriever, count, weight in (
            (
                self.lexical,
                self.retrieval_settings["lexical_candidates"],
                self.retrieval_settings["lexical_weight"],
            ),
            (
                self.embeddings,
                self.retrieval_settings["embedding_candidates"],
                self.retrieval_settings["embedding_weight"],
            ),
        ):
            if weight == 0:
                continue
            for rank, hit in enumerate(retriever.search(question, count), start=1):
                scores[hit.id] = scores.get(hit.id, 0.0) + weight / (
                    self.retrieval_settings["rrf_k"] + rank
                )
        ranked = sorted(
            range(len(self.passages)), key=lambda i: (-scores.get(self.passages[i].id, 0), i)
        )
        return [
            SearchHit(**self.passages[i].model_dump(), score=scores[self.passages[i].id])
            for i in ranked
            if self.passages[i].id in scores
        ][:limit]


def load_retriever(
    backend: str,
    path: Path,
    *,
    source: Path | None = None,
    expected_model: str | None = None,
    hybrid_settings: dict | None = None,
    reranker_settings: dict | None = None,
) -> PassageRetriever:
    reranking = None
    if reranker_settings:
        from researchlens.reranking import LocalReranker, RerankedRetriever, reranker_metadata

        settings = dict(reranker_settings)
        candidates = settings.pop("candidates", 40)
        diversity = settings.pop("diversity", 0.0)
        if settings != reranker_metadata():
            raise ValueError("Reranker model, revision or runtime settings are incompatible")
        if not 1 <= candidates <= 100 or not math.isfinite(diversity) or not 0 <= diversity <= 1:
            raise ValueError("Invalid reranking candidate count or diversity")
        reranking = candidates, diversity
    if backend == "tfidf":
        if reranker_settings:
            raise ValueError("This reranking integration requires embeddings or hybrid retrieval")
        return TfidfRetriever.from_path(path, source=source)
    if backend in ("embeddings", "hybrid"):
        # Check configured model before loading weights; evaluation derives it from the artifact.
        if expected_model is not None:
            try:
                artifact, _ = _load_artifact(path, source)
                if model_for_encoding(artifact["embeddings"]["encoding"]) != expected_model:
                    raise ValueError("Configured embedding model differs from saved vectors")
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
                raise _rebuild_error("Embedding configuration/artifact mismatch", backend) from exc
        embeddings = EmbeddingRetriever.from_path(path, source=source)
        retriever = (
            HybridRetriever(embeddings, **(hybrid_settings or {}))
            if backend == "hybrid"
            else embeddings
        )
        if reranker_settings:
            candidates, diversity = reranking
            retriever = RerankedRetriever(
                retriever,
                LocalReranker(),
                candidates=candidates,
                diversity=diversity,
            )
        return retriever
    raise ValueError("RETRIEVAL_BACKEND must be tfidf, embeddings or hybrid")
