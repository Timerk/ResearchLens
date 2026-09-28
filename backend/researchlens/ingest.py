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
) -> None:
    if retrieval not in ("tfidf", "embeddings"):
        raise ValueError("retrieval must be tfidf or embeddings")
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
    if retrieval == "embeddings":
        from researchlens.embeddings import ENCODING, LocalEncoder, validate_vectors

        vectors = validate_vectors(
            LocalEncoder(download=True).encode([passage.text for passage in passages]),
            len(passages),
        )
        artifact["embeddings"] = {
            "encoding": ENCODING,
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


if __name__ == "__main__":
    from researchlens.config import retrieval_environment

    defaults = retrieval_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", choices=("technical", "sample"))
    parser.add_argument(
        "--retrieval", choices=("tfidf", "embeddings"), default=defaults["retrieval"]
    )
    parser.add_argument("--source", type=Path, default=defaults["corpus_path"])
    parser.add_argument("--destination", type=Path, default=defaults["index_path"])
    args = parser.parse_args()
    source = (
        TECHNICAL_CORPUS if args.corpus == "technical" else CORPUS
    ) if args.corpus else args.source
    build_index(source, args.destination, retrieval=args.retrieval)
    print(f"Built {args.destination} ({args.retrieval})")
