"""Build a deterministic passage artifact from UTF-8 JSON documents.

This extractor accepts text only. Optional embeddings are computed before publication.
"""

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

from pydantic import TypeAdapter

from researchlens.models import Document, Passage

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "sample_documents.json"
TECHNICAL_CORPUS = ROOT / "data" / "technical" / "documents.json"
INDEX = ROOT / "data" / "index.json"
CHUNKING = {"method": "paragraph-word-windows", "max_words": 180}


def chunk_documents(documents: list[Document], max_words: int = 180) -> list[Passage]:
    if max_words < 1:
        raise ValueError("max_words must be positive")
    if len({document.id for document in documents}) != len(documents):
        raise ValueError("Document IDs must be unique")
    passages: list[Passage] = []
    for document in documents:
        for paragraph, text in enumerate(document.text.split("\n\n"), start=1):
            source = (
                document.paragraph_sources[paragraph - 1] if document.paragraph_sources else None
            )
            words = text.split()
            for offset in range(0, len(words), max_words):
                passages.append(
                    Passage(
                        id=f"{document.id}:p{paragraph}:w{offset}",
                        document_id=document.id,
                        title=document.title,
                        source_url=document.source_url,
                        license=document.license,
                        kind=document.kind,
                        paragraph=paragraph,
                        text=" ".join(words[offset : offset + max_words]),
                        attribution=document.attribution,
                        source_section=source.section if source else None,
                        source_locator=source.locator if source else None,
                    )
                )
    return passages


def build_index(
    source: Path = CORPUS,
    destination: Path = INDEX,
    *,
    retrieval: str = "tfidf",
    embedding_model: str = "minilm",
    max_tokens: int | None = None,
    batch_size: int | None = None,
    threads: int | None = None,
    precision: str | None = None,
) -> None:
    if retrieval not in ("tfidf", "embeddings", "hybrid"):
        raise ValueError("retrieval must be tfidf, embeddings or hybrid")
    raw = source.read_bytes()
    documents = TypeAdapter(list[Document]).validate_json(raw)
    passages = chunk_documents(documents)
    if not passages:
        raise ValueError("The corpus contains no text")
    artifact = {
        "schema_version": 2,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "chunking": CHUNKING,
        "passages": [passage.model_dump() for passage in passages],
    }
    if retrieval in ("embeddings", "hybrid"):
        from researchlens.embedding_models import create_encoder
        from researchlens.embeddings import validate_vectors

        encoder = create_encoder(
            embedding_model,
            download=True,
            max_tokens=max_tokens,
            batch_size=batch_size,
            threads=threads,
            precision=precision,
        )
        vectors = validate_vectors(
            encoder.encode([passage.text for passage in passages]),
            len(passages),
            encoder.encoding["dimensions"],
        )
        artifact["embeddings"] = {
            "encoding": encoder.encoding,
            "passage_ids": [passage.id for passage in passages],
            "vectors": vectors.tolist(),
            "vectors_sha256": hashlib.sha256(vectors.astype("<f4").tobytes()).hexdigest(),
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Publish a single coherent artifact; failures leave the previous index intact.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(artifact, indent=2, allow_nan=False) + "\n")
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build_tier_index(
    tier: str,
    source: Path = TECHNICAL_CORPUS,
    index_dir: Path | None = None,
) -> Path:
    """Encode the unchanged corpus with the tier's pinned model and runtime defaults."""
    from researchlens.config import RETRIEVAL_TIERS, ROOT

    if tier not in RETRIEVAL_TIERS:
        raise ValueError(f"Unknown retrieval tier: {tier}")
    spec = RETRIEVAL_TIERS[tier]
    destination = (index_dir if index_dir is not None else ROOT / "data" / "tiers") / f"{tier}.json"
    build_index(source, destination, retrieval=spec.backend, embedding_model=spec.model)
    return destination


if __name__ == "__main__":
    from researchlens.config import retrieval_environment

    defaults = retrieval_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=("full", "standard", "light", "minimal"))
    parser.add_argument("--tier-index-dir", type=Path)
    parser.add_argument("--corpus", choices=("technical", "sample"))
    parser.add_argument("--retrieval", choices=("tfidf", "embeddings", "hybrid"))
    parser.add_argument("--embedding-model")
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--threads", type=int)
    parser.add_argument("--precision", choices=("float32", "bfloat16"))
    parser.add_argument("--source", type=Path, default=defaults["corpus_path"])
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    source = (
        (TECHNICAL_CORPUS if args.corpus == "technical" else CORPUS) if args.corpus else args.source
    )
    if args.tier:
        if any(
            value is not None
            for value in (
                args.retrieval,
                args.embedding_model,
                args.destination,
                args.max_tokens,
                args.batch_size,
                args.threads,
                args.precision,
            )
        ):
            parser.error("--tier uses fixed model/runtime settings; use --tier-index-dir for paths")
        # Read the tier directory without requiring answer-provider credentials.
        from dotenv import dotenv_values

        from researchlens.config import ENV_FILE

        values = {**dotenv_values(ENV_FILE), **os.environ}
        directory = (
            args.tier_index_dir
            or ROOT / (values.get("RETRIEVAL_TIER_INDEX_DIR") or "data/tiers").strip()
        )
        destination = build_tier_index(args.tier, source, directory)
        print(f"Built {destination} (tier {args.tier})")
    else:
        if args.tier_index_dir is not None:
            parser.error("--tier-index-dir requires --tier")
        destination = args.destination or defaults["index_path"]
        retrieval = args.retrieval or defaults["retrieval"]
        build_index(
            source,
            destination,
            retrieval=retrieval,
            embedding_model=args.embedding_model or defaults["embedding_model"],
            max_tokens=args.max_tokens,
            batch_size=args.batch_size,
            threads=args.threads,
            precision=args.precision,
        )
        print(f"Built {destination} ({retrieval})")
