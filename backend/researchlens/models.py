from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9-]+$")
    title: str
    source_url: str | None
    license: str
    kind: Literal["synthetic", "technical"]
    text: str = Field(min_length=1)


class Passage(BaseModel):
    id: str
    document_id: str
    title: str
    source_url: str | None
    license: str
    kind: Literal["synthetic", "technical"]
    paragraph: int
    text: str


class SearchHit(Passage):
    score: float


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=3, max_length=2000)

    @field_validator("question", mode="before")
    @classmethod
    def strip_question(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class Answer(BaseModel):
    status: Literal["passages_found", "no_matches"]
    mode: Literal["local_preview"] = "local_preview"
    message: str
    passages: list[SearchHit]
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_api_cost_usd: float = 0
