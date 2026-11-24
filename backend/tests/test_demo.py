"""Public demo controls. Every test is offline; OpenAI clients are mocks."""

import logging
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import AuthenticationError
from researchlens.answers import OpenAIProvider, ProviderError
from researchlens.api import create_app
from researchlens.config import Settings
from researchlens.demo import (
    NOTICES,
    RECORDINGS,
    DemoConfig,
    load_recordings,
    read_visitor_key,
)
from researchlens.models import GeneratedAnswer, SearchHit
from researchlens.rate_limit import (
    LiveAnswerQuota,
    MemoryQuotaStore,
    SQLiteQuotaStore,
    client_address,
    network_key,
)
from researchlens_eval import demo_recordings

VISITOR_KEY = "sk-proj-visitorSecret_0123456789abcdefXYZ"
SERVER_KEY = "sk-server-secret-0123456789abcdef"
QUESTION = {"question": "What did dust do?"}


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
def retriever(hit):
    mock = Mock()
    mock.search.return_value = [hit]
    return mock


def parsed_response():
    return SimpleNamespace(
        status="completed",
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
        output_parsed=GeneratedAnswer(
            status="answered",
            sections=[
                {"text": "In the fixture, dust scattered light.", "citation_ids": ["fixture:p1:w0"]}
            ],
        ),
    )


@pytest.fixture
def sdk():
    client = Mock()
    client.responses.parse.return_value = parsed_response()
    return client


@pytest.fixture
def openai_factory(monkeypatch):
    """Replace the OpenAI SDK constructor; records every key a client is built with."""
    clients = []

    def factory(**kwargs):
        client = Mock()
        client.kwargs = kwargs
        client.responses.parse.return_value = parsed_response()
        clients.append(client)
        return client

    monkeypatch.setattr("researchlens.answers.OpenAI", factory)
    return clients


def live_app(retriever, sdk, demo=None, store=None, verify=None):
    settings = Settings(provider="openai", api_key=SERVER_KEY)
    return create_app(
        retriever,
        settings,
        OpenAIProvider(settings, client=sdk),
        demo or DemoConfig(),
        store,
        verify,
    )


def test_live_answers_count_down_then_fall_back_to_preview_with_429(retriever, sdk):
    demo = DemoConfig(visitor_daily_limit=2, global_daily_limit=50)
    with TestClient(live_app(retriever, sdk, demo)) as client:
        assert client.get("/api/demo").json()["visitor_remaining"] == 2
        first = client.post("/api/ask", json=QUESTION)
        assert first.status_code == 200
        assert first.json()["status"] == "answered"
        assert first.json()["live_answers_remaining"] == 1
        assert client.post("/api/ask", json=QUESTION).json()["live_answers_remaining"] == 0
        limited = client.post("/api/ask", json=QUESTION)
        status = client.get("/api/demo").json()
    assert limited.status_code == 429
    body = limited.json()
    assert body["status"] == "passages_found"
    assert body["mode"] == "local_preview"
    assert body["fallback_reason"] == "visitor_limit"
    assert body["notice"] == body["detail"] == NOTICES["visitor_limit"]
    assert [p["id"] for p in body["passages"]] == ["fixture:p1:w0"]
    assert 1 <= int(limited.headers["retry-after"]) <= 86400
    assert sdk.responses.parse.call_count == 2
    assert (status["visitor_remaining"], status["remaining_today"]) == (0, 48)


def test_global_daily_cap_applies_across_visitors(retriever, sdk):
    demo = DemoConfig(visitor_daily_limit=5, global_daily_limit=2)
    with TestClient(live_app(retriever, sdk, demo)) as client:
        for address in ("203.0.113.1", "203.0.113.2"):
            response = client.post("/api/ask", json=QUESTION, headers={"X-Forwarded-For": address})
            assert response.status_code == 200
        third = client.post("/api/ask", json=QUESTION, headers={"X-Forwarded-For": "203.0.113.3"})
    assert third.status_code == 429
    assert third.json()["fallback_reason"] == "daily_limit"
    assert sdk.responses.parse.call_count == 2


def test_quota_uses_the_injected_store_and_no_matches_are_free(retriever, sdk):
    store = Mock(wraps=MemoryQuotaStore())
    retriever.search.return_value = []
    with TestClient(live_app(retriever, sdk, store=store)) as client:
        response = client.post("/api/ask", json=QUESTION)
    assert response.json()["status"] == "no_matches"
    store.consume.assert_not_called()
    sdk.responses.parse.assert_not_called()


def test_rejected_quota_from_store_never_calls_openai(retriever, sdk):
    store = Mock()
    store.secret.return_value = b"k" * 32
    store.consume.return_value = SimpleNamespace(
        allowed=False, reason="daily_limit", visitor_remaining=5, global_remaining=0
    )
    with TestClient(live_app(retriever, sdk, store=store)) as client:
        response = client.post("/api/ask", json=QUESTION)
    assert response.status_code == 429
    assert response.json()["fallback_reason"] == "daily_limit"
    sdk.responses.parse.assert_not_called()
    day, visitor, visitor_limit, global_limit = store.consume.call_args.args
    assert (visitor_limit, global_limit) == (5, 50)
    assert "testclient" not in visitor and len(visitor) == 32


def test_openai_budget_limit_degrades_to_preview(retriever, sdk):
    provider = Mock()
    provider.answer.side_effect = ProviderError("OpenAI rate or quota limit reached.", 429)
    settings = Settings(provider="openai", api_key=SERVER_KEY)
    with TestClient(create_app(retriever, settings, provider)) as client:
        response = client.post("/api/ask", json=QUESTION)
    assert response.status_code == 429
    assert response.json()["fallback_reason"] == "provider_limit"
    assert response.json()["mode"] == "local_preview"


def test_other_provider_errors_are_still_reported(retriever):
    provider = Mock()
    provider.answer.side_effect = ProviderError("OpenAI timed out. Please try again.", 504)
    settings = Settings(provider="openai", api_key=SERVER_KEY)
    with TestClient(create_app(retriever, settings, provider)) as client:
        response = client.post("/api/ask", json=QUESTION)
    assert response.status_code == 504
    assert response.json() == {"detail": "OpenAI timed out. Please try again."}


def test_sqlite_store_persists_across_restarts(tmp_path):
    path = tmp_path / "state" / "quota.sqlite3"
    first = LiveAnswerQuota(SQLiteQuotaStore(path), 2, 10, today=lambda: "2026-11-24")
    assert first.consume("198.51.100.7").allowed
    restarted = LiveAnswerQuota(SQLiteQuotaStore(path), 2, 10, today=lambda: "2026-11-24")
    assert restarted.remaining("198.51.100.7") == (1, 9)
    assert restarted.consume("198.51.100.7").allowed
    assert restarted.consume("198.51.100.7").reason == "visitor_limit"
    assert b"198.51.100.7" not in path.read_bytes()
    tomorrow = LiveAnswerQuota(SQLiteQuotaStore(path), 2, 10, today=lambda: "2026-11-25")
    assert tomorrow.remaining("198.51.100.7") == (2, 10)


def test_sqlite_store_prunes_old_days(tmp_path):
    store = SQLiteQuotaStore(tmp_path / "quota.sqlite3")
    store.consume("2026-11-20", "a", 5, 5)
    store.consume("2026-11-24", "a", 5, 5)
    assert store.counts("2026-11-20", "a") == (0, 0)
    assert store.counts("2026-11-24", "a") == (1, 1)


@pytest.mark.parametrize(
    ("forwarded", "hops", "expected"),
    [
        (None, 1, "10.0.0.9"),
        ("203.0.113.5", 1, "203.0.113.5"),
        ("1.2.3.4, 203.0.113.5", 1, "203.0.113.5"),  # spoofed prefix ignored
        ("1.2.3.4, 203.0.113.5, 172.18.0.4", 2, "203.0.113.5"),
        ("203.0.113.5", 2, "203.0.113.5"),
        ("not-an-ip", 1, "10.0.0.9"),
        ("203.0.113.5", 0, "10.0.0.9"),
    ],
)
def test_client_address_trusts_only_configured_proxy_hops(forwarded, hops, expected):
    assert client_address(forwarded, "10.0.0.9", hops) == expected


def test_ipv6_visitors_share_a_slash_64_quota():
    assert network_key("2001:db8:1:2:aaaa::1") == network_key("2001:db8:1:2:bbbb::2")
    assert network_key("2001:db8:1:3::1") != network_key("2001:db8:1:2::1")
    assert network_key("::ffff:203.0.113.5") == "203.0.113.5"


def test_demo_only_kill_switch_never_builds_a_paid_client(monkeypatch, retriever):
    factory = Mock(side_effect=AssertionError("OpenAI client constructed"))
    monkeypatch.setattr("researchlens.answers.OpenAI", factory)
    settings = Settings(provider="openai", api_key=SERVER_KEY)
    demo = DemoConfig(demo_only=True, allow_visitor_keys=True)
    with TestClient(create_app(retriever, settings, demo=demo)) as client:
        health = client.get("/api/health").json()
        status = client.get("/api/demo").json()
        answer = client.post("/api/ask", json=QUESTION)
        visitor = client.post("/api/ask", json=QUESTION, headers={"X-OpenAI-API-Key": VISITOR_KEY})
    assert health["mode"] == "local_preview"
    assert status["live_answers"] == "demo_only"
    assert status["visitor_keys"] is False
    assert answer.status_code == 200
    assert answer.json()["status"] == "passages_found"
    assert answer.json()["fallback_reason"] == "demo_only"
    assert visitor.status_code == 403
    factory.assert_not_called()


def test_demo_only_overrides_an_injected_paid_provider(retriever, sdk):
    with TestClient(live_app(retriever, sdk, DemoConfig(demo_only=True))) as client:
        assert client.post("/api/ask", json=QUESTION).json()["mode"] == "local_preview"
    sdk.responses.parse.assert_not_called()


def test_visitor_key_is_used_once_and_never_logged_or_returned(
    caplog, openai_factory, retriever, sdk
):
    caplog.set_level(logging.DEBUG)
    demo = DemoConfig(allow_visitor_keys=True, visitor_daily_limit=0)
    with TestClient(live_app(retriever, sdk, demo)) as client:
        response = client.post(
            "/api/ask", json=QUESTION, headers={"X-OpenAI-API-Key": f"  {VISITOR_KEY} "}
        )
        status = client.get("/api/demo").json()
    # The visitor's own key bypasses the exhausted demo quota.
    assert response.status_code == 200
    assert response.json()["status"] == "answered"
    assert status["visitor_keys"] is True
    sdk.responses.parse.assert_not_called()
    (client_mock,) = openai_factory
    assert client_mock.kwargs["api_key"] == VISITOR_KEY
    assert client_mock.kwargs["max_retries"] == 0
    client_mock.close.assert_called_once()
    assert VISITOR_KEY not in response.text
    assert VISITOR_KEY not in str(dict(response.headers))
    assert VISITOR_KEY not in caplog.text
    assert SERVER_KEY not in caplog.text + response.text


def test_visitor_key_works_without_a_server_key(openai_factory, retriever):
    demo = DemoConfig(allow_visitor_keys=True)
    with TestClient(create_app(retriever, Settings(), demo=demo)) as client:
        assert client.get("/api/health").json()["mode"] == "local_preview"
        response = client.post("/api/ask", json=QUESTION, headers={"X-OpenAI-API-Key": VISITOR_KEY})
    assert response.json()["mode"] == "openai"
    assert openai_factory[0].kwargs["api_key"] == VISITOR_KEY


def test_rejected_visitor_key_reports_without_echo(caplog, monkeypatch, retriever):
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    client_mock = Mock()
    client_mock.responses.parse.side_effect = AuthenticationError(
        f"Incorrect API key provided: {VISITOR_KEY}",
        response=httpx.Response(401, request=request),
        body=None,
    )
    monkeypatch.setattr("researchlens.answers.OpenAI", Mock(return_value=client_mock))
    demo = DemoConfig(allow_visitor_keys=True)
    with TestClient(create_app(retriever, Settings(), demo=demo)) as client:
        response = client.post("/api/ask", json=QUESTION, headers={"X-OpenAI-API-Key": VISITOR_KEY})
    assert response.status_code == 503
    assert response.json() == {"detail": "OpenAI rejected the API key you supplied."}
    assert VISITOR_KEY not in response.text + caplog.text
    client_mock.close.assert_called_once()


@pytest.mark.parametrize(
    "value", ["not-a-key", "sk-short", "sk-" + "a" * 20 + " b", "sk-" + "a" * 400]
)
def test_malformed_visitor_key_is_rejected_without_echo(openai_factory, retriever, value):
    demo = DemoConfig(allow_visitor_keys=True)
    with TestClient(create_app(retriever, Settings(), demo=demo)) as client:
        response = client.post("/api/ask", json=QUESTION, headers={"X-OpenAI-API-Key": value})
    assert response.status_code == 400
    assert value not in response.text
    assert openai_factory == []
    retriever.search.assert_not_called()


def test_visitor_keys_are_refused_when_disabled(openai_factory, retriever):
    with TestClient(create_app(retriever, Settings())) as client:
        response = client.post("/api/ask", json=QUESTION, headers={"X-OpenAI-API-Key": VISITOR_KEY})
    assert response.status_code == 403
    assert VISITOR_KEY not in response.text
    assert openai_factory == []


def test_visitor_key_does_not_bypass_input_limits(openai_factory, retriever):
    demo = DemoConfig(allow_visitor_keys=True)
    with TestClient(create_app(retriever, Settings(), demo=demo)) as client:
        too_long = client.post(
            "/api/ask", json={"question": "x" * 2001}, headers={"X-OpenAI-API-Key": VISITOR_KEY}
        )
        extra = client.post(
            "/api/ask",
            json={**QUESTION, "api_key": VISITOR_KEY},
            headers={"X-OpenAI-API-Key": VISITOR_KEY},
        )
    assert too_long.status_code == extra.status_code == 422
    assert VISITOR_KEY not in too_long.text
    assert openai_factory == []


def test_turnstile_failure_falls_back_without_spending_quota(retriever, sdk):
    store = Mock(wraps=MemoryQuotaStore())
    verify = Mock(side_effect=lambda token, address: token == "good")
    demo = DemoConfig(turnstile_site_key="site", turnstile_secret_key="secret")
    with TestClient(live_app(retriever, sdk, demo, store, verify)) as client:
        assert client.get("/api/demo").json()["turnstile_site_key"] == "site"
        missing = client.post("/api/ask", json=QUESTION)
        bad = client.post("/api/ask", json={**QUESTION, "turnstile_token": "bad"})
        store.consume.assert_not_called()
        good = client.post(
            "/api/ask",
            json={**QUESTION, "turnstile_token": "good"},
            headers={"X-Forwarded-For": "203.0.113.9"},
        )
    assert missing.status_code == bad.status_code == 403
    assert missing.json()["fallback_reason"] == "verification"
    assert good.status_code == 200 and good.json()["status"] == "answered"
    verify.assert_called_with("good", "203.0.113.9")
    assert sdk.responses.parse.call_count == 1


def test_local_mode_preview_is_unchanged_and_reports_no_live_answers(retriever):
    with TestClient(create_app(retriever, Settings())) as client:
        status = client.get("/api/demo").json()
        response = client.post("/api/ask", json=QUESTION)
    assert status["live_answers"] == "not_configured"
    assert status["visitor_remaining"] is None and status["turnstile_site_key"] is None
    assert response.status_code == 200
    assert response.json()["status"] == "passages_found"
    assert response.json()["notice"] is None


def test_recorded_examples_replay_without_retrieval_or_api_calls(retriever, sdk):
    with TestClient(live_app(retriever, sdk)) as client:
        examples = client.get("/api/demo").json()["examples"]
        replays = [client.get(f"/api/examples/{example['id']}").json() for example in examples]
        missing = client.get("/api/examples/unknown")
        remaining = client.get("/api/demo").json()["visitor_remaining"]
    assert 3 <= len(examples) <= 5
    assert missing.status_code == 404
    retriever.search.assert_not_called()
    sdk.responses.parse.assert_not_called()
    assert remaining == 5
    statuses = {replay["status"] for replay in replays}
    assert statuses == {"answered", "insufficient_evidence"}
    for example, replay in zip(examples, replays, strict=True):
        assert example["label"].startswith("Recorded answer from evaluation run 2026-10-13, ")
        assert "model gpt-6-luna, tier full (Qwen3-4B, " in example["label"]
        assert replay["replay"]["label"] == example["label"]
        assert replay["model"] == "gpt-6-luna"
        assert replay["latency_ms"] is None
        cited = {cid for section in replay["sections"] for cid in section["citation_ids"]}
        assert cited == {passage["id"] for passage in replay["passages"]}
        assert all(passage["attribution"] for passage in replay["passages"])


def test_recorded_answers_match_the_committed_evaluation_packet():
    assert demo_recordings.main(["--check"]) == 0
    recordings = load_recordings(RECORDINGS)
    assert {r.recorded.configuration for r in recordings.values()} <= {"qwen12k", "qwen16k"}


def test_missing_recordings_disable_examples(tmp_path, retriever):
    demo = DemoConfig(recordings=tmp_path / "missing.json")
    with TestClient(create_app(retriever, Settings(), demo=demo)) as client:
        assert client.get("/api/demo").json()["examples"] == []


def test_demo_config_from_env(tmp_path, monkeypatch):
    names = (
        "DEMO_ONLY",
        "LIVE_ANSWERS_PER_VISITOR_PER_DAY",
        "LIVE_ANSWERS_PER_DAY",
        "LIVE_QUOTA_DB",
        "ALLOW_VISITOR_API_KEYS",
        "TURNSTILE_SITE_KEY",
        "TURNSTILE_SECRET_KEY",
        "TRUSTED_PROXY_HOPS",
    )
    for name in names:
        monkeypatch.delenv(name, raising=False)
    env = tmp_path / ".env"
    env.write_text(
        "DEMO_ONLY=true\nLIVE_ANSWERS_PER_VISITOR_PER_DAY=3\nLIVE_ANSWERS_PER_DAY=20\n"
        f"LIVE_QUOTA_DB={tmp_path / 'q.sqlite3'}\nALLOW_VISITOR_API_KEYS=yes\n"
        "TURNSTILE_SITE_KEY=site\nTURNSTILE_SECRET_KEY=turnstile-secret\nTRUSTED_PROXY_HOPS=2\n"
    )
    config = DemoConfig.from_env(env)
    assert config.demo_only and config.allow_visitor_keys and config.turnstile_enabled
    assert (config.visitor_daily_limit, config.global_daily_limit, config.proxy_hops) == (3, 20, 2)
    assert config.quota_db == tmp_path / "q.sqlite3"
    assert "turnstile-secret" not in repr(config)
    assert DemoConfig.from_env(tmp_path / "absent.env").quota_db.name == "live-quota.sqlite3"
    monkeypatch.setenv("DEMO_ONLY", "maybe")
    with pytest.raises(ValueError, match="DEMO_ONLY"):
        DemoConfig.from_env(env)
    monkeypatch.setenv("DEMO_ONLY", "false")
    monkeypatch.setenv("LIVE_ANSWERS_PER_DAY", "-1")
    with pytest.raises(ValueError, match="LIVE_ANSWERS_PER_DAY"):
        DemoConfig.from_env(env)
    monkeypatch.setenv("LIVE_ANSWERS_PER_DAY", "5")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "")
    with pytest.raises(ValueError, match="TURNSTILE"):
        DemoConfig.from_env(env)


def test_read_visitor_key():
    assert read_visitor_key(None) is None
    assert read_visitor_key("   ") is None
    assert read_visitor_key(f" {VISITOR_KEY} ") == VISITOR_KEY
    with pytest.raises(ValueError) as error:
        read_visitor_key("sk-bad key value here!!")
    assert "bad key" not in str(error.value)
