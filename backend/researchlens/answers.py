from typing import Protocol

from researchlens.models import Answer, SearchHit


class AnswerProvider(Protocol):
    def answer(self, question: str, passages: list[SearchHit]) -> Answer: ...


class LocalPreview:
    """Return evidence for inspection without pretending to generate an LLM answer."""

    def answer(self, question: str, passages: list[SearchHit]) -> Answer:
        return Answer(
            status="passages_found" if passages else "no_matches",
            message=(
                "These passages share terms with your question. Review them below; "
                "this preview cannot determine whether they answer it."
                if passages
                else "No matching passages were found. This does not prove the corpus "
                "has no answer: lexical search can miss synonyms."
            ),
            passages=passages,
            latency_ms=0,
        )
