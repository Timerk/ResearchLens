"""Measure canonical document visibility with the encoder's actual tokenizer."""

import hashlib

from researchlens.artifacts import canonical_hash


def measurement(text: str, input_tokens: int, encoded_tokens: int, end: int) -> dict:
    # An untruncated input retains whitespace as well as token characters.
    end = len(text) if input_tokens == encoded_tokens else min(end, len(text))
    return {
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "input_tokens": input_tokens,
        "encoded_tokens": encoded_tokens,
        "truncated": end < len(text),
        "retained_ranges": [{"start": 0, "end": end}] if end else [],
    }


def diagnostic_artifact(artifact: dict, rows: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "artifact_sha256": canonical_hash(artifact),
        "encoding_sha256": canonical_hash(artifact["embeddings"]["encoding"]),
        "token_count_scope": "encoder-input-including-instructions-and-special-tokens",
        "passages": [
            {"passage_id": passage["id"], **row}
            for passage, row in zip(artifact["passages"], rows, strict=True)
        ],
    }
