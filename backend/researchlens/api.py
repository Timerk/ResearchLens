from contextlib import asynccontextmanager
from dataclasses import replace
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from researchlens.answers import AnswerProvider, LocalPreview, OpenAIProvider, ProviderError
from researchlens.config import Settings
from researchlens.demo import (
    NOTICES,
    VISITOR_KEY_HEADER,
    AskRequest,
    DemoAnswer,
    DemoConfig,
    DemoStatus,
    ExampleSummary,
    FallbackReason,
    ReplayResponse,
    TurnstileVerifier,
    load_recordings,
    read_visitor_key,
    replay,
    turnstile_verifier,
)
from researchlens.models import Answer, SearchHit
from researchlens.rate_limit import (
    LiveAnswerQuota,
    MemoryQuotaStore,
    QuotaStore,
    SQLiteQuotaStore,
    client_address,
    seconds_until_utc_midnight,
)
from researchlens.retrieval import PassageRetriever
from researchlens.retrieval_tiers import load_configured_retriever

FALLBACK_STATUS = {
    "visitor_limit": 429,
    "daily_limit": 429,
    "provider_limit": 429,
    "verification": 403,
}


def create_app(
    retriever: PassageRetriever | None = None,
    settings: Settings | None = None,
    provider: AnswerProvider | None = None,
    demo: DemoConfig | None = None,
    quota_store: QuotaStore | None = None,
    verify_turnstile: TurnstileVerifier | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        active_settings = settings if settings is not None else Settings.from_env()
        # Explicit settings (tests, embedding) default to an in-memory quota and no .env.
        active_demo = demo or (DemoConfig() if settings is not None else DemoConfig.from_env())
        app.state.retriever = retriever
        app.state.retrieval_tier = None
        if app.state.retriever is None:
            try:
                app.state.retriever, active_settings, app.state.retrieval_tier = (
                    load_configured_retriever(active_settings)
                )
            except (ValueError, MemoryError, RuntimeError) as exc:
                raise RuntimeError(str(exc)) from exc
        app.state.settings = active_settings
        app.state.demo = active_demo
        # The kill switch never constructs a paid client.
        app.state.live = active_settings.provider == "openai" and not active_demo.demo_only
        app.state.mode = "openai" if app.state.live else "local_preview"
        app.state.retrieval_limit = (
            active_settings.answer_context_candidates
            if active_settings.answer_context_mode == "characters"
            else 4
        )
        app.state.preview = LocalPreview(active_settings)
        if active_demo.demo_only:
            app.state.provider = app.state.preview
        elif provider is not None:
            app.state.provider = provider
        elif app.state.live:
            app.state.provider = OpenAIProvider(active_settings)
        else:
            app.state.provider = app.state.preview
        app.state.quota = None
        if app.state.live:
            store = quota_store or (
                SQLiteQuotaStore(active_demo.quota_db)
                if active_demo.quota_db is not None
                else MemoryQuotaStore()
            )
            app.state.quota = LiveAnswerQuota(
                store, active_demo.visitor_daily_limit, active_demo.global_daily_limit
            )
        app.state.verify_turnstile = verify_turnstile or (
            turnstile_verifier(active_demo.turnstile_secret_key)
            if active_demo.turnstile_enabled
            else None
        )
        app.state.recordings = load_recordings(active_demo.recordings)
        try:
            yield
        finally:
            if provider is None and isinstance(app.state.provider, OpenAIProvider):
                app.state.provider.close()

    app = FastAPI(title="ResearchLens", version="0.1.0", lifespan=lifespan)

    def visitor_keys_enabled() -> bool:
        return app.state.demo.allow_visitor_keys and not app.state.demo.demo_only

    def address(request: Request) -> str:
        return client_address(
            request.headers.get("x-forwarded-for"),
            request.client.host if request.client else None,
            app.state.demo.proxy_hops,
        )

    @app.get("/api/health")
    def health() -> dict[str, str | None]:
        return {
            "status": "ok",
            "mode": app.state.mode,
            "retrieval_tier": app.state.retrieval_tier,
        }

    @app.get("/api/demo", response_model=DemoStatus)
    def demo_status(request: Request) -> DemoStatus:
        config: DemoConfig = app.state.demo
        quota: LiveAnswerQuota | None = app.state.quota
        visitor_remaining, remaining_today = (
            quota.remaining(address(request)) if quota is not None else (None, None)
        )
        return DemoStatus(
            live_answers="enabled"
            if app.state.live
            else "demo_only"
            if config.demo_only
            else "not_configured",
            visitor_daily_limit=config.visitor_daily_limit,
            global_daily_limit=config.global_daily_limit,
            visitor_remaining=visitor_remaining,
            remaining_today=remaining_today,
            visitor_keys=visitor_keys_enabled(),
            turnstile_site_key=config.turnstile_site_key
            if app.state.live and config.turnstile_enabled
            else None,
            examples=[
                ExampleSummary(id=r.id, title=r.title, question=r.question, label=r.label)
                for r in app.state.recordings.values()
            ],
        )

    @app.get("/api/examples/{example_id}", response_model=ReplayResponse)
    def example(example_id: str) -> ReplayResponse:
        recording = app.state.recordings.get(example_id)
        if recording is None:
            raise HTTPException(status_code=404, detail="Unknown example")
        return replay(recording)

    def finish(answer: Answer, started: float, **extra) -> DemoAnswer:
        result = DemoAnswer(**answer.model_dump(), **extra)
        result.latency_ms = round((perf_counter() - started) * 1000, 2)
        return result

    def fallback(
        reason: FallbackReason, question: str, passages: list[SearchHit], started: float
    ) -> JSONResponse:
        answer = finish(
            app.state.preview.answer(question, passages),
            started,
            notice=NOTICES[reason],
            fallback_reason=reason,
            live_answers_remaining=0 if reason == "visitor_limit" else None,
        )
        status = FALLBACK_STATUS[reason]
        return JSONResponse(
            {**answer.model_dump(mode="json"), "detail": NOTICES[reason]},
            status_code=status,
            headers={"Retry-After": str(seconds_until_utc_midnight())} if status == 429 else None,
        )

    def answer_with(selected: AnswerProvider, question: str, passages: list[SearchHit]):
        try:
            return selected.answer(question, passages)
        except ProviderError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None

    def answer_with_visitor_key(key: str, question: str, passages: list[SearchHit]) -> Answer:
        # A fresh client per request; the key is not stored, logged or returned.
        visitor = OpenAIProvider(replace(app.state.settings, provider="openai", api_key=key))
        try:
            return visitor.answer(question, passages)
        except ProviderError as exc:
            detail = (
                "OpenAI rejected the API key you supplied."
                if exc.status_code == 503 and str(exc).startswith("OpenAI authentication")
                else str(exc)
            )
            raise HTTPException(status_code=exc.status_code, detail=detail) from None
        finally:
            visitor.close()

    @app.post(
        "/api/ask",
        response_model=DemoAnswer,
        responses={
            403: {"model": DemoAnswer, "description": "Bot check failed; local preview"},
            429: {"model": DemoAnswer, "description": "Live-answer limit; local preview"},
        },
    )
    def ask(body: AskRequest, request: Request):
        started = perf_counter()
        try:
            visitor_key = read_visitor_key(request.headers.get(VISITOR_KEY_HEADER))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from None
        if visitor_key is not None and not visitor_keys_enabled():
            raise HTTPException(
                status_code=403, detail="This server does not accept visitor API keys."
            )
        active_retriever: PassageRetriever | None = app.state.retriever
        if active_retriever is None:
            raise HTTPException(status_code=503, detail="Document index is unavailable")
        question = body.question
        passages = active_retriever.search(question, limit=app.state.retrieval_limit)

        if visitor_key is not None:
            return finish(answer_with_visitor_key(visitor_key, question, passages), started)
        if not app.state.live:
            reason = "demo_only" if app.state.demo.demo_only else None
            return finish(
                answer_with(app.state.provider, question, passages),
                started,
                notice=NOTICES[reason] if reason else None,
                fallback_reason=reason,
            )
        if not passages:
            # The provider returns no_matches without an API call; do not spend quota.
            return finish(answer_with(app.state.provider, question, passages), started)
        client = address(request)
        verify: TurnstileVerifier | None = app.state.verify_turnstile
        if verify is not None and not (
            body.turnstile_token and verify(body.turnstile_token, client)
        ):
            return fallback("verification", question, passages, started)
        decision = app.state.quota.consume(client)
        if not decision.allowed:
            return fallback(decision.reason, question, passages, started)
        try:
            answer = app.state.provider.answer(question, passages)
        except ProviderError as exc:
            if exc.status_code == 429:
                # OpenAI rate or budget limit: degrade to the free preview.
                return fallback("provider_limit", question, passages, started)
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None
        return finish(answer, started, live_answers_remaining=decision.visitor_remaining)

    return app


app = create_app()
