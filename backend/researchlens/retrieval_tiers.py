"""Resolve application tiers without mixing model-specific index artifacts."""

import gc
import logging
from dataclasses import replace

from researchlens.config import RETRIEVAL_TIERS, Settings
from researchlens.memory import available_memory_gib
from researchlens.retrieval import PassageRetriever, load_retriever

logger = logging.getLogger(__name__)


def uses_tiers(settings: Settings) -> bool:
    return bool(settings.retrieval_tier) and not (
        settings.retrieval_overridden
        or settings.retrieval != "tfidf"
        or settings.embedding_model != "minilm"
    )


def tier_settings(settings: Settings, name: str) -> Settings:
    tier = RETRIEVAL_TIERS[name]
    return replace(
        settings,
        retrieval=tier.backend,
        embedding_model=tier.model,
        index_path=settings.tier_index_dir / f"{name}.json",
        answer_context_mode="characters",
        answer_context_chars=tier.context_chars,
        answer_context_candidates=40,
    )


def load_configured_retriever(settings: Settings) -> tuple[PassageRetriever, Settings, str | None]:
    def load(selected: Settings) -> PassageRetriever:
        return load_retriever(
            selected.retrieval,
            selected.index_path,
            source=selected.corpus_path,
            expected_model=selected.embedding_model,
            **selected.retriever_options(),
        )

    if not uses_tiers(settings):
        return load(settings), settings, None
    automatic = settings.retrieval_tier == "auto"
    names = list(RETRIEVAL_TIERS) if automatic else [settings.retrieval_tier]
    for name in names:
        tier = RETRIEVAL_TIERS[name]
        selected = tier_settings(settings, name)
        available = available_memory_gib()
        if available < tier.required_gib:
            following = list(RETRIEVAL_TIERS)
            index = following.index(name)
            suggestion = (
                f"Try RETRIEVAL_TIER={following[index + 1]}."
                if index + 1 < len(following)
                else "Free physical RAM before restarting."
            )
            message = (
                f"Retrieval tier {name} ({tier.model if tier.backend != 'tfidf' else 'tfidf'}) "
                f"needs {tier.required_gib:.2f} GiB available physical RAM; "
                f"available {available:.2f} GiB. {suggestion}"
            )
            if not automatic:
                raise RuntimeError(message)
            logger.info("Skipping %s", message)
            continue
        if not selected.index_path.is_file():
            message = (
                f"Missing retrieval tier {name} artifact: {selected.index_path}. "
                f"Build with python -m researchlens.ingest --tier {name}."
            )
            if not automatic:
                raise RuntimeError(message)
            logger.info(message)
            continue
        try:
            retriever = load(selected)
        except (ValueError, MemoryError, RuntimeError) as exc:
            if not automatic:
                raise RuntimeError(f"Retrieval tier {name} failed: {exc}") from exc
            # Do not retain failed model allocations or tracebacks while trying a lower tier.
            logger.warning("Skipping retrieval tier %s after load failure: %s", name, exc)
        else:
            logger.info(
                "Selected retrieval tier %s (%s), %.2f GiB available, index %s",
                name,
                tier.backend if tier.backend == "tfidf" else tier.model,
                available,
                selected.index_path,
            )
            return retriever, selected, name
        gc.collect()
    raise RuntimeError(
        "No retrieval tier could load with available RAM and artifacts. "
        "Build a fitting tier with python -m researchlens.ingest --tier minimal "
        "or inspect the tier load warnings."
    )
