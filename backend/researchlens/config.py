import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


@dataclass(frozen=True)
class Settings:
    provider: Literal["local", "openai"] = "local"
    api_key: str = field(default="", repr=False)
    model: str = "gpt-6-luna"

    def __post_init__(self) -> None:
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
        )
