"""Shared passage/artifact validation, independent of any embedding implementation."""

import hashlib
import json
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from researchlens.ingest import chunk_documents
from researchlens.models import Document, Passage


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


class EncodingMetadata(BaseModel):
    """Allowlisted metadata: extend this contract rather than dump model/client settings."""

    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1)
    revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    dimensions: int = Field(ge=1)
    max_tokens: int = Field(ge=1)
    pooling: str = Field(min_length=1)
    normalization: str = Field(min_length=1)
    query_prefix: str
    document_prefix: str
    text: str = Field(min_length=1)
    encoding_version: int = Field(ge=1)
    weights: str | None = None
    tokenizer: str | None = None
    runtime: str | None = None
    runtime_version: str | None = None
    backend: str | None = None
    device: str | None = None
    precision: str | None = None
    quantization: str | None = None
    truncation: str | None = None
    batch_size: int | None = Field(default=None, ge=1)
    intra_op_threads: int | None = Field(default=None, ge=1)
    inter_op_threads: int | None = Field(default=None, ge=1)


class ChunkingMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["paragraph-word-windows"]
    max_words: int = Field(ge=1, strict=True)


def validate_passage_artifact(artifact: dict) -> list[Passage]:
    """Validate schemas 1/2, including vector row identity/checksum for schema 2.

    Encoding compatibility with an actual query encoder belongs to its retrieval
    adapter. This validator never loads weights, encodes text or downloads models.
    """
    if type(artifact.get("schema_version")) is not int or artifact["schema_version"] not in (1, 2):
        raise ValueError("Unsupported passage artifact schema")
    if not isinstance(artifact.get("source_sha256"), str) or not (
        len(artifact["source_sha256"]) == 64
        and all(c in "0123456789abcdef" for c in artifact["source_sha256"])
    ):
        raise ValueError("Invalid corpus checksum")
    ChunkingMetadata.model_validate(artifact["chunking"])
    passages = TypeAdapter(list[Passage]).validate_python(artifact["passages"])
    if not passages or len({p.id for p in passages}) != len(passages):
        raise ValueError("Passage artifact must contain unique passages")
    if "embeddings" in artifact:
        if artifact["schema_version"] != 2:
            raise ValueError("Embedding artifacts require schema 2")
        saved = artifact["embeddings"]
        encoding = EncodingMetadata.model_validate(saved["encoding"])
        if saved["passage_ids"] != [p.id for p in passages]:
            raise ValueError("Embedding rows do not match passage identities")
        vectors = np.asarray(saved["vectors"], dtype=np.float32)
        if vectors.shape != (len(passages), encoding.dimensions) or not np.isfinite(vectors).all():
            raise ValueError("Invalid embedding dimensions or values")
        norms = np.linalg.norm(vectors, axis=1)
        if np.any(norms == 0) or (
            encoding.normalization == "l2" and not np.allclose(norms, 1.0, atol=1e-4)
        ):
            raise ValueError("Invalid embedding normalization")
        if saved["vectors_sha256"] != hashlib.sha256(vectors.astype("<f4").tobytes()).hexdigest():
            raise ValueError("Embedding vector checksum mismatch")
    return passages


def passage_identity(artifact: dict, passages: list[Passage]) -> str:
    """Corpus, chunking and ordered full passage/source metadata, excluding vectors."""
    return canonical_hash(
        {
            "source_sha256": artifact["source_sha256"],
            "chunking": artifact["chunking"],
            "passages": [p.model_dump(mode="json") for p in passages],
        }
    )


def load_artifact(path: Path, *, source: Path | None = None) -> tuple[dict, list[Passage]]:
    artifact = json.loads(path.read_bytes())
    passages = validate_passage_artifact(artifact)
    if source is not None:
        raw = source.read_bytes()
        if artifact["source_sha256"] != hashlib.sha256(raw).hexdigest():
            raise ValueError("Corpus changed since ingestion")
        documents = TypeAdapter(list[Document]).validate_json(raw)
        expected = chunk_documents(documents, max_words=artifact["chunking"]["max_words"])
        if passages != expected:
            raise ValueError("Passages do not match corpus text, source metadata or chunking")
    return artifact, passages
