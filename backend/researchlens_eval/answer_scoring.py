"""Answer scoring commands for the existing evaluation runner."""

import json
import math
from statistics import mean
from typing import Literal

from pydantic import Field
from researchlens.answers import (
    prepare_answer_context,
)
from researchlens.artifacts import atomic_write_text
from researchlens.models import SearchHit

from researchlens_eval.answer_constants import CONTEXT_CHARS
from researchlens_eval.answer_judge_v2 import MODEL
from researchlens_eval.evaluation_schema import StrictModel


class Decision(StrictModel):
    value: bool | None
    reason: str = Field(min_length=1)


class CitationDecision(Decision):
    section_index: int = Field(ge=0)
    citation_id: str
    evidence_quotes: list[str]


class Judgment(StrictModel):
    required_claims: list[Decision]
    qualifications: list[Decision]
    forbidden_claims: list[Decision]
    citations: list[CitationDecision]
    sections_fully_supported: list[Decision]


class Prices(StrictModel):
    model: Literal["gpt-6-luna"] = MODEL
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    provenance: str = Field(min_length=1)
    input_per_million: float = Field(gt=0, allow_inf_nan=False)
    output_per_million: float = Field(gt=0, allow_inf_nan=False)

    def cost(self, inputs, outputs):
        return (inputs * self.input_per_million + outputs * self.output_per_million) / 1e6


def save(path, value):
    atomic_write_text(
        path,
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
    )


def visible_context(row, budget):
    return prepare_answer_context(
        [SearchHit.model_validate(p) for p in row["retrieved_passages"]],
        mode="passages" if budget == 4 else "characters",
        max_context_chars=CONTEXT_CHARS if budget == 4 else budget,
    )


def judge_input(case, answer, prepared, evidence):
    return {
        "question": case.question,
        "required_claims": case.required_claims,
        "qualifications": case.required_qualifications,
        "forbidden_claims": case.forbidden_claims,
        "answer": {"status": answer["status"], "sections": answer["sections"]},
        "visible_passages": prepared.items,
        "approved_evidence": evidence.model_dump(mode="json") if evidence else None,
    }


def all_decided(values):
    if any(v is False for v in values):
        return False
    return None if any(v is None for v in values) else True


def score(case, answer, prepared, judgment=None, *, judge_version=1):
    sections = answer.get("sections", []) if answer else []
    generated = bool(answer and answer["status"] in ("answered", "insufficient_evidence"))
    abstained = bool(generated and answer["status"] == "insufficient_evidence" and not sections)
    valid = bool(
        generated
        and all(
            s["citation_ids"]
            and s["text"].strip()
            and set(s["citation_ids"]) <= {p["id"] for p in prepared.items}
            for s in sections
        )
    )
    if sections and judgment is None:
        required = [None] * len(case.required_claims)
        qualifications = [None] * len(case.required_qualifications)
        forbidden = [None] * len(case.forbidden_claims)
        support = None
    elif not sections:
        required = [False] * len(case.required_claims)
        qualifications = [False] * len(case.required_qualifications)
        forbidden = [False] * len(case.forbidden_claims)
        support = True if abstained else False
    else:
        for field, expected in (
            ("required_claims", case.required_claims),
            ("qualifications", case.required_qualifications),
            ("forbidden_claims", case.forbidden_claims),
            ("sections_fully_supported", sections),
        ):
            if len(getattr(judgment, field)) != len(expected):
                raise ValueError("Judge returned incomplete decisions")
        pairs = [(i, pid) for i, s in enumerate(sections) for pid in s["citation_ids"]]
        if {(c.section_index, c.citation_id) for c in judgment.citations} != set(pairs):
            raise ValueError("Judge citations do not match answer")
        visible = {p["id"]: p["text"] for p in prepared.items}
        citation_values = []
        for citation in judgment.citations:
            if judge_version == 2:
                from researchlens.answer_judge_v2 import citation_value

                citation_values.append(
                    citation_value(citation, sections[citation.section_index], visible)
                )
                continue
            value = citation.value
            section_text = sections[citation.section_index]["text"].strip()
            if section_text and section_text in visible.get(citation.citation_id, ""):
                value = True  # Verbatim extraction is decidable without a semantic judge.
            if value is True and (
                not citation.evidence_quotes
                or any(
                    not q.strip() or q not in visible.get(citation.citation_id, "")
                    for q in citation.evidence_quotes
                )
            ):
                if section_text not in visible.get(citation.citation_id, ""):
                    value = None  # Invented quotes cannot verify semantic support assertions.
            citation_values.append(value)
        required = [d.value for d in judgment.required_claims]
        qualifications = [d.value for d in judgment.qualifications]
        forbidden = [d.value for d in judgment.forbidden_claims]
        support = all_decided(
            citation_values + [d.value for d in judgment.sections_fully_supported]
        )
    no_forbidden = all_decided([None if v is None else not v for v in forbidden])
    abstention_correct = (abstained == case.expected_abstention) if generated else False
    correct = all_decided(
        [
            generated,
            abstention_correct,
            valid,
            support,
            all_decided(required),
            True if case.expected_abstention and abstained else all_decided(qualifications),
            no_forbidden,
        ]
    )
    return {
        "required_claims": required,
        "qualifications": qualifications,
        "forbidden_claims": forbidden,
        "required_claim_coverage": mean(required) if required and None not in required else None,
        "qualification_preservation": mean(qualifications)
        if qualifications and None not in qualifications and not case.expected_abstention
        else None,
        "required_claims_met": all_decided(required) if required else None,
        "qualifications_preserved": all_decided(qualifications)
        if qualifications and not case.expected_abstention
        else None,
        "no_forbidden_claims": no_forbidden,
        "citation_ids_valid": valid if sections else None,
        "citation_support": support if sections else None,
        "abstention_correct": abstention_correct,
        "negative_abstention_correct": abstention_correct if case.expected_abstention else None,
        "answer_correct": correct,
    }


class CostGuard:
    def __init__(self, maximum):
        if not math.isfinite(maximum) or maximum <= 0:
            raise ValueError("--max-cost-usd must be finite and positive")
        self.maximum = maximum
        self.reserved = 0.0
        self.journal = None

    def reserve(self, amount):
        if not math.isfinite(amount) or amount < 0 or self.reserved + amount > self.maximum:
            raise ValueError("Hard cost cap exceeded before call")
        self.reserved += amount  # Failed calls still consume their full reservation.
        if self.journal:
            save(self.journal, {"reserved_usd": self.reserved, "max_cost_usd": self.maximum})
        print(
            f"Before paid call: reserve ${amount:.6f}; total ${self.reserved:.6f} "
            f"/ ${self.maximum:.6f}",
            flush=True,
        )
