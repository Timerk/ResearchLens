"""Functional diagnostic contracts, including joint evidence and greedy traps."""

import numpy as np
import pytest
from researchlens.evaluation_evidence import CaseEvidence
from researchlens.evidence_selection import select_complementary
from researchlens.selection_diagnostics import constrained_oracle
from researchlens.set_selection import exact_max_utility, rank_utilities


def entry(options):
    return CaseEvidence.model_validate(
        {
            "case_id": "test",
            "groups": [
                {
                    "id": str(i),
                    "claim_index": i,
                    "description": "fact",
                    "alternatives": [
                        [{"passage_id": pid, "start": 0, "end": 1, "quote": "x"} for pid in option]
                        for option in alternatives
                    ],
                }
                for i, alternatives in enumerate(options)
            ],
        }
    )


def test_oracle_requires_joint_support_and_respects_slot_budget():
    labels = entry([[["a", "b", "c"]], [["d", "e"]]])
    assert not constrained_oracle(labels, list("abcde"))["complete"]
    assert constrained_oracle(labels, list("abcde"))["covered"] == 1
    labels = entry([[["a", "b"], ["x"]], [["c", "d"]]])
    assert constrained_oracle(labels, list("abcd"))["witness"] == list("abcd")
    assert constrained_oracle(labels, list("abcdx"))["witness"] == ["c", "d", "x"]
    assert not constrained_oracle(labels, list("abc"))["complete"]


def test_oracle_does_not_mix_incomplete_alternatives():
    labels = entry([[["a", "b"], ["c", "d"]]])
    assert not constrained_oracle(labels, ["a", "c"])["complete"]
    with pytest.raises(ValueError):
        constrained_oracle(labels, ["a", "a"])


def test_exact_objective_resolves_a_greedy_trap_without_labels():
    values = np.array([[0.6, 1, 0], [0.6, 0, 1]])
    greedy = select_complementary(values, 2, original_weight=1)
    exact = exact_max_utility(values, 2, original_weight=1)
    assert greedy == [0, 1]
    assert exact == [1, 2]
    assert values[:, exact].max(axis=1).sum() > values[:, greedy].max(axis=1).sum()


def test_exact_ties_and_relevance_ranks_are_deterministic():
    assert exact_max_utility(np.ones((2, 5))) == [0, 1, 2, 3]
    np.testing.assert_allclose(rank_utilities([[2, 2, 0]]), [[1, 11 / 12, 11 / 13]])
    with pytest.raises(ValueError):
        exact_max_utility([[np.nan]])
    with pytest.raises(ValueError):
        exact_max_utility(np.ones((1, 61)))
