"""Build a deterministic passage artifact from UTF-8 JSON documents."""

import argparse
import hashlib
import json
from pathlib import Path

from pydantic import TypeAdapter

from researchlens.models import Document, Passage

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "sample_documents.json"
TECHNICAL_CORPUS = ROOT / "data" / "technical" / "documents.json"
INDEX = ROOT / "data" / "index.json"


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


def build_index(source: Path = CORPUS, destination: Path = INDEX) -> None:
    raw = source.read_bytes()
    documents = TypeAdapter(list[Document]).validate_json(raw)
    passages = chunk_documents(documents)
    if not passages:
        raise ValueError("The corpus contains no text")
    artifact = {
        "schema_version": 1,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "chunking": {"method": "paragraph-word-windows", "max_words": 180},
        "passages": [passage.model_dump() for passage in passages],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", choices=("technical", "sample"), default="technical")
    args = parser.parse_args()
    build_index(TECHNICAL_CORPUS if args.corpus == "technical" else CORPUS)
    print(f"Built {INDEX}")
