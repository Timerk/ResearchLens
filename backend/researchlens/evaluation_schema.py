"""Versioned evaluation contracts; draft expectations are not human judgments."""

from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from researchlens.models import Question


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Reference(StrictModel):
    source_id: str
    passage_id: str
    paragraph: int = Field(ge=1)
    page: int | None = Field(default=None, ge=1)


class Case(Question):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    category: Literal["factual", "comparison", "unanswerable"]
    expected_source_ids: list[str]
    references: list[Reference]
    required_claims: list[str]
    required_qualifications: list[str]
    forbidden_claims: list[str]
    expected_abstention: bool
    review_status: Literal["unreviewed", "approved", "rejected"]
    reviewer: str | None
    review_date: date | None

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.expected_abstention != (self.category == "unanswerable"):
            raise ValueError("Unanswerable cases must expect abstention")
        sources = set(self.expected_source_ids)
        if len(sources) != len(self.expected_source_ids):
            raise ValueError("Expected sources must be unique")
        if sources != {ref.source_id for ref in self.references}:
            raise ValueError("Each expected source needs a passage reference")
        if not self.expected_abstention and (not sources or not self.required_claims):
            raise ValueError("Answerable cases need sources and required claims")
        if self.category == "comparison" and len(sources) < 2:
            raise ValueError("Comparisons need at least two sources")
        if self.review_status != "unreviewed" and (
            not self.reviewer or not self.reviewer.strip() or not self.review_date
        ):
            raise ValueError("Human review requires a reviewer and date")
        if self.review_status == "unreviewed" and (self.reviewer or self.review_date):
            raise ValueError("Unreviewed drafts cannot claim a reviewer or review date")
        return self


class Dataset(StrictModel):
    schema_version: Literal[1]
    id: str
    version: str
    split: Literal["development", "held-out"]
    material: Literal["synthetic", "real-corpus"]
    status: Literal["draft", "frozen", "pending-real-corpus"]
    corpus_sha256: str | None = Field(pattern=r"^[a-f0-9]{64}$")
    notes: str
    cases: list[Case]

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("Case IDs must be unique")
        if len({case.question.casefold() for case in self.cases}) != len(self.cases):
            raise ValueError("Questions must be unique")
        if self.status == "pending-real-corpus":
            if self.cases or self.corpus_sha256 or self.material != "real-corpus":
                raise ValueError("Pending real corpus must be empty and unpinned")
        elif not self.cases or not self.corpus_sha256:
            raise ValueError("Runnable datasets need cases and a pinned corpus hash")
        if self.status == "frozen" and any(c.review_status != "approved" for c in self.cases):
            raise ValueError("Frozen datasets require human-approved cases")
        if self.split == "held-out" and self.material != "real-corpus":
            raise ValueError("Synthetic examples belong in development only")
        return self


class RetrievalConfig(StrictModel):
    implementation: str
    version: str
    limit: int = Field(default=4, ge=1)
    model: str | None = None
    revision: str | None = None
    artifact_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    # Explicit fields avoid serializing arbitrary settings (which may contain credentials).
    normalization: str | None = None
    score_threshold: float | None = None


class GenerationConfig(StrictModel):
    provider: Literal["none", "local-preview", "mock", "openai"] = "none"
    model: str | None = None
    reasoning_effort: Literal["medium"] | None = None
    max_output_tokens: int | None = Field(default=None, ge=1, le=2000)
    max_retries: Literal[0] = 0
    prompt_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def live_limits(self) -> Self:
        if self.provider == "openai" and (
            self.model != "gpt-6-luna"
            or self.reasoning_effort != "medium"
            or self.max_output_tokens is None
            or self.prompt_sha256 is None
        ):
            raise ValueError("Live evaluation requires Luna/medium, bounded output and prompt hash")
        return self


class ClaimReview(StrictModel):
    section_index: int = Field(ge=0)
    correctness: Literal["correct", "incorrect", "unclear"] | None = None
    citation_support: Literal["supported", "unsupported", "unclear"] | None = None
    evidence_notes: str = ""


class CaseReview(StrictModel):
    case_id: str
    status: Literal["pending", "complete"] = "pending"
    reviewer: str | None = None
    review_date: date | None = None
    correctness: Literal["correct", "partial", "incorrect", "unclear", "not-applicable"] | None = (
        None
    )
    citation_support: Literal["supported", "unsupported", "unclear", "not-applicable"] | None = None
    abstention: Literal["full", "partial", "none", "not-applicable"] | None = None
    required_claims_met: bool | None = None
    qualifications_preserved: bool | None = None
    forbidden_claims_present: bool | None = None
    claims: list[ClaimReview] = Field(default_factory=list)
    notes: str = ""

    @model_validator(mode="after")
    def completed(self) -> Self:
        if self.status == "complete" and (
            not self.reviewer
            or not self.reviewer.strip()
            or not self.review_date
            or any(
                value is None
                for value in (
                    self.correctness,
                    self.citation_support,
                    self.abstention,
                    self.required_claims_met,
                    self.qualifications_preserved,
                    self.forbidden_claims_present,
                )
            )
            or any(c.correctness is None or c.citation_support is None for c in self.claims)
        ):
            raise ValueError("Complete reviews need identity, date and all judgments")
        return self


class Review(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str
    run_sha256: str
    cases: list[CaseReview]
