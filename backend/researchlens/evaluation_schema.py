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
    source_section: str | None = None
    source_locator: str | None = None


class SourceVersion(StrictModel):
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    doi: str
    publication_date: str


class Case(Question):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    category: Literal["factual", "comparison", "unanswerable"]
    query_style: (
        Literal[
            "exact-terminology", "paraphrase", "cross-document", "unrelated", "missing-evidence"
        ]
        | None
    ) = None
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
    status: Literal["draft", "frozen", "pending-real-corpus", "pending-human-review"]
    corpus_sha256: str | None = Field(pattern=r"^[a-f0-9]{64}$")
    notes: str
    source_versions: list[SourceVersion] = Field(default_factory=list)
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
        elif self.status == "pending-human-review":
            if self.cases or not self.corpus_sha256 or self.material != "real-corpus":
                raise ValueError("Pending held-out review needs a pinned real corpus and no cases")
        elif not self.cases or not self.corpus_sha256:
            raise ValueError("Runnable datasets need cases and a pinned corpus hash")
        if self.status == "frozen" and any(c.review_status != "approved" for c in self.cases):
            raise ValueError("Frozen datasets require human-approved cases")
        if self.split == "held-out" and self.material != "real-corpus":
            raise ValueError("Synthetic examples belong in development only")
        if len({s.source_id for s in self.source_versions}) != len(self.source_versions):
            raise ValueError("Source version IDs must be unique")
        if self.material == "real-corpus" and self.cases and not self.source_versions:
            raise ValueError("Technical datasets must pin original source versions")
        return self


class RetrievalConfig(StrictModel):
    implementation: str
    version: str
    limit: int = Field(default=4, ge=1)
    backend: Literal["tfidf", "embeddings", "hybrid", "custom"] = "custom"
    model: str | None = None
    revision: str | None = None
    artifact_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    # Explicit fields avoid serializing arbitrary settings (which may contain credentials).
    normalization: str | None = None
    score_threshold: float | None = Field(default=None, allow_inf_nan=False)
    runtime: str | None = None
    runtime_version: str | None = None
    runtime_backend: str | None = None
    device: str | None = None
    precision: str | None = None
    quantization: str | None = None
    dimensions: int | None = Field(default=None, ge=1)
    weights: str | None = None
    tokenizer: str | None = None
    pooling: str | None = None
    query_instruction: str | None = None
    document_instruction: str | None = None
    max_tokens: int | None = Field(default=None, ge=1)
    truncation: str | None = None
    batch_size: int | None = Field(default=None, ge=1)
    intra_op_threads: int | None = Field(default=None, ge=1)
    inter_op_threads: int | None = Field(default=None, ge=1)
    text_representation: str | None = None
    encoding_version: int | None = Field(default=None, ge=1)
    lexical_candidates: int | None = Field(default=None, ge=1)
    embedding_candidates: int | None = Field(default=None, ge=1)
    fusion_method: Literal["rrf", "weighted-score"] | None = None
    rrf_k: int | None = Field(default=None, ge=1)
    lexical_weight: float | None = Field(default=None, ge=0, le=1)
    embedding_weight: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def hybrid_settings(self) -> Self:
        if self.backend == "hybrid" and (
            self.lexical_candidates is None
            or self.embedding_candidates is None
            or self.fusion_method is None
            or (self.fusion_method == "rrf" and self.rrf_k is None)
            or (
                self.fusion_method == "weighted-score"
                and (self.lexical_weight is None or self.embedding_weight is None)
            )
        ):
            raise ValueError("Hybrid comparisons require candidate counts and fusion settings")
        return self


class ExecutionConfig(StrictModel):
    repeats: int = Field(default=1, ge=1, le=100)
    warmups: int = Field(default=0, ge=0, le=100)
    measure_memory: bool = False
    ingestion_time_ms: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    index_load_time_ms: float | None = Field(default=None, ge=0, allow_inf_nan=False)


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
    status: Literal["pending", "complete", "not-applicable"] = "pending"
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
