# Development guide

This page holds the setup and reference material that used to live in the main README.
For the quickest start, use [Docker Compose](docker.md) instead.

## Run without Docker

Install Python 3.13, [uv](https://docs.astral.sh/uv/) and Node 24 with npm. From the
repository root:

```sh
uv sync --locked --python 3.13
uv run --directory backend python -m researchlens.ingest
uv run --directory backend uvicorn researchlens.api:app --host 127.0.0.1 --port 8000
```

In another terminal, from `frontend`:

```sh
npm ci
npm start
```

Open <http://127.0.0.1:4200>. The API documentation is at <http://127.0.0.1:8000/docs>.
On Windows, `py -m uv` can replace `uv` if uv is installed as a Python module but not
on PATH.

The backend reads `.env` from the repository root, and process environment variables
take precedence. Local preview mode needs no API key. Without a retrieval tier, the
backend uses TF-IDF and sends four passages to the answer provider.

Local preview lists the same passages that OpenAI mode would receive. With a tier,
retrieval fetches 40 candidates and context selection keeps a ranked prefix that fits
the tier's serialized character budget. Selection caps each passage at 3,000 characters;
both modes return the selected passages' full text for inspection. The response's
`context_diagnostics` records the selected IDs, visible characters and truncations.
Local preview makes no API call and reports zero estimated API cost.

## Retrieval options

### Local embeddings

```sh
uv sync --locked --extra embeddings --python 3.13
uv run --extra embeddings --directory backend python -m researchlens.ingest --retrieval embeddings
```

Set `RETRIEVAL_BACKEND=embeddings` in `.env`, then start the backend with the same extra:

```sh
uv run --extra embeddings --directory backend uvicorn researchlens.api:app --host 127.0.0.1 --port 8000
```

The first ingestion downloads the pinned Apache-2.0 `all-MiniLM-L6-v2` model, about
91 MB. Encoding runs on the CPU, and startup reads only cached model files. MiniLM
needs no embedding API, PyTorch or vector database. Set `RETRIEVAL_BACKEND=tfidf` to
return to the baseline.

The `embedding-models` extra adds `bge-m3`, `qwen3-0.6b` and `qwen3-4b`. Set
`EMBEDDING_MODEL` to the alias used at ingestion. `RETRIEVAL_BACKEND=hybrid` combines
lexical and embedding ranks. [Embedding setup](embeddings.md) covers reranking, fusion
weights, custom corpus paths and stale-index recovery.

### Hardware tiers

Set `RETRIEVAL_TIER=auto` and remove any `RETRIEVAL_BACKEND` or `EMBEDDING_MODEL`
values. Either of those settings takes precedence and turns tier selection off.
Auto mode picks full, standard, light or minimal from the available physical RAM and
the tier artifacts you have built:

```sh
uv sync --locked --extra embedding-models --python 3.13
uv run --no-sync --directory backend python -m researchlens.ingest --tier full
uv run --no-sync --directory backend python -m researchlens.ingest --tier minimal
```

| Tier | Retrieval | Context characters | Required available RAM |
| --- | --- | ---: | ---: |
| full | Qwen3-4B dense | 12,000 | 10 GiB |
| standard | BGE-M3 dense | 16,000 | 5 GiB |
| light | Qwen3-0.6B dense | 16,000 | 2.5 GiB |
| minimal | TF-IDF | 16,000 | 0.25 GiB |

The [tier section](embeddings.md#hardware-retrieval-tiers) explains the RAM estimates,
the fallback order and the downloads, which reach about 8 GB for Qwen3-4B.

## Document-only OpenAI answers

Copy `.env.example` to `.env` and set:

```dotenv
ANSWER_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-6-luna
```

Restart the backend after you change settings. Git ignores `.env`. The key stays on
the backend and never appears in frontend responses. OpenAI mode fails at startup if
the key or model is empty. The first request checks model access and key validity.
The header shows the active mode from `/api/health`.

Requests use the Responses API with medium reasoning, no automatic retries, a
45-second timeout and at most 2,000 output tokens including reasoning. Questions are
limited to 2,000 characters. Each passage is capped at 3,000 characters. The backend
sends the question and the selected passage text with `store=false`. It sends no
conversation history, tools or full corpus. Account-level data retention rules still
apply.

The backend rejects unknown citation IDs, uncited sections, malformed output and
incomplete responses. If retrieval finds no passages, the backend makes no API
request. A failed API request returns an error. The app does not fall back to preview
mode. Response metadata includes the model, latency and token usage.
`estimated_api_cost_usd` is `null` for paid requests because the code does not
hardcode billing rates, and zero when no API call was made.

Example questions: `Why combine forward and backward lighting for aircraft glass
canopy inspection?` and `What training data are used in each stage of the autoencoder
method?`. Each result lists author, date, license, section and the original XML
location. XML citations use section and paragraph locations, not PDF page numbers.

## Technical corpus

The four papers cover dual-modal glass inspection, transfer learning on painted
surfaces, TDI dark-field wafer inspection and two-stage autoencoder training. Their
authors license the texts under CC BY 4.0. The original XML, checksums, publication
metadata, permission evidence and extraction notes are in
[`data/technical/manifest.json`](../data/technical/manifest.json). Keep
[`data/technical/NOTICE.txt`](../data/technical/NOTICE.txt) when you redistribute the
corpus. The repository includes no external image datasets.

Normal startup uses the checked-in extracted text and downloads nothing. To reproduce
the extraction offline, which also verifies the original checksums, or to refresh the
source files:

```sh
uv run --directory backend python -m researchlens.corpus
# Optional network refresh. Review the resulting content, license and checksum changes.
uv run --directory backend python -m researchlens.corpus --download
uv run --directory backend python -m researchlens.ingest --corpus technical
```

Extraction keeps abstract and body prose, section paths and XML paragraph locations,
and normalizes whitespace. It drops figures, captions, tables, references and back
matter. The approved `mathml-readable-v2` renderer restores 122 formulas as readable
symbols, scripts and grouped fractions. Four unsupported formulas remain
`[formula omitted]`. This is a partial extraction, so consult the originals for
omitted evidence and numerical tables.

Changes to extraction or source content can change passage IDs. Rebuild the index and
review evaluation references after such a change. Git treats the raw XML files as
binary, so checksums match across Windows and Linux checkouts.

### Synthetic fixture corpus

To run the original three synthetic documents, rebuild with `--corpus sample`, set
`RETRIEVAL_CORPUS=data/sample_documents.json` and restart the backend. The two corpora
are never mixed. `CORPUS` and the Python `build_index()` default still point at the
sample corpus for test compatibility, while the ingestion CLI defaults to technical.

In sample TF-IDF mode, `Who composed Beethoven symphonies?` shows the no-match state.
Embedding retrieval always returns nearest neighbors, even for unrelated questions, so
OpenAI mode can make a paid request and relies on the model to abstain.

## Verify

```sh
uv run pytest -q
uv run ruff check backend
uv run ruff format --check backend
```

From `frontend`:

```sh
npm ci
npm run check
npm test
npm run build
npm run test:smoke:install
npm run test:smoke
```

Frontend tests mock the API and need no backend, API key or paid call. GitHub Actions
runs the backend checks, frontend checks, component tests, production build and
Chromium smoke tests. CI does not download models or run real-model benchmarks. See
the [frontend instructions](../frontend/README.md) and the
[verification record](../frontend/docs/verification.md).

## Code layout and boundaries

- `backend/researchlens/ingest.py` validates documents, keeps metadata, and writes a
  corpus hash with deterministic passage IDs. Rebuild after corpus edits.
- `retrieval.py` gives TF-IDF and local embeddings one search interface. Startup checks
  the corpus hash and artifact compatibility, then builds the lexical matrix or loads
  saved vectors and one cached CPU encoder.
- `retrieval_tiers.py` picks a tier from available RAM and falls back when a tier
  cannot load.
- `answers.py` contains the local preview, the OpenAI provider, the context budget,
  the document-only instructions and citation validation.
- `config.py` reads backend-only configuration without changing the process environment.
- `api.py` handles HTTP validation and request timing. A missing or corrupt index stops
  startup with an actionable message.
- `evaluation.py` and the `answer_*` modules run the retrieval and answer-quality
  studies. See the [evaluation workflow](../evaluation/README.md).
- The Angular app shows plain text and expandable reference metadata. Its development
  proxy sends `/api` to FastAPI, so there is no CORS configuration.

The passage artifact stores normalized text, paragraph numbers, word offsets,
attribution and source locations. Its IDs stay stable for unchanged input, not across
arbitrary source revisions. There is no PDF extractor yet.

For a corpus of this size, disk files and an in-memory index are enough. LangChain, a
vector database, graph infrastructure, authentication and agent orchestration stay out
until a concrete requirement needs them.

## Roadmap

1. Expand the four-paper starter set to 15-30 authorized documents with recorded source
   URL, author, date, license and permission evidence. Add PDF and text extraction with
   page references.
2. Record a live demonstration of the document-only answer mode.
3. Demonstrate an Azure deployment, compare a defined graph approach against the same
   baseline, and expose search and source retrieval through a Python MCP server.

## Learning checkpoint

Read `Retriever.search` and the chunking test. With `--corpus sample`, compare
`Does dust cause false positives?` with `Can contamination trigger erroneous alarms?`.
Explain why lexical matching treats these equivalent questions differently. Then
explain why a passage that matches `illumination` cannot establish a numerical
defect-size limit. The first is a retrieval recall problem and the second is an
evidence sufficiency problem. The archived
[local implementation checks](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/retrieval-checks.md)
record the observed rankings.
