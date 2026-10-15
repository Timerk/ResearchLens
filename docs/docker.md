# Docker Compose

Docker Compose starts the FastAPI backend and the Angular frontend with one command.
The default setup uses the minimal tier, which is TF-IDF retrieval with a
16,000-character context. It downloads no models and needs about 0.25 GiB of free RAM.

## Start

```sh
git clone https://github.com/Timerk/ResearchLens.git
cd ResearchLens
docker compose up --build
```

Open <http://127.0.0.1:4200>. The API documentation is at <http://127.0.0.1:8000/docs>.
Stop the stack with Ctrl+C, or with `docker compose down` if you started it with `-d`.

The backend image builds the default index and the minimal tier index during the
build, so startup takes a few seconds. The frontend container waits until the backend
health check passes. nginx serves the production Angular build and forwards `/api` to
the backend.

## What works without an API key

Without `OPENAI_API_KEY`, the app runs in local preview mode. You can ask questions,
read the ranked passages selected by the same context budget as OpenAI mode, and
inspect each source's section, XML location, authors, DOI and license. The minimal
tier retrieves 40 candidates and keeps the ranked prefix that fits its 16,000-character
serialized context budget, with each passage capped at 3,000 characters for selection.
The preview returns the selected passages' full text and context diagnostics.
Local preview does not generate answers or make API calls.

To get generated answers with citations, create `.env` next to `docker-compose.yml`:

```dotenv
ANSWER_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-6-luna
```

Then run `docker compose up -d` again. Each question is a paid OpenAI request. Compose
reads `.env` only to fill in `ANSWER_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_MODEL` and
`RETRIEVAL_TIER`. It does not pass the retrieval settings from `.env.example`, so they
cannot turn off tier selection. The `.dockerignore` file keeps `.env` out of the images.

## Switch retrieval tiers

The dense tiers need PyTorch, the model weights and a tier index built with the same
model. `docker-compose.models.yml` installs the `embedding-models` extra and stores the
Hugging Face cache and the tier indexes in named volumes, so they survive rebuilds.

```sh
# Build the image with PyTorch and Transformers (CPU wheels).
docker compose -f docker-compose.yml -f docker-compose.models.yml build backend

# Download a model and encode the corpus once per tier you want to use.
docker compose -f docker-compose.yml -f docker-compose.models.yml run --rm backend \
  python -m researchlens.ingest --tier standard

# Start with automatic selection, or name a tier.
docker compose -f docker-compose.yml -f docker-compose.models.yml up
RETRIEVAL_TIER=full docker compose -f docker-compose.yml -f docker-compose.models.yml up
```

| Tier | Model | Download | Required available RAM |
| --- | --- | ---: | ---: |
| full | Qwen3-4B | about 8 GB | 10 GiB |
| standard | BGE-M3 | about 2.3 GB | 5 GiB |
| light | Qwen3-0.6B | about 1.2 GB | 2.5 GiB |
| minimal | TF-IDF | none | 0.25 GiB |

`RETRIEVAL_TIER=auto` tries full, standard, light and minimal in that order. It skips a
tier when RAM is short or its index is missing. The container sees the memory of the
Docker VM, not the whole host. On Docker Desktop, raise the memory limit in the
settings before you use the full tier. `/api/health` reports the tier that loaded.
See [hardware tiers](embeddings.md#hardware-retrieval-tiers) for the measured peaks.

To use the original no-tier default of TF-IDF with four passages, set
`RETRIEVAL_TIER=` to an empty value in `.env`.

## Fresh-clone check

Run on 2026-10-15 on Windows 11 with Docker Desktop (Engine 29.2.1, Compose 5.1.0).
The base images were already present locally. On a machine without them, add the
time to pull `python:3.13-slim`, `node:24-slim` and `nginx:1.29-alpine`.

1. Cloned branch `docs/portfolio-polish` at `cc25579` from GitHub into an empty
   temporary directory, with no `.env` file.
2. Ran `docker compose build --no-cache --pull`. It finished in 31 seconds, with every
   build step executed: `uv sync` installed 30 packages, `npm ci` added 475 packages,
   the Angular production build ran, and ingestion built both TF-IDF indexes.
3. Ran `docker compose up -d --wait`. Both containers reported healthy after 8 seconds.
4. `GET /api/health` returned
   `{"status":"ok","mode":"local_preview","retrieval_tier":"minimal"}`, both directly
   on port 8000 and through nginx on port 4200. The frontend returned HTTP 200.
5. `POST /api/ask` through port 4200 with *Why combine forward and backward lighting
   for aircraft glass canopy inspection?* returned `passages_found` with 40 ranked
   passages. The first was `pmc11510794:p58:w0` from section `5. Conclusions`.
6. Ran `docker compose down`.

That check predates local preview context filtering. An offline API recheck with the
same question and a rebuilt minimal index now returns 26 of the 40 candidates, matching
OpenAI context selection. The response fell from about 74.6 KB to 49.3 KB, including
context diagnostics. The selected serialized context uses 14,655 of 16,000 characters;
the next ranked passage would exceed the budget.

The dense-tier override was checked separately with the light tier. Building the
`embedding-models` image took 1 minute 39 seconds, and `ingest --tier light`
downloaded Qwen3-0.6B and encoded the corpus in 1 minute 54 seconds. With
`RETRIEVAL_TIER=auto`, the backend skipped the missing full and standard indexes,
reported `"retrieval_tier":"light"`, and answered a query. The full and standard tiers
were not built in Docker.

## Screenshots

The images in [`docs/images`](images/) were captured on 2026-10-15 with Playwright and
Chromium against this Docker stack.

- [`desktop-local-preview.png`](images/desktop-local-preview.png) shows the real backend
  in local preview mode, using the minimal tier and no API key. It predates context
  filtering and was captured from the old 40-passage response. The image shows only
  the first two passages, which remain selected; it does not show the total count.
- [`desktop-answer.png`](images/desktop-answer.png),
  [`desktop-answer-full.png`](images/desktop-answer-full.png) and
  [`mobile-answer.png`](images/mobile-answer.png) show a generated answer. No API key
  was used. The browser intercepted `/api/ask` and returned a saved response from the
  2026-10-15 development evaluation: question `tech-glass-paraphrase`, Qwen3-4B with
  16,000 characters, generated by `gpt-6-luna`. The frozen judge found all of its
  required claims present. The displayed server time is the recorded retrieval plus
  generation latency. The header reports OpenAI mode because the browser intercepted
  the health check as well.
