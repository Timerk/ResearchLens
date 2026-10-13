"""Available physical RAM, independent of swap and installed memory."""

import psutil

from researchlens.config import RETRIEVAL_TIERS

GIB = 1024**3
MODEL_REQUIRED_GIB = {
    tier.model: tier.required_gib
    for tier in RETRIEVAL_TIERS.values()
    if tier.backend == "embeddings"
}
MODEL_REQUIRED_GIB["minilm"] = 0.5


def available_memory_gib() -> float:
    # psutil implements Windows, Linux and macOS physical-memory accounting.
    return psutil.virtual_memory().available / GIB


def next_tier(model: str) -> str:
    names = list(RETRIEVAL_TIERS)
    for index, name in enumerate(names[:-1]):
        if RETRIEVAL_TIERS[name].model == model:
            return names[index + 1]
    return "minimal"


def check_model_memory(model: str) -> None:
    required = MODEL_REQUIRED_GIB[model]
    available = available_memory_gib()
    if available < required:
        raise RuntimeError(
            f"Embedding model {model} needs {required:.2f} GiB available physical RAM; "
            f"available {available:.2f} GiB. Try RETRIEVAL_TIER={next_tier(model)}."
        )
