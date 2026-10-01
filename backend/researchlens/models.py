from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Attribution(BaseModel):
    authors: list[str]
    publication_date: str
    doi: str
    license_url: str
    copyright: str
    changes: str
    source_sha256: str


class ParagraphSource(BaseModel):
    section: str
    locator: str


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9-]+$")
    title: str
    source_url: str | None
    license: str
    kind: Literal["synthetic", "technical"]
    text: str = Field(min_length=1)
    attribution: Attribution | None = None
    paragraph_sources: list[ParagraphSource] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_provenance(self) -> "Document":
        if self.paragraph_sources and len(self.paragraph_sources) != len(self.text.split("\n\n")):
            raise ValueError("Each paragraph must have exactly one source location")
        return self


class Passage(BaseModel):
    id: str
    document_id: str
    title: str
    source_url: str | None
    license: str
    kind: Literal["synthetic", "technical"]
    paragraph: int
    text: str
    attribution: Attribution | None = None
    source_section: str | None = None
    source_locator: str | None = None


class SearchHit(Passage):
    score: float


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=3, max_length=2000)

    @field_validator("question", mode="before")
    @classmethod
    def strip_question(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AnswerSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=4000)
    citation_ids: list[str] = Field(min_length=1, max_length=4)


class GeneratedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["answered", "insufficient_evidence"]
    sections: list[AnswerSection] = Field(max_length=6)


class AnswerContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_passages: int
    max_passage_chars: int
    max_context_chars: int
    serialized_chars: int
    passage_ids: list[str]
    omitted_passage_ids: list[str]
    truncated_passage_ids: list[str]
    visible_chars: dict[str, int]


class Answer(BaseModel):
    status: Literal["passages_found", "no_matches", "answered", "insufficient_evidence"]
    mode: Literal["local_preview", "openai"] = "local_preview"
    message: str
    sections: list[AnswerSection] = Field(default_factory=list)
    passages: list[SearchHit]
    latency_ms: float
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_api_cost_usd: float | None = None
    context_diagnostics: AnswerContext | None = None
