from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, HTTPException

from researchlens.answers import AnswerProvider, LocalPreview, OpenAIProvider, ProviderError
from researchlens.config import Settings
from researchlens.models import Answer, Question
from researchlens.retrieval import PassageRetriever
from researchlens.retrieval_tiers import load_configured_retriever


def create_app(
    retriever: PassageRetriever | None = None,
    settings: Settings | None = None,
    provider: AnswerProvider | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        active_settings = settings if settings is not None else Settings.from_env()
        app.state.retriever = retriever
        app.state.retrieval_tier = None
        if app.state.retriever is None:
            try:
                app.state.retriever, active_settings, app.state.retrieval_tier = (
                    load_configured_retriever(active_settings)
                )
            except (ValueError, MemoryError, RuntimeError) as exc:
                raise RuntimeError(str(exc)) from exc
        app.state.mode = "openai" if active_settings.provider == "openai" else "local_preview"
        app.state.retrieval_limit = (
            active_settings.answer_context_candidates
            if active_settings.answer_context_mode == "characters"
            else 4
        )
        app.state.provider = (
            provider
            if provider is not None
            else (
                OpenAIProvider(active_settings)
                if active_settings.provider == "openai"
                else LocalPreview(active_settings)
            )
        )
        try:
            yield
        finally:
            if provider is None and isinstance(app.state.provider, OpenAIProvider):
                app.state.provider.close()

    app = FastAPI(title="ResearchLens", version="0.1.0", lifespan=lifespan)

    @app.get("/api/health")
    def health() -> dict[str, str | None]:
        return {
            "status": "ok",
            "mode": app.state.mode,
            "retrieval_tier": app.state.retrieval_tier,
        }

    @app.post("/api/ask", response_model=Answer)
    def ask(request: Question) -> Answer:
        started = perf_counter()
        active_retriever: PassageRetriever | None = app.state.retriever
        if active_retriever is None:
            raise HTTPException(status_code=503, detail="Document index is unavailable")
        passages = active_retriever.search(request.question, limit=app.state.retrieval_limit)
        try:
            answer = app.state.provider.answer(request.question, passages)
        except ProviderError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None
        answer.latency_ms = round((perf_counter() - started) * 1000, 2)
        return answer

    return app


app = create_app()
