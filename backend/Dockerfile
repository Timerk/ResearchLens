# ResearchLens API. Build from the repository root: docker build -f backend/Dockerfile .
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.23 /uv /usr/local/bin/uv

# Empty installs the TF-IDF runtime only. Pass "--extra embedding-models" for dense tiers.
ARG UV_EXTRAS=""
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml uv.lock LICENSE ./
RUN uv sync --locked --no-dev --no-install-project $UV_EXTRAS

COPY backend/researchlens backend/researchlens
COPY data data

# The default index and the minimal tier are TF-IDF artifacts and need no model download.
RUN python -m researchlens.ingest && python -m researchlens.ingest --tier minimal

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=6 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uvicorn", "researchlens.api:app", "--host", "0.0.0.0", "--port", "8000"]
