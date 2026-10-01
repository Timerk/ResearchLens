"""Evidence labels and encoder measurements, independent of retrieval implementations."""

import hashlib
import json
from datetime import date
from typing import Literal, Self

from pydantic import Field, model_validator

from researchlens.artifacts import canonical_hash, passage_identity
from researchlens.evaluation_schema import Case, Dataset, StrictModel
from researchlens.models import Passage


class TextRange(StrictModel):
    start: int = Field(ge=0, strict=True)
    end: int = Field(ge=1, strict=True)

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end <= self.start:
            raise ValueError("Text ranges are nonempty half-open character offsets")
        return self


class EvidenceSpan(TextRange):
    passage_id: str
    quote: str = Field(min_length=1)


class EvidenceGroup(StrictModel):
    id: str = Field(min_length=1)
    claim_index: int = Field(ge=0, strict=True)
    description: str = Field(min_length=1)
    # OR between alternatives, AND between spans in one alternative.
    alternatives: list[list[EvidenceSpan]] = Field(min_length=1)

    @model_validator(mode="after")
    def nonempty_options(self) -> Self:
        if any(not option for option in self.alternatives):
            raise ValueError("Each evidence alternative requires supporting spans")
        options = []
        for option in self.alternatives:
            keys = [(span.passage_id, span.start, span.end) for span in option]
            if len(set(keys)) != len(keys):
                raise ValueError("Duplicate evidence spans within an alternative")
            options.append(tuple(sorted(keys)))
        if len(set(options)) != len(options):
            raise ValueError("Duplicate evidence alternatives")
        return self


class CaseEvidence(StrictModel):
    case_id: str
    groups: list[EvidenceGroup] = Field(min_length=1)


class EvidenceLabels(StrictModel):
    schema_version: Literal[1] = 1
    dataset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    corpus_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    shared_passage_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    review_status: Literal["unreviewed", "approved"]
    reviewer: str | None
    review_date: date | None
    notes: str
    cases: list[CaseEvidence]

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if len({c.case_id for c in self.cases}) != len(self.cases):
            raise ValueError("Evidence case IDs must be unique")
        if self.review_status == "approved" and (
            not self.reviewer or not self.reviewer.strip() or not self.review_date
        ):
            raise ValueError("Approved evidence labels require reviewer and date")
        if self.review_status == "unreviewed" and (self.reviewer or self.review_date):
            raise ValueError("Draft evidence labels cannot claim review provenance")
        return self


def dataset_digest(dataset: Dataset) -> str:
    raw = json.dumps(dataset.model_dump(mode="json"), indent=2, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256((raw + "\n").encode()).hexdigest()


def validate_labels(
    labels: EvidenceLabels, dataset: Dataset, artifact: dict, passages: list[Passage]
) -> dict[str, CaseEvidence]:
    if (
        labels.dataset_sha256 != dataset_digest(dataset)
        or labels.corpus_sha256 != artifact["source_sha256"]
        or labels.shared_passage_sha256 != passage_identity(artifact, passages)
    ):
        raise ValueError("Evidence labels do not match dataset and shared passages")
    cases = {c.id: c for c in dataset.cases}
    by_id = {p.id: p for p in passages}
    for entry in labels.cases:
        case = cases.get(entry.case_id)
        if case is None or case.expected_abstention:
            raise ValueError("Evidence labels require a known answerable case")
        if len({g.id for g in entry.groups}) != len(entry.groups):
            raise ValueError("Evidence group IDs must be unique within a case")
        if {g.claim_index for g in entry.groups} != set(range(len(case.required_claims))):
            raise ValueError("Evidence groups must cover every required claim index")
        for group in entry.groups:
            for option in group.alternatives:
                for span in option:
                    passage = by_id.get(span.passage_id)
                    if (
                        passage is None
                        or passage.document_id not in case.expected_source_ids
                        or span.end > len(passage.text)
                        or passage.text[span.start : span.end] != span.quote
                    ):
                        raise ValueError("Evidence span is stale or not from an expected source")
    return {c.case_id: c for c in labels.cases}


class EncodedPassage(StrictModel):
    passage_id: str
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_tokens: int = Field(ge=1, strict=True)
    encoded_tokens: int = Field(ge=1, strict=True)
    truncated: bool = Field(strict=True)
    retained_ranges: list[TextRange]


class EncodingDiagnostics(StrictModel):
    schema_version: Literal[1] = 1
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    encoding_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    # Counts include instructions/special tokens; offsets refer only to canonical passage text.
    token_count_scope: Literal["encoder-input-including-instructions-and-special-tokens"]
    passages: list[EncodedPassage]


def validate_pair_diagnostics(
    rows: list[dict], passages: list[Passage], max_tokens: int
) -> list[dict]:
    """Pair token counts include the question; ranges refer to the canonical passage only."""
    measurements = [EncodedPassage.model_validate(row) for row in rows]
    by_id = {p.id: p for p in passages}
    if len({p.passage_id for p in measurements}) != len(measurements):
        raise ValueError("Duplicate reranker measurements")
    for row in measurements:
        passage = by_id.get(row.passage_id)
        if (
            passage is None
            or row.text_sha256 != hashlib.sha256(passage.text.encode()).hexdigest()
            or row.encoded_tokens > min(row.input_tokens, max_tokens)
        ):
            raise ValueError("Invalid reranker text or token counts")
        previous = 0
        for region in row.retained_ranges:
            if region.start < previous or region.end > len(passage.text):
                raise ValueError("Invalid reranker retained ranges")
            previous = region.end
        retained = sum(region.end - region.start for region in row.retained_ranges)
        if row.truncated != (retained < len(passage.text)) or (
            row.truncated and row.input_tokens == row.encoded_tokens
        ):
            raise ValueError("Invalid reranker truncation flag")
    return [row.model_dump(mode="json") for row in measurements]


def validate_encoding_diagnostics(
    diagnostics: EncodingDiagnostics, artifact: dict, passages: list[Passage]
) -> dict[str, EncodedPassage]:
    if (
        "embeddings" not in artifact
        or diagnostics.artifact_sha256 != canonical_hash(artifact)
        or diagnostics.encoding_sha256 != canonical_hash(artifact["embeddings"]["encoding"])
    ):
        raise ValueError("Encoding diagnostics do not match embedding artifact")
    if len({p.passage_id for p in diagnostics.passages}) != len(diagnostics.passages):
        raise ValueError("Encoding diagnostic passage IDs must be unique")
    by_id = {p.id: p for p in passages}
    for measurement in diagnostics.passages:
        passage = by_id.get(measurement.passage_id)
        if (
            passage is None
            or measurement.text_sha256 != hashlib.sha256(passage.text.encode()).hexdigest()
            or measurement.encoded_tokens > measurement.input_tokens
            or measurement.encoded_tokens > artifact["embeddings"]["encoding"]["max_tokens"]
        ):
            raise ValueError("Encoding measurement has stale text or invalid token counts")
        previous = 0
        for region in measurement.retained_ranges:
            if region.start < previous or region.end > len(passage.text):
                raise ValueError("Retained ranges must be ordered, nonoverlapping and in bounds")
            previous = region.end
        retained = sum(r.end - r.start for r in measurement.retained_ranges)
        if measurement.truncated != (retained < len(passage.text)):
            raise ValueError("Truncation flag disagrees with retained text ranges")
        if measurement.truncated and measurement.encoded_tokens == measurement.input_tokens:
            raise ValueError("Truncated inputs must lose tokens")
    return {p.passage_id: p for p in diagnostics.passages}


def span_visible(span: EvidenceSpan, ranges: list[TextRange]) -> bool:
    # Adjacent ranges can jointly retain an entire evidence span.
    position = span.start
    for region in ranges:
        if region.start > position:
            return False
        if region.end > position:
            position = region.end
        if position >= span.end:
            return True
    return False


def evidence_coverage(
    entry: CaseEvidence | None,
    visible: dict[str, list[TextRange] | None],
) -> dict:
    """Unknown encoder ranges remain unknown; lack of a retrieved passage is a miss."""
    if entry is None:
        return {"groups": [], "group_coverage": None, "complete_evidence": None}
    groups = []
    for group in entry.groups:
        alternatives = []
        for option in group.alternatives:
            states = [
                None
                if span.passage_id in visible and visible[span.passage_id] is None
                else span_visible(span, visible.get(span.passage_id, []))
                for span in option
            ]
            alternatives.append(False if False in states else None if None in states else True)
        covered = True if True in alternatives else None if None in alternatives else False
        groups.append({"group_id": group.id, "claim_index": group.claim_index, "covered": covered})
    states = [g["covered"] for g in groups]
    return {
        "groups": groups,
        "group_coverage": None if None in states else sum(states) / len(states),
        "complete_evidence": False if False in states else None if None in states else True,
    }


def ranking_metrics(case: Case, hits: list[Passage], entry: CaseEvidence | None) -> dict:
    if case.expected_abstention:
        return {
            "source_recall": None,
            "passage_recall": None,
            "first_relevant_rank": None,
            "reciprocal_rank": None,
            "all_sources": None,
            **evidence_coverage(None, {}),
        }
    ids = {p.id for p in hits}
    sources = {p.document_id for p in hits}
    positive = {r.passage_id for r in case.references}
    relevant = (
        {
            span.passage_id
            for group in entry.groups
            for option in group.alternatives
            for span in option
        }
        if entry
        else positive
    )
    first = next((i for i, p in enumerate(hits, 1) if p.id in relevant), None)
    return {
        "source_recall": len(set(case.expected_source_ids) & sources)
        / len(case.expected_source_ids),
        "passage_recall": len(positive & ids) / len(positive),
        "first_relevant_rank": first,
        "reciprocal_rank": 1 / first if first else 0.0,
        "all_sources": set(case.expected_source_ids) <= sources,
        **evidence_coverage(entry, {p.id: [TextRange(start=0, end=len(p.text))] for p in hits}),
    }


def coverage_loss(before: dict, after: dict) -> dict:
    """Identify groups present in full retrieved text but removed or unmeasured later."""
    previous = {g["group_id"]: g["covered"] for g in before["groups"]}
    return {
        "lost_group_ids": [
            g["group_id"]
            for g in after["groups"]
            if previous[g["group_id"]] is True and g["covered"] is False
        ],
        "unknown_group_ids": [
            g["group_id"]
            for g in after["groups"]
            if previous[g["group_id"]] is True and g["covered"] is None
        ],
    }
