from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, HTTPException

from researchlens.answers import AnswerProvider, LocalPreview, OpenAIProvider, ProviderError
from researchlens.config import Settings
from researchlens.models import Answer, Question
from researchlens.retrieval import PassageRetriever, load_retriever


def create_app(
    retriever: PassageRetriever | None = None,
    settings: Settings | None = None,
    provider: AnswerProvider | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        active_settings = settings if settings is not None else Settings.from_env()
        app.state.retriever = retriever
        if app.state.retriever is None:
            try:
                app.state.retriever = load_retriever(
                    active_settings.retrieval,
                    active_settings.index_path,
                    source=active_settings.corpus_path,
                    expected_model=active_settings.embedding_model,
                )
            except ValueError as exc:
                raise RuntimeError(str(exc)) from exc
        app.state.mode = "openai" if active_settings.provider == "openai" else "local_preview"
        app.state.provider = (
            provider
            if provider is not None
            else (
                OpenAIProvider(active_settings)
                if active_settings.provider == "openai"
                else LocalPreview()
            )
        )
        try:
            yield
        finally:
            if provider is None and isinstance(app.state.provider, OpenAIProvider):
                app.state.provider.close()

    app = FastAPI(title="ResearchLens", version="0.1.0", lifespan=lifespan)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": app.state.mode}

    @app.post("/api/ask", response_model=Answer)
    def ask(request: Question) -> Answer:
        started = perf_counter()
        active_retriever: PassageRetriever | None = app.state.retriever
        if active_retriever is None:
            raise HTTPException(status_code=503, detail="Document index is unavailable")
        passages = active_retriever.search(request.question)
        try:
            answer = app.state.provider.answer(request.question, passages)
        except ProviderError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None
        answer.latency_ms = round((perf_counter() - started) * 1000, 2)
        return answer

    return app


app = create_app()
