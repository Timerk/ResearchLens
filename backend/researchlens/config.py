import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"


def retrieval_environment(path: Path = ENV_FILE) -> dict:
    """Ingestion reads retrieval settings without requiring answer-provider credentials.

    Relative environment paths are repository-relative, independent of the launch directory.
    """
    values = {**dotenv_values(path), **os.environ}

    def configured_path(name: str, default: str) -> Path:
        selected = Path((values.get(name) or default).strip())
        return selected if selected.is_absolute() else ROOT / selected

    return {
        "retrieval": (values.get("RETRIEVAL_BACKEND") or "tfidf").strip(),
        "index_path": configured_path("RETRIEVAL_INDEX", "data/index.json"),
        "corpus_path": configured_path("RETRIEVAL_CORPUS", "data/technical/documents.json"),
    }


@dataclass(frozen=True)
class Settings:
    provider: Literal["local", "openai"] = "local"
    api_key: str = field(default="", repr=False)
    model: str = "gpt-6-luna"
    retrieval: Literal["tfidf", "embeddings"] = "tfidf"
    index_path: Path = ROOT / "data" / "index.json"
    corpus_path: Path = ROOT / "data" / "technical" / "documents.json"

    def __post_init__(self) -> None:
        if self.retrieval not in ("tfidf", "embeddings"):
            raise ValueError("RETRIEVAL_BACKEND must be tfidf or embeddings")
        if self.provider not in ("local", "openai"):
            raise ValueError("ANSWER_PROVIDER must be local or openai")
        if self.provider == "openai" and (not self.api_key.strip() or not self.model.strip()):
            raise ValueError("OpenAI mode requires OPENAI_API_KEY and OPENAI_MODEL")

    @classmethod
    def from_env(cls, path: Path = ENV_FILE) -> "Settings":
        # Process settings take precedence; reading a file does not modify global environment.
        values = {**dotenv_values(path), **os.environ}
        return cls(
            provider=(values.get("ANSWER_PROVIDER") or "local").strip(),
            api_key=(values.get("OPENAI_API_KEY") or "").strip(),
            model=(values.get("OPENAI_MODEL", "gpt-6-luna") or "").strip(),
            **retrieval_environment(path),
        )
