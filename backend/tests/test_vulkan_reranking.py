"""Offline GPU-adapter contract checks; no drivers, model downloads or API calls."""

from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from researchlens.evaluation_schema import RerankerConfig, VulkanRerankerConfig
from researchlens.reranking import reranker_metadata
from researchlens.vulkan_experiments import plan
from researchlens.vulkan_reranking import QWEN_TEMPLATE, VulkanReranker, restore_scores


def response(items, tokens=7):
    return {"results": items, "usage": {"total_tokens": tokens}}


def test_restores_response_order_and_rejects_invalid_or_clipped_results():
    items = [{"index": 1, "relevance_score": -2}, {"index": 0, "relevance_score": 3}]
    np.testing.assert_array_equal(restore_scores(response(items), 2, 7), [3, -2])
    for invalid in (
        response(items[:1]),
        response(items, tokens=6),
        response([items[0], items[0]]),
        response([items[0], {"index": 2, "relevance_score": 3}]),
        response([items[0], {"index": True, "relevance_score": 3}]),
        response([items[0], {"index": 0, "relevance_score": float("nan")}]),
        response([items[0], {"index": 0, "relevance_score": float("inf")}]),
        {},
    ):
        with pytest.raises(ValueError, match="invalid scores"):
            restore_scores(invalid, 2, 7)


def test_cpu_contract_remains_unchanged_and_does_not_accept_vulkan_settings():
    cpu = {**reranker_metadata(), "candidates": 40, "diversity": 0.0}
    assert RerankerConfig.model_validate(cpu).model_dump() == cpu
    with pytest.raises(ValueError):
        RerankerConfig.model_validate({**cpu, "device": "Vulkan0"})
    with pytest.raises(ValueError):
        VulkanRerankerConfig.model_validate({**cpu, "runtime": "llama.cpp"})


def test_pair_format_and_reserved_placeholders():
    scorer = object.__new__(VulkanReranker)
    scorer.alias = "qwen"
    scorer.tokenizer = Mock(return_value={"input_ids": [1, 2]})
    assert scorer.pair_tokens("question", "passage") == [1, 2]
    scorer.tokenizer.assert_called_once_with(
        QWEN_TEMPLATE.format(query="question", document="passage"),
        add_special_tokens=False,
        truncation=False,
    )
    for question, passage in (("{document}", "text"), ("query", "{query}")):
        with pytest.raises(ValueError, match="reserved"):
            scorer.pair_tokens(question, passage)
    scorer.alias = "bge"
    scorer.tokenizer.reset_mock()
    scorer.pair_tokens("question", "passage")
    scorer.tokenizer.assert_called_once_with("question", "passage", truncation=False)


def scorer_stub():
    scorer = object.__new__(VulkanReranker)
    scorer.client = Mock()
    scorer.process = SimpleNamespace(poll=lambda: None)
    scorer.metadata = {"max_tokens": 511}
    scorer.last_diagnostics = []
    scorer._last_key = None
    scorer._last_tokens = []
    scorer.pair_tokens = Mock(return_value=[1, 2])
    return scorer


def test_no_silent_truncation_or_empty_requests():
    scorer = scorer_stub()
    assert scorer.score("question", []).shape == (0,)
    scorer.pair_tokens.return_value = [1] * 512
    with pytest.raises(ValueError, match="exceeds 511"):
        scorer.score("question", [SimpleNamespace(id="one", text="passage")])
    scorer.client.post.assert_not_called()


def test_measures_pairs_but_never_caches_inference_scores():
    scorer = scorer_stub()
    scorer.client.post.return_value.json.return_value = response(
        [{"index": 0, "relevance_score": 1}], tokens=2
    )
    passages = [SimpleNamespace(id="one", text="passage")]
    for _ in range(2):
        assert scorer.score("question", passages).tolist() == [1]
    assert scorer.pair_tokens.call_count == 1
    assert scorer.client.post.call_count == 2
    assert scorer.last_diagnostics[0]["retained_ranges"] == [{"start": 0, "end": 7}]
    assert scorer.last_diagnostics[0]["truncated"] is False
    scorer.score("different question", passages)
    assert scorer.pair_tokens.call_count == 2


def test_fixed_development_plan_has_controls_and_both_candidate_pools():
    entries = plan()
    assert len(entries) == 10
    assert len({e["name"] for e in entries}) == 10
    assert sum(e["reranker"] is None for e in entries) == 2
    for model in ("bge-m3", "qwen3-4b"):
        assert {
            (e["reranker"], e["candidates"])
            for e in entries
            if e["model"] == model and e["reranker"]
        } == {(r, n) for r in ("bge", "qwen") for n in (20, 40)}
