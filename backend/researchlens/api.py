from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, HTTPException

from researchlens.answers import AnswerProvider, LocalPreview
from researchlens.ingest import INDEX
from researchlens.models import Answer, Question
from researchlens.retrieval import Retriever


def create_app(retriever: Retriever | None = None) -> FastAPI:
    provider: AnswerProvider = LocalPreview()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.retriever = retriever
        if app.state.retriever is None:
            try:
                app.state.retriever = Retriever.from_path(INDEX)
            except (OSError, ValueError, KeyError) as exc:
                raise RuntimeError(
                    "Index missing or invalid. Run: "
                    "uv run --directory backend python -m researchlens.ingest"
                ) from exc
        yield

    app = FastAPI(title="ResearchLens", version="0.1.0", lifespan=lifespan)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "local_preview"}

    @app.post("/api/ask", response_model=Answer)
    def ask(request: Question) -> Answer:
        started = perf_counter()
        active_retriever: Retriever | None = app.state.retriever
        if active_retriever is None:
            raise HTTPException(status_code=503, detail="Document index is unavailable")
        passages = active_retriever.search(request.question)
        answer = provider.answer(request.question, passages)
        answer.latency_ms = round((perf_counter() - started) * 1000, 2)
        return answer

    return app


app = create_app()
