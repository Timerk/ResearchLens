"""Allowlisted, pinned local encoders for controlled retrieval comparisons."""

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

import numpy as np

from researchlens.embeddings import ENCODING, Encoder, LocalEncoder

QUERY_INSTRUCTION = (
    "Instruct: Given a research question, retrieve relevant passages that answer the question"
    "\nQuery: "
)


@dataclass(frozen=True)
class ModelSpec:
    model: str
    revision: str
    dimensions: int
    max_tokens: int
    pooling: str
    weights: str
    query_prefix: str = ""


MODELS = {
    "minilm": ModelSpec(
        ENCODING["model"],
        ENCODING["revision"],
        384,
        256,
        "attention-masked-mean",
        "onnx/model.onnx",
    ),
    "bge-m3": ModelSpec(
        "BAAI/bge-m3",
        "5617a9f61b028005a4858fdac845db406aefb181",
        1024,
        8192,
        "cls",
        "pytorch_model.bin",
    ),
    "qwen3-0.6b": ModelSpec(
        "Qwen/Qwen3-Embedding-0.6B",
        "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3",
        1024,
        32768,
        "last-nonpadding-token",
        "model.safetensors",
        QUERY_INSTRUCTION,
    ),
    "qwen3-4b": ModelSpec(
        "Qwen/Qwen3-Embedding-4B",
        "5cf2132abc99cad020ac570b19d031efec650f2b",
        2560,
        32768,
        "last-nonpadding-token",
        "model.safetensors.index.json",
        QUERY_INSTRUCTION,
    ),
}


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def encoding_metadata(
    model: str = "minilm",
    *,
    max_tokens: int | None = None,
    batch_size: int | None = None,
    threads: int | None = None,
    precision: str | None = None,
) -> dict:
    if model not in MODELS:
        raise ValueError(f"Unknown local embedding model; choose from {', '.join(MODELS)}")
    spec = MODELS[model]
    minilm = model == "minilm"
    tokens = max_tokens if max_tokens is not None else (256 if minilm else 512)
    batch = batch_size if batch_size is not None else (32 if minilm else 1)
    cpu_threads = threads if threads is not None else (2 if minilm else 8)
    dtype = precision or ("float32" if minilm else "bfloat16")
    if not 1 <= tokens <= spec.max_tokens or batch < 1 or not 1 <= cpu_threads <= 64:
        raise ValueError("Invalid embedding token limit, batch size or CPU thread count")
    if dtype not in ("float32", "bfloat16") or (minilm and dtype != "float32"):
        raise ValueError("MiniLM requires float32; Torch encoders support float32 or bfloat16")
    return {
        "model": spec.model,
        "revision": spec.revision,
        "dimensions": spec.dimensions,
        "max_tokens": tokens,
        "pooling": spec.pooling,
        "normalization": "l2",
        "query_prefix": spec.query_prefix,
        "document_prefix": "",
        "text": "passage-text-only",
        "encoding_version": 2,
        "weights": spec.weights,
        "tokenizer": "tokenizer.json",
        "runtime": "onnxruntime" if minilm else "torch+transformers",
        "runtime_version": package_version("onnxruntime" if minilm else "torch"),
        "backend": "CPUExecutionProvider" if minilm else "pytorch-cpu",
        "device": "cpu",
        "precision": dtype,
        "quantization": "none",
        "truncation": "right",
        "batch_size": batch,
        "intra_op_threads": cpu_threads,
        "inter_op_threads": 1,
    }


def model_for_encoding(saved: dict) -> str:
    """Verify every declared runtime/encoding setting before loading any weights."""
    name = next((name for name, spec in MODELS.items() if spec.model == saved.get("model")), None)
    if name is None:
        raise ValueError("Artifact uses an unsupported local embedding model")
    expected = encoding_metadata(
        name,
        max_tokens=saved.get("max_tokens"),
        batch_size=saved.get("batch_size"),
        threads=saved.get("intra_op_threads"),
        precision=saved.get("precision"),
    )
    if saved != expected:
        raise ValueError("Embedding model, revision, encoding or installed runtime changed")
    return name


def create_encoder(
    model: str = "minilm",
    *,
    download: bool = False,
    max_tokens: int | None = None,
    batch_size: int | None = None,
    threads: int | None = None,
    precision: str | None = None,
) -> Encoder:
    metadata = encoding_metadata(
        model, max_tokens=max_tokens, batch_size=batch_size, threads=threads, precision=precision
    )
    if model == "minilm":
        encoder = LocalEncoder(
            download=download,
            max_tokens=metadata["max_tokens"],
            batch_size=metadata["batch_size"],
            threads=metadata["intra_op_threads"],
        )
        encoder.encoding = metadata
        return encoder
    return TorchEncoder(metadata, download=download)


class TorchEncoder:
    """Dense BGE/Qwen embeddings on CPU; no remote code, generation or GPU allocation."""

    def __init__(self, encoding: dict, *, download: bool = False) -> None:
        self.encoding = encoding
        try:
            import torch
            from huggingface_hub import snapshot_download
            from transformers import AutoModel, AutoTokenizer
        except ImportError:
            raise ValueError(
                "Local Torch encoder dependencies are missing. Run: "
                "uv sync --locked --extra embedding-models --python 3.13"
            ) from None
        self.torch = torch
        try:
            # Only model/tokenizer files at the pinned revision; never repository Python code.
            path = snapshot_download(
                encoding["model"],
                revision=encoding["revision"],
                token=False,
                local_files_only=not download,
                allow_patterns=[
                    "config.json",
                    "tokenizer*.json",
                    "special_tokens_map.json",
                    "vocab.json",
                    "merges.txt",
                    "sentencepiece.bpe.model",
                    "model*.safetensors",
                    "model.safetensors.index.json",
                    "pytorch_model.bin",
                ],
            )
            torch.set_num_threads(encoding["intra_op_threads"])
            if torch.get_num_interop_threads() != encoding["inter_op_threads"]:
                torch.set_num_interop_threads(encoding["inter_op_threads"])
            self.tokenizer = AutoTokenizer.from_pretrained(
                path,
                local_files_only=True,
                trust_remote_code=False,
                padding_side="right",
                truncation_side="right",
            )
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model = (
                AutoModel.from_pretrained(
                    path,
                    local_files_only=True,
                    trust_remote_code=False,
                    dtype=getattr(torch, encoding["precision"]),
                    use_safetensors=encoding["weights"] != "pytorch_model.bin",
                    attn_implementation="sdpa",
                )
                .to("cpu")
                .eval()
            )
        except Exception:
            raise ValueError(
                "Pinned CPU embedding model could not be loaded. Check available RAM, installed "
                "runtime and Hugging Face cache/network; rebuild with researchlens.ingest "
                "--retrieval embeddings --embedding-model and the desired model alias."
            ) from None

    def encode(self, texts: list[str]) -> np.ndarray:
        torch = self.torch
        batches = []
        for start in range(0, len(texts), self.encoding["batch_size"]):
            inputs = self.tokenizer(
                texts[start : start + self.encoding["batch_size"]],
                padding=True,
                truncation=True,
                max_length=self.encoding["max_tokens"],
                return_tensors="pt",
            )
            options = {"use_cache": False} if self.encoding["pooling"] != "cls" else {}
            with torch.inference_mode():
                hidden = self.model(**inputs, **options).last_hidden_state
                if self.encoding["pooling"] == "cls":
                    pooled = hidden[:, 0]
                else:
                    positions = inputs["attention_mask"].sum(dim=1) - 1
                    pooled = hidden[torch.arange(hidden.shape[0]), positions]
                pooled = torch.nn.functional.normalize(pooled.float(), p=2, dim=1)
            batches.append(pooled.cpu().numpy())
        return (
            np.concatenate(batches)
            if batches
            else np.empty((0, self.encoding["dimensions"]), dtype=np.float32)
        )

    def measure_documents(self, texts: list[str]) -> list[dict]:
        from researchlens.encoding_diagnostics import measurement

        if not self.tokenizer.is_fast:
            raise ValueError("Encoding diagnostics require the pinned fast tokenizer's offsets")
        rows = []
        for text in texts:
            original = self.tokenizer(text, truncation=False, padding=False)
            retained = self.tokenizer(
                text,
                truncation=True,
                max_length=self.encoding["max_tokens"],
                padding=False,
                return_offsets_mapping=True,
                return_special_tokens_mask=True,
            )
            end = max(
                (
                    offset[1]
                    for offset, special in zip(
                        retained["offset_mapping"],
                        retained["special_tokens_mask"],
                        strict=True,
                    )
                    if not special
                ),
                default=0,
            )
            rows.append(
                measurement(
                    text,
                    len(original["input_ids"]),
                    len(retained["input_ids"]),
                    end,
                )
            )
        return rows
