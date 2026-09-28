import json
import logging
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)
from researchlens.answers import OpenAIProvider, ProviderError
from researchlens.api import create_app
from researchlens.config import Settings
from researchlens.models import GeneratedAnswer, SearchHit


@pytest.fixture
def hit():
    return SearchHit(
        id="fixture:p1:w0",
        document_id="fixture",
        title="Test fixture",
        source_url=None,
        license="CC0",
        kind="synthetic",
        paragraph=1,
        text="Dust scattered light.",
        score=0.8,
    )


@pytest.fixture
def sdk():
    client = Mock()
    client.responses.parse.return_value = SimpleNamespace(
        status="completed",
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
        output_parsed=GeneratedAnswer(
            status="answered",
            sections=[
                {
                    "text": "In the test fixture, dust scattered light.",
                    "citation_ids": ["fixture:p1:w0"],
                }
            ],
        ),
    )
    return client


def provider(sdk):
    return OpenAIProvider(Settings(provider="openai", api_key="fake-test-key"), client=sdk)


def test_supported_answer_and_request_boundaries(sdk, hit):
    result = provider(sdk).answer("What did dust do?", [hit])
    assert result.status == "answered"
    assert result.sections[0].citation_ids == [hit.id]
    assert (result.input_tokens, result.output_tokens) == (100, 50)
    assert result.estimated_api_cost_usd is None
    kwargs = sdk.responses.parse.call_args.kwargs
    assert kwargs["model"] == "gpt-6-luna"
    assert kwargs["reasoning"] == {"effort": "medium"}
    assert kwargs["max_output_tokens"] == 2000
    assert kwargs["store"] is False
    assert "tools" not in kwargs and "previous_response_id" not in kwargs
    assert json.loads(kwargs["input"])["passages"] == [
        {"id": hit.id, "kind": "synthetic", "text": hit.text}
    ]


def test_no_matches_never_calls_openai(sdk):
    result = provider(sdk).answer("Who composed symphonies?", [])
    assert result.status == "no_matches"
    assert result.estimated_api_cost_usd == 0
    sdk.responses.parse.assert_not_called()


def test_usage_log_excludes_question_and_passage_contents(sdk, hit, caplog):
    with caplog.at_level(logging.INFO, logger="uvicorn.error.researchlens"):
        provider(sdk).answer("Private question content", [hit])
    assert "model=gpt-6-luna" in caplog.text
    assert "input_tokens=100 output_tokens=50" in caplog.text
    assert "latency_ms=" in caplog.text
    assert "Private question content" not in caplog.text
    assert hit.text not in caplog.text
    assert "fake-test-key" not in caplog.text


def test_insufficient_evidence(sdk, hit):
    sdk.responses.parse.return_value.output_parsed = GeneratedAnswer(
        status="insufficient_evidence",
        sections=[],
    )
    result = provider(sdk).answer("What was the exact defect size?", [hit])
    assert result.status == "insufficient_evidence"
    assert result.sections == []
    assert result.passages == [hit]


@pytest.mark.parametrize(
    "status,sections",
    [
        ("answered", []),
        ("answered", [{"text": "A claim", "citation_ids": ["invented-id"]}]),
        ("answered", [{"text": "   ", "citation_ids": ["fixture:p1:w0"]}]),
        ("insufficient_evidence", [{"text": "A claim", "citation_ids": ["fixture:p1:w0"]}]),
    ],
)
def test_rejects_invalid_evidence(sdk, hit, status, sections):
    sdk.responses.parse.return_value.output_parsed = GeneratedAnswer(
        status=status, sections=sections
    )
    with pytest.raises(ProviderError, match="invalid evidence"):
        provider(sdk).answer("Question", [hit])


@pytest.mark.parametrize("status,parsed", [("incomplete", True), ("completed", False)])
def test_rejects_incomplete_and_refused_answers(sdk, hit, status, parsed):
    sdk.responses.parse.return_value.status = status
    if not parsed:
        sdk.responses.parse.return_value.output_parsed = None
    with pytest.raises(ProviderError, match="complete answer"):
        provider(sdk).answer("Question", [hit])


def test_context_bound_and_only_supplied_citations(sdk, hit):
    hits = [hit.model_copy(update={"id": f"passage-{i}", "text": "é" * 10000}) for i in range(8)]
    # Escaped Unicode exceeds the budget; no request should be made.
    with pytest.raises(ProviderError, match="context size"):
        provider(sdk).answer("Question", hits)
    sdk.responses.parse.assert_not_called()
    hits = [hit.model_copy(update={"id": f"passage-{i}", "text": "x" * 10000}) for i in range(8)]
    with pytest.raises(ProviderError, match="invalid evidence"):
        provider(sdk).answer("Question", hits)
    context = json.loads(sdk.responses.parse.call_args.kwargs["input"])["passages"]
    assert len(context) == 4
    assert len(json.dumps(context)) <= OpenAIProvider.MAX_CONTEXT_CHARS
    assert all(len(item["text"]) <= 3000 for item in context)


@pytest.mark.parametrize(
    "kind,code",
    [
        (AuthenticationError, 503),
        (RateLimitError, 429),
        (APITimeoutError, 504),
        (APIConnectionError, 503),
        (APIStatusError, 502),
        (ValueError, 502),
    ],
)
def test_api_errors_are_safe_and_not_retried(sdk, hit, kind, code):
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    if kind is APITimeoutError:
        error = kind(request=request)
    elif kind is APIConnectionError:
        error = kind(message="secret upstream detail", request=request)
    elif kind is ValueError:
        error = kind("secret upstream detail")
    else:
        error = kind(
            "secret upstream detail", response=httpx.Response(400, request=request), body=None
        )
    sdk.responses.parse.side_effect = error
    retriever = Mock()
    retriever.search.return_value = [hit]
    with TestClient(
        create_app(retriever, Settings(provider="openai", api_key="fake"), provider(sdk))
    ) as client:
        assert client.get("/api/health").json()["mode"] == "openai"
        response = client.post("/api/ask", json={"question": "What did dust do?"})
    assert response.status_code == code
    assert "secret" not in response.text
    assert sdk.responses.parse.call_count == 1


def test_configuration_loading_and_precedence(tmp_path, monkeypatch):
    for name in ("ANSWER_PROVIDER", "OPENAI_API_KEY", "OPENAI_MODEL"):
        monkeypatch.delenv(name, raising=False)
    env = tmp_path / ".env"
    env.write_text("ANSWER_PROVIDER=openai\nOPENAI_API_KEY=file-secret\nOPENAI_MODEL=gpt-6-luna\n")
    settings = Settings.from_env(env)
    assert settings.api_key == "file-secret"
    assert "file-secret" not in repr(settings)
    monkeypatch.setenv("OPENAI_API_KEY", "process-secret")
    assert Settings.from_env(env).api_key == "process-secret"
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with pytest.raises(ValueError, match="requires"):
        Settings.from_env(env)
    monkeypatch.setenv("ANSWER_PROVIDER", "invalid")
    with pytest.raises(ValueError, match="ANSWER_PROVIDER"):
        Settings.from_env(env)


def test_startup_rejects_missing_key(monkeypatch):
    monkeypatch.setattr(Settings, "from_env", lambda: Settings(provider="openai"))
    with pytest.raises(ValueError, match="requires"), TestClient(create_app(Mock())):
        pass


def test_client_has_timeout_no_retries_and_official_endpoint(monkeypatch):
    client = Mock()
    factory = Mock(return_value=client)
    monkeypatch.setattr("researchlens.answers.OpenAI", factory)
    instance = OpenAIProvider(Settings(provider="openai", api_key="fake"))
    assert factory.call_args.kwargs == {
        "api_key": "fake",
        "base_url": "https://api.openai.com/v1",
        "timeout": 45.0,
        "max_retries": 0,
    }
    instance.close()
    client.close.assert_called_once()
