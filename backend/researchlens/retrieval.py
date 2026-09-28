import hashlib
from pathlib import Path
from typing import Protocol

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from researchlens.artifacts import load_artifact
from researchlens.embeddings import ENCODING, Encoder, LocalEncoder, validate_vectors
from researchlens.ingest import CHUNKING, CORPUS
from researchlens.models import Passage, SearchHit


class PassageRetriever(Protocol):
    def search(self, question: str, limit: int = 4) -> list[SearchHit]: ...


def _rebuild_error(reason: str, backend: str) -> ValueError:
    extra = "--extra embeddings " if backend == "embeddings" else ""
    return ValueError(
        f"{reason}. Rebuild with the configured RETRIEVAL_CORPUS and RETRIEVAL_INDEX: "
        f"uv run {extra}--directory backend python -m researchlens.ingest "
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
    def from_path(cls, path: Path, *, source: Path = CORPUS) -> "TfidfRetriever":
        try:
            _, passages = _load_artifact(path, source)
            return cls(passages)
        except (OSError, ValueError, KeyError, TypeError) as exc:
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

    def __init__(self, passages: list[Passage], vectors: np.ndarray, encoder: Encoder) -> None:
        self.passages = passages
        self.matrix = validate_vectors(vectors, len(passages))
        self.encoder = encoder

    @classmethod
    def from_path(cls, path: Path, *, source: Path = CORPUS) -> "EmbeddingRetriever":
        try:
            artifact, passages = _load_artifact(path, source)
            if artifact["schema_version"] != 2:
                raise ValueError("Embeddings require schema version 2")
            saved = artifact["embeddings"]
            if saved["encoding"] != ENCODING:
                raise ValueError("Incompatible embedding model, revision or encoding")
            if saved["passage_ids"] != [passage.id for passage in passages]:
                raise ValueError("Embedding rows do not match passage identities")
            vectors = validate_vectors(saved["vectors"], len(passages))
            if (
                saved["vectors_sha256"]
                != hashlib.sha256(vectors.astype("<f4").tobytes()).hexdigest()
            ):
                raise ValueError("Embedding vector checksum mismatch")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise _rebuild_error(
                "Missing, stale or incompatible embedding artifact", "embeddings"
            ) from exc
        # Startup is cache-only. Only explicit ingestion can download model files.
        return cls(passages, vectors, LocalEncoder())

    def search(self, question: str, limit: int = 4) -> list[SearchHit]:
        if limit < 1:
            raise ValueError("limit must be positive")
        if not question.strip():
            return []
        query = validate_vectors(self.encoder.encode([question]), 1)[0]
        scores = np.clip(self.matrix @ query, -1.0, 1.0)
        ranked = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        return [
            SearchHit(**self.passages[index].model_dump(), score=float(scores[index]))
            for index in ranked[:limit]
        ]


def load_retriever(backend: str, path: Path, *, source: Path | None = None) -> PassageRetriever:
    if backend == "tfidf":
        return TfidfRetriever.from_path(path, source=source)
    if backend == "embeddings":
        return EmbeddingRetriever.from_path(path, source=source)
    raise ValueError("RETRIEVAL_BACKEND must be tfidf or embeddings")
