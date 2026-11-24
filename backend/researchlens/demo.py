"""Public demo controls: recorded answers, live-answer limits, visitor keys and a kill switch.

None of this changes retrieval or answer generation. It decides whether a request may
spend money on a live answer and, if not, serves the free local preview instead.
"""

import json
import logging
import os
import re
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field

from researchlens.config import ENV_FILE, ROOT
from researchlens.models import Answer, AnswerSection, Passage, Question

logger = logging.getLogger("uvicorn.error.researchlens")

RECORDINGS = ROOT / "data" / "demo" / "recorded-answers.json"
DEFAULT_QUOTA_DB = ROOT / "data" / "state" / "live-quota.sqlite3"
VISITOR_KEY_HEADER = "X-OpenAI-API-Key"
# Accept the documented key shapes without echoing or logging a rejected value.
VISITOR_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{16,300}")
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

FallbackReason = Literal[
    "visitor_limit", "daily_limit", "verification", "provider_limit", "demo_only"
]
NOTICES: dict[str, str] = {
    "visitor_limit": (
        "You have used today's live answers for this demo. Here are the ranked passages "
        "instead; live answers reset at midnight UTC. You can also use your own OpenAI key."
    ),
    "daily_limit": (
        "The demo's live answers for today are used up. Here are the ranked passages "
        "instead; live answers reset at midnight UTC."
    ),
    "verification": (
        "The bot check did not succeed, so no live answer was generated. Here are the ranked "
        "passages instead. Complete the check and ask again for a live answer."
    ),
    "provider_limit": (
        "The demo's OpenAI budget is exhausted for now. Here are the ranked passages instead."
    ),
    "demo_only": (
        "Live answers are switched off on this demo, so no API call was made. Here are the "
        "ranked passages. Recorded example answers are still available."
    ),
}


def _flag(value: str | None, name: str) -> bool:
    normalized = (value or "").strip().lower()
    if normalized in ("", "0", "false", "no", "off"):
        return False
    if normalized in ("1", "true", "yes", "on"):
        return True
    raise ValueError(f"{name} must be true or false")


def _number(value: str | None, name: str, default: int, low: int, high: int) -> int:
    try:
        number = int((value or "").strip() or default)
    except ValueError:
        raise ValueError(f"{name} must be a whole number") from None
    if not low <= number <= high:
        raise ValueError(f"{name} must be within {low}..{high}")
    return number


@dataclass(frozen=True)
class DemoConfig:
    """Defaults suit tests and local use: live answers allowed, in-memory quota."""

    demo_only: bool = False
    visitor_daily_limit: int = 5
    global_daily_limit: int = 50
    # None keeps counts in memory. from_env always selects a file.
    quota_db: Path | None = None
    allow_visitor_keys: bool = False
    turnstile_site_key: str = ""
    turnstile_secret_key: str = field(default="", repr=False)
    proxy_hops: int = 1
    recordings: Path = RECORDINGS

    def __post_init__(self) -> None:
        if bool(self.turnstile_site_key) != bool(self.turnstile_secret_key):
            raise ValueError("Set both TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY, or neither")

    @property
    def turnstile_enabled(self) -> bool:
        return bool(self.turnstile_secret_key)

    @classmethod
    def from_env(cls, path: Path = ENV_FILE) -> "DemoConfig":
        values = {**dotenv_values(path), **os.environ}
        quota_db = Path((values.get("LIVE_QUOTA_DB") or "").strip() or DEFAULT_QUOTA_DB)
        return cls(
            demo_only=_flag(values.get("DEMO_ONLY"), "DEMO_ONLY"),
            visitor_daily_limit=_number(
                values.get("LIVE_ANSWERS_PER_VISITOR_PER_DAY"),
                "LIVE_ANSWERS_PER_VISITOR_PER_DAY",
                5,
                0,
                1000,
            ),
            global_daily_limit=_number(
                values.get("LIVE_ANSWERS_PER_DAY"), "LIVE_ANSWERS_PER_DAY", 50, 0, 100000
            ),
            quota_db=quota_db if quota_db.is_absolute() else ROOT / quota_db,
            allow_visitor_keys=_flag(
                values.get("ALLOW_VISITOR_API_KEYS"), "ALLOW_VISITOR_API_KEYS"
            ),
            turnstile_site_key=(values.get("TURNSTILE_SITE_KEY") or "").strip(),
            turnstile_secret_key=(values.get("TURNSTILE_SECRET_KEY") or "").strip(),
            proxy_hops=_number(values.get("TRUSTED_PROXY_HOPS"), "TRUSTED_PROXY_HOPS", 1, 0, 5),
        )


class AskRequest(Question):
    model_config = ConfigDict(extra="forbid")

    turnstile_token: str | None = Field(default=None, max_length=4096)


class RecordedPassage(Passage):
    # The grading packet did not record retrieval scores.
    score: float | None = None


class RecordingInfo(BaseModel):
    study_id: str
    recorded_on: str
    model: str
    configuration: str
    retrieval_tier: str
    retrieval_model: str
    context_chars: int
    case_id: str
    packet_item: str
    run_sha256: str


class RecordedAnswer(BaseModel):
    status: Literal["answered", "insufficient_evidence"]
    mode: Literal["openai"] = "openai"
    message: str
    sections: list[AnswerSection]
    passages: list[RecordedPassage]
    model: str


class Recording(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9-]+$")
    title: str
    question: str
    recorded: RecordingInfo
    answer: RecordedAnswer

    @property
    def label(self) -> str:
        info = self.recorded
        return (
            f"Recorded answer from evaluation run {info.recorded_on}, model {info.model}, "
            f"tier {info.retrieval_tier} ({info.retrieval_model}, "
            f"{info.context_chars // 1000}k context)"
        )


class Replay(BaseModel):
    example_id: str
    label: str
    recorded: RecordingInfo
    note: str


class ReplayResponse(Answer):
    passages: list[RecordedPassage]  # type: ignore[assignment]
    latency_ms: float | None = None  # type: ignore[assignment]
    replay: Replay


class DemoAnswer(Answer):
    notice: str | None = None
    fallback_reason: FallbackReason | None = None
    live_answers_remaining: int | None = None


class ExampleSummary(BaseModel):
    id: str
    title: str
    question: str
    label: str


class DemoStatus(BaseModel):
    live_answers: Literal["enabled", "demo_only", "not_configured"]
    visitor_daily_limit: int
    global_daily_limit: int
    visitor_remaining: int | None
    remaining_today: int | None
    visitor_keys: bool
    turnstile_site_key: str | None
    examples: list[ExampleSummary]


def load_recordings(path: Path = RECORDINGS) -> dict[str, Recording]:
    if not path.is_file():
        logger.warning("No recorded demo answers at %s; examples are disabled", path)
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1:
        raise ValueError(f"Unsupported recorded-answer schema in {path}")
    recordings = [Recording.model_validate(item) for item in document["examples"]]
    return {recording.id: recording for recording in recordings}


def replay(recording: Recording) -> ReplayResponse:
    """Serve a recorded answer exactly as recorded. No retrieval and no API call."""
    answer = recording.answer
    return ReplayResponse(
        status=answer.status,
        mode=answer.mode,
        message=answer.message,
        sections=answer.sections,
        passages=answer.passages,
        model=answer.model,
        estimated_api_cost_usd=0,
        replay=Replay(
            example_id=recording.id,
            label=recording.label,
            recorded=recording.recorded,
            note=(
                "Replayed from a saved development evaluation run; no API call was made. "
                "Only the cited passages were recorded, as the model saw them."
            ),
        ),
    )


def read_visitor_key(value: str | None) -> str | None:
    """Validate a visitor-supplied key. Errors never include the value."""
    if value is None or not value.strip():
        return None
    key = value.strip()
    if not VISITOR_KEY_PATTERN.fullmatch(key):
        raise ValueError("The supplied OpenAI API key is not in a recognized format.")
    return key


TurnstileVerifier = Callable[[str, str], bool]


def turnstile_verifier(secret: str, timeout: float = 5.0) -> TurnstileVerifier:
    def verify(token: str, address: str) -> bool:
        payload = urllib.parse.urlencode(
            {"secret": secret, "response": token, "remoteip": address}
        ).encode()
        request = urllib.request.Request(TURNSTILE_VERIFY_URL, data=payload, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
                return json.loads(response.read()).get("success") is True
        except (OSError, ValueError):
            logger.warning("Turnstile verification could not complete")
            return False

    return verify
