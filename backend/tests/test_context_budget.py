import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import tiktoken
from fastapi.testclient import TestClient
from researchlens.answers import (
    INSTRUCTIONS,
    LocalPreview,
    OpenAIProvider,
    ProviderError,
    prepare_answer_context,
)
from researchlens.api import create_app
from researchlens.config import Settings
from researchlens.context_evaluation import context_profile
from researchlens.evaluation_evidence import CaseEvidence
from researchlens.evaluation_metrics import binomial_ci, exact_mcnemar
from researchlens.ingest import TECHNICAL_CORPUS, build_tier_index
from researchlens.models import GeneratedAnswer, SearchHit
from researchlens.retrieval_tiers import tier_settings


def hit(i, text="evidence"):
    return SearchHit(
        id=f"fixture:p{i}:w0",
        document_id="fixture",
        title="Fixture",
        source_url=None,
        license="CC0",
        kind="synthetic",
        paragraph=i,
        text=text,
        score=1 / i,
    )


def test_default_four_and_character_mode_more_than_four():
    hits = [hit(i) for i in range(1, 10)]
    assert len(prepare_answer_context(hits).items) == 4
    prepared = prepare_answer_context(hits, mode="characters")
    assert len(prepared.items) == 9
    assert prepared.diagnostics.max_passages is None


def test_serialized_cap_accounts_for_ids_escaping_and_item_overhead():
    hits = [hit(1, 'σ\\"\n'), hit(2, "x" * 100), hit(3, "x")]
    first = prepare_answer_context(hits[:1], mode="characters")
    size = len(json.dumps(first.items))
    assert size > len(hits[0].text)
    assert (
        prepare_answer_context(hits, mode="characters", max_context_chars=size).supplied == hits[:1]
    )
    # A smaller later item cannot replace the next ranked item.
    assert (
        prepare_answer_context(hits, mode="characters", max_context_chars=size + 80).supplied
        == hits[:1]
    )
    assert prepare_answer_context(hits, mode="characters", max_context_chars=size - 1).items == []


def test_visible_span_scoring_preserves_truncation_and_qualification_views():
    passage = hit(1, "x" * 2999 + "gold")
    entry = CaseEvidence.model_validate(
        {
            "case_id": "case",
            "groups": [
                {
                    "id": "part-1",
                    "claim_index": 0,
                    "description": "Asked",
                    "alternatives": [
                        [{"passage_id": passage.id, "start": 0, "end": 1, "quote": "x"}]
                    ],
                },
                {
                    "id": "qualification",
                    "claim_index": 0,
                    "description": "Extra",
                    "alternatives": [
                        [{"passage_id": passage.id, "start": 2999, "end": 3003, "quote": "gold"}]
                    ],
                },
            ],
        }
    )
    profile = context_profile("Q", [passage], entry, 16000)
    assert profile["all_groups"]["complete_evidence"] is False
    assert profile["all_groups"]["group_coverage"] == 0.5
    assert profile["asked_groups"]["complete_evidence"] is True
    assert profile["context"]["visible_chars"][passage.id] == 3000


def test_offline_profile_matches_actual_mock_provider_input():
    hits = [hit(i, "σ" * 200) for i in range(1, 41)]
    client = Mock()
    client.responses.parse.return_value = SimpleNamespace(
        status="completed",
        usage=None,
        output_parsed=GeneratedAnswer(status="insufficient_evidence", sections=[]),
    )
    provider = OpenAIProvider(
        Settings(answer_context_mode="characters", answer_context_chars=8000), client
    )
    answer = provider.answer("Question?", hits)
    profile = context_profile("Question?", hits, None, 8000)
    payload = client.responses.parse.call_args.kwargs["input"]
    actual = json.loads(payload)["passages"]
    assert len(json.dumps(actual)) <= 8000
    assert [p["id"] for p in actual] == profile["context"]["passage_ids"]
    assert answer.context_diagnostics.model_dump() == profile["context"]
    encoding = tiktoken.get_encoding("o200k_base")
    assert profile["input_tokens_estimate"] == len(encoding.encode(payload)) + len(
        encoding.encode(INSTRUCTIONS)
    )


def test_api_retrieves_character_candidates():
    retriever = Mock()
    retriever.search.return_value = []
    with TestClient(create_app(retriever, Settings(answer_context_mode="characters"))) as client:
        assert client.post("/api/ask", json={"question": "Question?"}).status_code == 200
    retriever.search.assert_called_once_with("Question?", limit=40)


def test_minimal_local_preview_matches_openai_context(tmp_path, monkeypatch):
    build_tier_index("minimal", TECHNICAL_CORPUS, tmp_path)
    monkeypatch.setattr("researchlens.retrieval_tiers.available_memory_gib", lambda: 20)
    settings = Settings(retrieval_tier="minimal", tier_index_dir=tmp_path)
    question = "Why combine forward and backward lighting for aircraft glass canopy inspection?"
    app = create_app(settings=settings)
    with TestClient(app) as client:
        search = Mock(wraps=app.state.retriever.search)
        monkeypatch.setattr(app.state.retriever, "search", search)
        response = client.post("/api/ask", json={"question": question})
        assert response.status_code == 200
        preview = response.json()
        search.assert_called_once_with(question, limit=40)
        hits = search(question, limit=40)

    openai_client = Mock()
    openai_client.responses.parse.return_value = SimpleNamespace(
        status="completed",
        usage=None,
        output_parsed=GeneratedAnswer(status="insufficient_evidence", sections=[]),
    )
    answer = OpenAIProvider(tier_settings(settings, "minimal"), openai_client).answer(
        question, hits
    )
    actual = json.loads(openai_client.responses.parse.call_args.kwargs["input"])["passages"]
    assert len(hits) == 40
    assert 4 < len(preview["passages"]) < 40
    assert preview["passages"] == [p.model_dump(mode="json") for p in answer.passages]
    assert [p["id"] for p in preview["passages"]] == [p["id"] for p in actual]
    assert answer.passages == hits[: len(answer.passages)]
    assert len(json.dumps(actual)) <= 16000
    next_hit = hits[len(actual)]
    next_item = {"id": next_hit.id, "kind": next_hit.kind, "text": next_hit.text[:3000]}
    assert len(json.dumps([*actual, next_item])) > 16000
    assert preview["context_diagnostics"] == answer.context_diagnostics.model_dump()
    assert preview["estimated_api_cost_usd"] == 0


@pytest.mark.parametrize("settings", [None, Settings(answer_context_chars=7000)])
def test_local_preview_passages_mode_preserves_full_text(settings):
    hits = [hit(i, "x" * 3500) for i in range(1, 10)]
    provider = LocalPreview() if settings is None else LocalPreview(settings)
    answer = provider.answer("Question?", hits)
    expected_count = 4 if settings is None else 2
    assert answer.passages == hits[:expected_count]
    assert answer.context_diagnostics.truncated_passage_ids == [p.id for p in hits[:expected_count]]
    assert all(len(p.text) == 3500 for p in answer.passages)


def test_local_preview_api_without_tier_returns_four():
    hits = [hit(i) for i in range(1, 10)]
    retriever = Mock()
    retriever.search.side_effect = lambda question, limit: hits[:limit]
    with TestClient(create_app(retriever, Settings())) as client:
        response = client.post("/api/ask", json={"question": "Question?"})
        assert response.status_code == 200
        assert response.json()["passages"] == [p.model_dump() for p in hits[:4]]
    retriever.search.assert_called_once_with("Question?", limit=4)


def test_local_preview_rejects_context_that_cannot_fit():
    provider = LocalPreview(Settings(answer_context_mode="characters", answer_context_chars=2))
    with pytest.raises(ProviderError, match="Retrieved passages exceed the supported context size"):
        provider.answer("Question?", [hit(1)])


@pytest.mark.parametrize(
    "settings",
    [
        {"answer_context_chars": 16001},
        {"answer_context_mode": "invalid"},
        {"answer_context_candidates": 20},
        {
            "answer_context_mode": "characters",
            "retrieval": "embeddings",
            "reranker": "minilm",
            "reranking_candidates": 20,
        },
    ],
)
def test_invalid_context_settings(settings):
    with pytest.raises(ValueError):
        Settings(**settings)


def test_exact_statistics_and_unscored_pairs():
    assert binomial_ci(0, 36)[0] == 0
    assert binomial_ci(36, 36)[1] == 1
    assert binomial_ci(29, 36) == pytest.approx([0.6397519918, 0.9180563608])
    baseline = {str(i): False for i in range(5)} | {"negative": None}
    candidate = {str(i): True for i in range(5)} | {"negative": None}
    stats = exact_mcnemar(baseline, candidate)
    assert stats["gains"] == 5 and stats["losses"] == 0
    assert stats["p_two_sided"] == 0.0625
    assert stats["paired_cases"] == 5 and stats["excluded_unscored_cases"] == 1
    assert exact_mcnemar(baseline, baseline)["p_two_sided"] == 1
    with pytest.raises(ValueError):
        exact_mcnemar(baseline, {})
