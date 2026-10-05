"""Small-pool exact selection over cached utilities, independent of evidence labels."""

from itertools import combinations, islice

import numpy as np


def rank_utilities(scores):
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 2 or not scores.size or not np.isfinite(scores).all():
        raise ValueError("Expected finite requirement/candidate scores")
    utilities = np.zeros_like(scores)
    for row, values in enumerate(scores):
        for rank, index in enumerate(sorted(range(len(values)), key=lambda i: (-values[i], i))):
            utilities[row, index] = 11 / (11 + rank)
    return utilities


def exact_max_utility(utilities, limit=4, original_weight=0.5):
    """Exactly optimize the existing weighted maximum-per-query objective.

    This objective is relevance utility, not evidence sufficiency. Candidate order
    deterministically breaks ties. Enumeration is bounded to 60 candidates/4 slots.
    """
    values = np.asarray(utilities, dtype=np.float64)
    if (
        values.ndim != 2
        or not values.size
        or not np.isfinite(values).all()
        or not 1 <= limit <= min(4, values.shape[1])
        or values.shape[1] > 60
        or not np.isfinite(original_weight)
        or original_weight < 0
    ):
        raise ValueError("Use finite utilities, at most 60 candidates and 1 to 4 slots")
    weights = np.ones(len(values))
    if len(weights) > 1:
        weights[0] = original_weight
    iterator = combinations(range(values.shape[1]), limit)
    best, objective = None, -np.inf
    while batch := list(islice(iterator, 8192)):
        indexes = np.asarray(batch)
        scores = weights @ values[:, indexes].max(axis=2)
        index = int(np.argmax(scores))
        if scores[index] > objective:
            best, objective = batch[index], float(scores[index])
    return list(best)
