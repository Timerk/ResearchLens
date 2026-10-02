"""Fixed-candidate selection policies, independent of evaluation labels and models."""

import hashlib

import numpy as np

from researchlens.evidence_selection import select_complementary
from researchlens.models import SearchHit

POLICIES = (
    "dense-order",
    "whole-rerank",
    "rules-max",
    "needs-max",
    "needs-saturation",
    "needs-round-robin",
)


def select_indices(scores, limit, policy, redundancy=None):
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 2 or not scores.shape[0] or not np.isfinite(scores).all():
        raise ValueError("Expected a finite query/candidate score matrix")
    if not 1 <= limit <= scores.shape[1] or policy not in POLICIES:
        raise ValueError("Invalid fixed-pool selection policy or limit")
    ranks = np.zeros_like(scores)
    for row, values in enumerate(scores):
        for rank, index in enumerate(sorted(range(len(values)), key=lambda i: (-values[i], i))):
            ranks[row, index] = 11 / (11 + rank)
    if policy in ("dense-order", "whole-rerank"):
        return sorted(range(scores.shape[1]), key=lambda i: (-scores[0, i], i))[:limit]
    if policy in ("rules-max", "needs-max"):
        return select_complementary(ranks, limit)
    if policy == "needs-round-robin":
        selected = []
        rows = list(range(1, len(scores))) or [0]
        while len(selected) < limit:
            for row in rows:
                index = max(
                    (i for i in range(scores.shape[1]) if i not in selected),
                    key=lambda i: (scores[row, i], scores[0, i], -i),
                )
                selected.append(index)
                if len(selected) == limit:
                    break
        return selected
    if redundancy is None or redundancy.shape != (scores.shape[1], scores.shape[1]):
        raise ValueError("Saturation selection requires candidate cosine similarities")
    if not np.isfinite(redundancy).all():
        raise ValueError("Candidate similarities must be finite")
    # Sigmoid is an uncalibrated saturation utility, NOT a factual-support probability.
    utility = 1 / (1 + np.exp(-np.clip(scores, -40, 40)))
    weights = np.ones(len(scores))
    if len(weights) > 1:
        weights[0] = 0.25
    remaining = np.ones(len(scores))
    selected = []
    for _ in range(limit):
        gain = weights @ (remaining[:, None] * utility)
        if selected:
            gain -= 0.1 * np.maximum(redundancy[:, selected], 0).max(axis=1)
        index = max(
            (i for i in range(scores.shape[1]) if i not in selected),
            key=lambda i: (gain[i], scores[0, i], -i),
        )
        selected.append(index)
        remaining *= 1 - utility[:, index]
    return selected


class FixedPoolSelector:
    """Replay immutable model measurements to isolate selection; never infer answerability."""

    def __init__(self, bundle, passages, vectors, policy, bundle_hash):
        if policy not in POLICIES:
            raise ValueError("Unsupported fixed-pool policy")
        self.bundle, self.passages, self.vectors, self.policy = bundle, passages, vectors, policy
        self.by_id = {p.id: i for i, p in enumerate(passages)}
        self.cases = {row["question_sha256"]: row for row in bundle["cases"]}
        self.last_record = None
        self.information_settings = {
            "version": "fixed-information-needs-v1",
            "policy": policy,
            "input_bundle_sha256": bundle_hash,
            "candidate_count": 40,
            "timing_scope": "replay-selection-only",
        }
        if policy != "dense-order":
            self.reranking_settings = {
                **bundle["manifest"]["reranker"],
                "candidates": 40,
                "diversity": 0.0,
            }

    def get_encoding_diagnostics(self):
        return self.bundle["encoding_diagnostics"]

    def get_reranking_diagnostics(self, question):
        row = self.cases.get(hashlib.sha256(question.encode()).hexdigest())
        return row["original_pair_diagnostics"] if row and self.policy != "dense-order" else []

    def search(self, question, limit=4):
        row = self.cases.get(hashlib.sha256(question.encode()).hexdigest())
        if row is None:
            raise ValueError("Question is absent from the frozen development measurement bundle")
        if row.get("error") and self.policy.startswith("needs-"):
            raise ValueError("Question measurement failed; no silent decomposition fallback")
        ids = row["candidate_ids"]
        if self.policy == "dense-order":
            scores = [row["dense_scores"]]
        else:
            queries = row["rule_scores"] if self.policy == "rules-max" else row["need_scores"]
            scores = [row["original_scores"]] + (queries if self.policy != "whole-rerank" else [])
        positions = [self.by_id[i] for i in ids]
        matrix = self.vectors[positions]
        chosen = select_indices(scores, limit, self.policy, matrix @ matrix.T)
        self.last_record = {"candidate_ids": ids, "selected_ids": [ids[i] for i in chosen]}
        return [
            SearchHit(**self.passages[positions[i]].model_dump(), score=float(scores[0][i]))
            for i in chosen
        ]
