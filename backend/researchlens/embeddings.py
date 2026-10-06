"""Pinned local CPU encoder. Importing this module never downloads model files."""

from typing import Protocol

import numpy as np

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
DIMENSIONS = 384
ENCODING = {
    "model": MODEL,
    "revision": REVISION,
    "weights": "onnx/model.onnx",
    "tokenizer": "tokenizer.json",
    "dimensions": DIMENSIONS,
    "max_tokens": 256,
    "pooling": "attention-masked-mean",
    "normalization": "l2",
    "query_prefix": "",
    "document_prefix": "",
    "text": "passage-text-only",
    "encoding_version": 1,
}


class Encoder(Protocol):
    encoding: dict

    def encode(self, texts: list[str]) -> np.ndarray: ...


class LocalEncoder:
    """Reuse one tokenizer and ONNX session; queries and passages use identical encoding."""

    def __init__(
        self,
        *,
        download: bool = False,
        max_tokens: int = 256,
        batch_size: int = 32,
        threads: int = 2,
    ) -> None:
        self.batch_size = batch_size
        try:
            import onnxruntime as ort
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer
        except ImportError:
            raise ValueError(
                "Local embedding dependencies are missing. Run: "
                "uv sync --locked --extra embeddings --python 3.13"
            ) from None

        try:
            paths = {
                key: hf_hub_download(
                    repo_id=MODEL,
                    revision=REVISION,
                    filename=ENCODING[key],
                    local_files_only=not download,
                    token=False,
                )
                for key in ("weights", "tokenizer")
            }
            self.tokenizer = Tokenizer.from_file(paths["tokenizer"])
            self.tokenizer.enable_truncation(max_length=max_tokens)
            self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
            options = ort.SessionOptions()
            options.intra_op_num_threads = threads
            options.inter_op_num_threads = 1
            self.session = ort.InferenceSession(
                paths["weights"], sess_options=options, providers=["CPUExecutionProvider"]
            )
            self.input_names = {item.name for item in self.session.get_inputs()}
        except Exception:
            # Avoid leaking upstream details (e.g. a private cache path or proxy credentials).
            raise ValueError(
                "Pinned local embedding model is unavailable or invalid. Check the Hugging Face "
                "cache/network and run: uv run --extra embeddings --directory backend "
                "python -m researchlens.ingest --retrieval embeddings"
            ) from None

    def encode(self, texts: list[str]) -> np.ndarray:
        batches = []
        for start in range(0, len(texts), self.batch_size):
            encoded = self.tokenizer.encode_batch(texts[start : start + self.batch_size])
            inputs = {
                "input_ids": np.asarray([item.ids for item in encoded], dtype=np.int64),
                "attention_mask": np.asarray(
                    [item.attention_mask for item in encoded], dtype=np.int64
                ),
                "token_type_ids": np.asarray([item.type_ids for item in encoded], dtype=np.int64),
            }
            hidden = self.session.run(
                ["last_hidden_state"],
                {key: value for key, value in inputs.items() if key in self.input_names},
            )[0]
            mask = inputs["attention_mask"][..., None].astype(np.float32)
            pooled = (hidden * mask).sum(axis=1) / mask.sum(axis=1)
            pooled /= np.linalg.norm(pooled, axis=1, keepdims=True)
            batches.append(pooled.astype(np.float32))
        return np.concatenate(batches) if batches else np.empty((0, DIMENSIONS), dtype=np.float32)

    def measure_documents(self, texts: list[str]) -> list[dict]:
        from tokenizers import Tokenizer

        from researchlens.encoding_diagnostics import measurement

        # Clone rather than changing the tokenizer used by live searches.
        full = Tokenizer.from_str(self.tokenizer.to_str())
        full.no_truncation()
        full.no_padding()
        rows = []
        for text in texts:
            original = full.encode(text)
            retained = self.tokenizer.encode(text)
            end = max(
                (
                    offset[1]
                    for offset, special, visible in zip(
                        retained.offsets,
                        retained.special_tokens_mask,
                        retained.attention_mask,
                        strict=True,
                    )
                    if visible and not special
                ),
                default=0,
            )
            rows.append(measurement(text, len(original.ids), sum(retained.attention_mask), end))
        return rows


def validate_vectors(vectors: object, count: int, dimensions: int = DIMENSIONS) -> np.ndarray:
    """Fail closed on malformed, non-finite, zero or non-unit passage/query vectors."""
    try:
        matrix = np.asarray(vectors, dtype=np.float32)
    except (ValueError, TypeError, OverflowError):
        raise ValueError("Embedding vectors must be a rectangular numeric matrix") from None
    if (
        matrix.shape != (count, dimensions)
        or not np.isfinite(matrix).all()
        or not np.allclose(np.linalg.norm(matrix, axis=1), 1.0, atol=1e-4)
    ):
        raise ValueError("Embedding vectors have invalid dimensions, values or normalization")
    return matrix
