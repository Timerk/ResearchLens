"""Evaluation-only question decomposition and complementary passage selection.

Inputs are a question and indexed passages. No evaluation cases, claims or labels
enter this module. Canonical text and citation identities are never modified.
"""

import hashlib
import re
from collections import Counter
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from researchlens.artifacts import canonical_hash

GENERIC = set(ENGLISH_STOP_WORDS) | {
    "study",
    "using",
    "based",
    "approach",
    "method",
    "model",
    "system",
    "training",
    "detection",
    "inspection",
    "defect",
    "surface",
    "data",
    "results",
    "reported",
    "learning",
    "image",
    "network",
    "control",
    "quality",
    "paper",
    "proposed",
}


def terms(text):
    words = re.findall(r"[a-z]+", text.lower())
    # A deliberately small, deterministic plural normalizer, not a domain alias list.
    words = [w[:-3] + "y" if w.endswith("ies") else w[:-1] if w.endswith("s") else w for w in words]
    return {w for w in words if len(w) >= 4 and w not in GENERIC}


@dataclass(frozen=True)
class Facet:
    query: str
    document_id: str | None = None


class QuestionDecomposer:
    """Bounded rules over question grammar and title/first-paragraph corpus profiles."""

    def __init__(self, passages):
        self.profiles = {}
        for passage in passages:
            self.profiles.setdefault(
                passage.document_id,
                {
                    "title": passage.title,
                    "text": passage.text,
                },
            )
        vocab = {doc: terms(p["title"] + " " + p["text"]) for doc, p in self.profiles.items()}
        frequencies = Counter(w for words in vocab.values() for w in words)
        self.anchors = {
            doc: {w for w in words if frequencies[w] == 1} for doc, words in vocab.items()
        }
        self.profile_sha256 = canonical_hash(self.profiles)

    def split(self, question):
        original = Facet(question)
        query_terms = terms(question)
        matches = [doc for doc in self.profiles if query_terms & self.anchors[doc]]
        multipart = re.search(r"\b(?:compare|differ|both|each|and|with)\b", question, re.I)
        if multipart and len(matches) == 2:
            parts = [
                Facet(question + "\nFocus on this study: " + self.profiles[doc]["title"], doc)
                for doc in matches
            ]
        else:
            pieces = re.split(
                r",\s*(?:and\s+)?(?=(?:what|why|how|which|is|are|can)\b)"
                r"|\s+and\s+(?=(?:what|why|how|which|is|are|can)\b)|[?;]",
                question,
                flags=re.I,
            )
            pieces = [p.strip(" ,?") for p in pieces if len(p.split()) >= 4]
            prefix = re.match(r"^(?:In|For|According to)\b[^,]{0,180},", question, re.I)
            parts = []
            if len(pieces) >= 2:
                for piece in pieces[:2]:
                    query = (
                        piece
                        if not prefix or piece.startswith(prefix[0])
                        else prefix[0] + " " + piece
                    )
                    if len(matches) == 1:
                        query += "\nStudy: " + self.profiles[matches[0]]["title"]
                    parts.append(Facet(query))
        # Internal queries respect the existing user-question length budget too.
        return [original] + [p for p in parts if p.query != question and len(p.query) <= 2000][:2]


def scoring_text(passage, representation):
    if representation == "passage-text-only":
        return passage.text
    if representation != "title-section-text-v1":
        raise ValueError("Unknown reranking representation")
    return f"Title: {passage.title}\nSection: {passage.source_section or ''}\n\n{passage.text}"


def select_complementary(utilities, limit, original_weight=0.5):
    """Greedy diminishing coverage over query facets, without relevance thresholds."""
    if utilities.ndim != 2 or not np.isfinite(utilities).all():
        raise ValueError("Selection utilities must be a finite query/candidate matrix")
    selected = []
    covered = np.zeros(utilities.shape[0])
    weights = np.ones(utilities.shape[0])
    if len(weights) > 1:
        weights[0] = original_weight
    for _ in range(min(limit, utilities.shape[1])):
        gains = weights @ np.maximum(utilities - covered[:, None], 0)
        for index in selected:
            gains[index] = -np.inf
        # Original-query utility fills spare slots once each facet's best is covered.
        chosen = max(
            (i for i in range(len(gains)) if i not in selected),
            key=lambda i: (gains[i], utilities[0, i], -i),
        )
        selected.append(chosen)
        covered = np.maximum(covered, utilities[:, chosen])
    return selected


class EvidenceSelector:
    """Retrieve per facet, retain original candidates, optionally rerank, select four."""

    def __init__(
        self,
        base,
        reranker=None,
        *,
        decompose=True,
        complementary=True,
        representation="passage-text-only",
        candidates=40,
        per_query=20,
    ):
        if not 1 <= per_query <= candidates <= 100:
            raise ValueError("Use 1 <= per_query <= candidates <= 100")
        scoring_text(base.passages[0], representation)
        self.base, self.reranker = base, reranker
        self.passages = base.passages
        self.decomposer = QuestionDecomposer(self.passages)
        self.decompose, self.complementary = decompose, complementary
        self.representation, self.candidates, self.per_query = representation, candidates, per_query
        self.positions = {p.id: i for i, p in enumerate(self.passages)}
        self.last_selection = {}
        self._question_hash = None
        self._pair_diagnostics = []
        if reranker:
            self.reranking_settings = {
                **reranker.metadata,
                "candidates": candidates,
                "diversity": 0.0,
            }
        self.selection_settings = {
            "version": "facets-v1",
            "decompose": decompose,
            "complementary": complementary,
            "candidates": candidates,
            "per_query": per_query,
            "max_queries": 3,
            "reranking_representation": representation,
            "original_weight": 0.5,
            "profile_sha256": self.decomposer.profile_sha256,
            "document_profile": "title-first-passage-v1",
            "rank_constant": 10,
        }

    def get_encoding_diagnostics(self):
        return self.base.get_encoding_diagnostics()

    def get_reranking_diagnostics(self, question):
        return (
            self._pair_diagnostics
            if self._question_hash == hashlib.sha256(question.encode()).hexdigest()
            else []
        )

    def search(self, question, limit=4):
        if not 1 <= limit <= self.per_query:
            raise ValueError("Output limit must fit the original query's candidate budget")
        facets = self.decomposer.split(question) if self.decompose else [Facet(question)]
        rankings = [self.base.search(f.query, len(self.passages)) for f in facets]
        routes = [
            [h for h in hits if f.document_id is None or h.document_id == f.document_id][
                : self.per_query
            ]
            for f, hits in zip(facets, rankings, strict=True)
        ]
        pool = {h.id: h for h in routes[0]}
        for rank in range(self.per_query):
            for route in routes[1:]:
                if rank < len(route) and len(pool) < self.candidates:
                    pool.setdefault(route[rank].id, route[rank])
        hits = list(pool.values())
        if not hits:
            self.last_selection = {"queries": [], "candidate_ids": [], "selected_ids": []}
            self._pair_diagnostics = []
            return []
        values = []
        query_diagnostics = []
        for query_index, (facet, ranking) in enumerate(zip(facets, rankings, strict=True)):
            if self.reranker:
                inputs = [
                    h.model_copy(update={"text": scoring_text(h, self.representation)})
                    for h in hits
                ]
                scores = np.asarray(self.reranker.score(facet.query, inputs))
                if scores.shape != (len(hits),) or not np.isfinite(scores).all():
                    raise ValueError("Reranker returned invalid facet scores")
                diagnostics = []
                for h, measured in zip(hits, self.reranker.last_diagnostics, strict=True):
                    actual_text = scoring_text(h, self.representation)
                    if (
                        measured["passage_id"] != h.id
                        or measured["truncated"]
                        or measured["input_tokens"] != measured["encoded_tokens"]
                        or measured["text_sha256"]
                        != hashlib.sha256(actual_text.encode()).hexdigest()
                    ):
                        raise ValueError(
                            "Facet reranking requires complete, ordered passage measurements"
                        )
                    diagnostics.append(
                        {
                            **measured,
                            "text_sha256": hashlib.sha256(h.text.encode()).hexdigest(),
                            "retained_ranges": [{"start": 0, "end": len(h.text)}],
                        }
                    )
                query_diagnostics.append(diagnostics)
                if query_index == 0:
                    self._pair_diagnostics = diagnostics
            else:
                by_id = {h.id: h.score for h in ranking}
                scores = np.array([by_id[h.id] for h in hits])
            values.append(scores)
        utilities = np.zeros((len(facets), len(hits)))
        for row, (facet, scores) in enumerate(zip(facets, values, strict=True)):
            allowed = [
                i
                for i, h in enumerate(hits)
                if facet.document_id is None or h.document_id == facet.document_id
            ]
            ordered = sorted(allowed, key=lambda i: (-scores[i], self.positions[hits[i].id]))
            for rank, i in enumerate(ordered):
                utilities[row, i] = 11 / (11 + rank)
        chosen = (
            select_complementary(utilities, limit)
            if self.complementary
            else sorted(
                range(len(hits)), key=lambda i: (-values[0][i], self.positions[hits[i].id])
            )[:limit]
        )
        self._question_hash = hashlib.sha256(question.encode()).hexdigest()
        self.last_selection = {
            "queries": [{"query": f.query, "document_id": f.document_id} for f in facets],
            "candidate_ids": [h.id for h in hits],
            "selected_ids": [hits[i].id for i in chosen],
            "query_pair_diagnostics": query_diagnostics,
        }
        return [hits[i].model_copy(update={"score": float(values[0][i])}) for i in chosen]
