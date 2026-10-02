# ResearchLens

An independent portfolio project for exploring a curated technical document collection.
The application answers research questions from retrieved document passages,
with inspectable citations and explicit insufficient-evidence responses.

Angular and FastAPI run end to end with four **CC BY 4.0 technical papers** by default.
The original three synthetic documents remain available as a separate regression corpus.
Retrieval offers TF-IDF word matching (the default baseline), local CPU embeddings and
hybrid rank fusion. Local mode shows retrieved passages; OpenAI mode generates document-only
answers with validated passage references. Do not treat the fixtures as technical findings
or valid citation IDs as proof that a claim is supported. The technical corpus has not yet
received human scientific review.

## Run locally

Install Python 3.13, uv, and Node 24 with npm. From the repository root:

```sh
rtk proxy uv sync --locked --python 3.13
rtk proxy uv run --directory backend python -m researchlens.ingest
rtk proxy uv run --directory backend uvicorn researchlens.api:app --host 127.0.0.1 --port 8000
```

In another terminal, from `frontend`:

```sh
rtk npm ci
rtk npm start
```

Open <http://127.0.0.1:4200>. API documentation is at <http://127.0.0.1:8000/docs>.
RTK is the workspace command wrapper; if it is not installed on another machine,
run the underlying commands without `rtk` or `rtk proxy`.
Local mode needs no API key. The backend reads `.env` from the repository root;
process environment variables take precedence. On Windows, `py -m uv` can replace
`uv` if it is installed as a Python module but not on PATH.

### Enable local embedding retrieval

```sh
rtk proxy uv sync --locked --extra embeddings --python 3.13
rtk proxy uv run --extra embeddings --directory backend python -m researchlens.ingest --retrieval embeddings
```

Set `RETRIEVAL_BACKEND=embeddings` in `.env`, then start the backend with the extra:

```sh
rtk proxy uv run --extra embeddings --directory backend uvicorn researchlens.api:app --host 127.0.0.1 --port 8000
```

The first ingestion downloads the pinned Apache-2.0 English `all-MiniLM-L6-v2` model
(about 91 MB); encoding runs locally on CPU. Startup uses only cached model files.
MiniLM needs no embedding API, key, PyTorch installation or vector database.
Set `RETRIEVAL_BACKEND=tfidf` to select the baseline again; it can use the same artifact.
Keep `ANSWER_PROVIDER=local` for a free passage preview in either retrieval mode.
See [embedding setup and integration](docs/embeddings.md) for model conventions,
custom corpus paths, stale-index recovery and the evaluation runner interface.

The CPU model catalog also supports `bge-m3`, `qwen3-0.6b` and `qwen3-4b` using the
optional `embedding-models` extra. Set `EMBEDDING_MODEL` to the matching alias and
`RETRIEVAL_BACKEND=hybrid` to fuse TF-IDF and embedding ranks. Each model needs its own
ingested artifact; startup rejects mismatched models or encoding/runtime settings.
Run the existing evaluation pipeline across all four models and both retrieval modes:

```sh
rtk proxy uv sync --locked --extra embeddings --extra embedding-models --python 3.13
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.compare_retrieval --evidence-labels ../evaluation/labels/technical-development.json --output ../evaluation/runs/cpu-comparison-k4
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.compare_retrieval --evidence-labels ../evaluation/labels/technical-development.json --limit 10 --cutoffs 1 4 10 --output ../evaluation/runs/cpu-comparison-ranking
```

This uses the 50 approved development questions and their separately approved evidence
groups without answer generation. The first command measures actual k=4 retrieval;
the second scores ranking prefixes at 1, 4 and 10. Each saves a paired per-question
report against TF-IDF. Both use fresh processes and may download pinned weights on
first ingestion. Held-out questions are not executed. See [evaluation readiness](docs/retrieval-readiness.md)
and the [historical preliminary comparison](docs/model-comparison.md).
The [approved development results](docs/approved-model-comparison.md) report all nine
configurations, complete evidence, paired regressions and CPU costs on the reviewed set.
See [retrieval development experiments](docs/retrieval-improvements.md) for optional
local reranking, weighted fusion, tokenizer measurements and offline context comparisons.
Optional RX 6800 Vulkan reranker experiments are documented in
[Vulkan reranker tests](docs/vulkan-reranking.md).
The [complementary selection experiment](docs/complementary-selection.md) tests
question splitting and title/section reranking. Its five variants regress against
the existing controls, so the previous selection and application defaults remain.

### Enable document-only OpenAI answers

Create `.env` using `.env.example` as a guide (preserve your existing key if present):

```dotenv
ANSWER_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-6-luna
```

Restart the backend after changing settings. `.env` is ignored by Git. The key stays
on the backend and is never included in frontend responses. OpenAI mode fails at
startup when the key or model is empty. Model access and key validity are checked by
the first API request. Set `ANSWER_PROVIDER=local` to return to the free preview.
The header shows the active mode from `/api/health`.

OpenAI requests use the Responses API with **medium reasoning**, no automatic retries,
a 45-second network timeout, and at most 2,000 output tokens including reasoning.
Questions are limited to 2,000 characters. Context is capped at four passages,
3,000 characters per passage and 16,000 serialized context characters in total.
The question and selected passage text are sent to OpenAI with `store=false`;
no conversation history, tools, or full-corpus upload is used. Account-level data
retention rules still apply.

Answers contain cited sections or an explicit abstention. Unknown citation IDs,
uncited sections, malformed output, and incomplete responses are rejected. No
matching passages means no API request. Failed API requests surface an error;
the app does not silently fall back to preview mode. Response metadata includes
model, latency and token usage; `estimated_api_cost_usd` is `null` for paid requests
because billing rates are not hardcoded, and zero when no API call was made.

Try `Why combine forward and backward lighting for aircraft glass canopy inspection?`
or `What training data are used in each stage of the autoencoder method?` and inspect
the source references. Results include author, date, license, section and original XML
location. XML citations use section/paragraph locations, not invented PDF page numbers.

### Technical corpus and attribution

The four papers cover dual-modal glass inspection, transfer learning on painted surfaces,
TDI dark-field wafer inspection, and two-stage autoencoder training. Their original XML,
checksums, publication metadata, permission evidence and extraction notes are in
[`data/technical/manifest.json`](data/technical/manifest.json). Preserve
[`data/technical/NOTICE.txt`](data/technical/NOTICE.txt) when redistributing this corpus.
The texts are licensed CC BY 4.0 by their authors; no external image datasets are included.

Normal startup uses the checked-in extracted text and requires no download. Reproduce
the extraction offline (verifies original checksums), or explicitly refresh source files:

```sh
rtk proxy uv run --directory backend python -m researchlens.corpus
# Optional network refresh; review the resulting content/license/checksum changes:
rtk proxy uv run --directory backend python -m researchlens.corpus --download
rtk proxy uv run --directory backend python -m researchlens.ingest --corpus technical
```

Extraction includes abstract and body prose, preserves section paths and XML paragraph
locations, and normalizes whitespace. Figures, captions, tables, references and back matter
are excluded; mathematical markup is replaced with `[formula omitted]`. This is a partial
extraction. Consult the originals for omitted evidence, equations and numerical tables.
Changing extraction or source content can change passage IDs; rebuild the index and review
evaluation references after such changes. Raw XML files are marked binary for Git line-ending
purposes so checksums remain valid across Windows and Linux checkouts.

To run the old fixture examples instead, rebuild with `--corpus sample`, set
`RETRIEVAL_CORPUS=data/sample_documents.json` and restart the backend. The two corpora
are not mixed. `CORPUS` and the Python `build_index()` default remain
the sample corpus for compatibility with existing tests; the ingestion CLI defaults to
technical. Questions such as `Does dust cause false positives?` retain their original test
meaning only against the fixture corpus. Rebuild and restart after switching corpora.
In sample TF-IDF mode, try `Who composed Beethoven symphonies?` for the no-match state. Embeddings return
nearest neighbors even for unrelated questions, so OpenAI mode may make a paid request
and must rely on the answer provider's abstention behavior. Similarity is not answerability.

## Verify

```sh
rtk proxy uv run pytest -q
rtk proxy uv run ruff check backend
rtk proxy uv run ruff format --check backend
```

From `frontend`:

```sh
rtk npm ci
rtk npm run check
rtk npm test
rtk npm run build
rtk npm run test:smoke:install
rtk npm run test:smoke
```

Frontend tests use mocked API responses and need no backend, API keys or paid calls.
GitHub Actions runs the backend checks above, frontend checks, component tests,
production build and Chromium smoke tests. See the [frontend instructions](frontend/README.md)
for watch mode and offline UI inspection, and the [verification record](frontend/docs/verification.md)
for actual browser coverage, screenshots and limitations.
Model downloads and real-model benchmarks are manual; CI uses offline retrieval tests.

## Architecture and boundaries

```text
JSON documents → paragraph/word chunking → passage artifact + optional local vectors
                                                   ↓
Angular → POST /api/ask → selected retriever → answer provider → passage references
```

- `backend/researchlens/ingest.py` validates text documents, preserves metadata,
  and writes a corpus hash and deterministic passage IDs. Rebuild after corpus edits.
- `retrieval.py` exposes a common search interface for TF-IDF and local embeddings.
  Startup checks the corpus hash and artifact compatibility, then builds the lexical
  matrix or loads saved vectors and one cached CPU encoder. Scores are not proof of answerability.
- `answers.py` implements the local preview and OpenAI provider, structured output,
  bounded context, document-only instructions and citation validation.
- `config.py` reads backend-only configuration without modifying the process environment.
- `api.py` owns HTTP validation and request timing. Missing or corrupt indexes
  stop startup with an actionable message.
- Angular displays plain text and expandable reference metadata. Its development
  proxy sends `/api` to FastAPI. There is no separate CORS configuration.

The saved artifact stores normalized text, paragraph numbers, word offsets, attribution
and technical-source section/XML locations.
Its IDs are stable for unchanged input, not across arbitrary source revisions.
There is no PDF extractor or production deployment configuration yet.

For this corpus size, disk files and an in-memory index are enough. Keep LangChain,
a vector database, graph infrastructure, authentication, and agent orchestration out
until a concrete requirement justifies them.

## Milestones

1. Local preview and document-only OpenAI integration: implemented and checked with
   automated tests and a small Luna/medium live smoke test. Frontend regression coverage
   now includes mocked component tests and Chromium keyboard/mobile smoke tests.
   Normal Chrome verification covered keyboard focus, response states and 320px/390px
   layouts with viewport screenshots. Earlier T3 preview capture was blocked by its
   host; that limitation and the Chrome follow-up are recorded above.
2. Baseline RAG: expand the four-paper starter set to 15–30 authorized documents; record source URL, author, date,
   license and permission evidence. Add PDF/text extraction with page references,
   and evaluate the implemented local embeddings. Evaluate the LLM provider's citations and
   insufficient-evidence behavior on the reviewed corpus.
3. Evaluation foundation: pinned synthetic smoke tests and source-reviewed technical
   questions, schema-1/2 validation, selectable retrieval adapters, controlled
   embedding comparisons, ranking/timing/memory diagnostics and human review. Model
   implementations belong in retrieval work. The [PR 8 source review](evaluation/reviews/2026-10-01-pr8/README.md)
   accepted 50 development and 36 held-out questions, rejected 14 overlapping or
   unsuitable drafts, and froze held-out before model selection. The owner approved
   all 86 accepted questions on 2026-10-01. Human approval and the new freeze hashes
   are recorded separately from the preserved AI source review. Answer-quality
   evaluation and a demonstration remain pending.
4. Extensions: demonstrate Azure deployment, compare a defined graph approach with
   the same baseline, then expose search/source retrieval through Python MCP.

Available budget is approximately $5 each on OpenAI and Anthropic. The default is
`gpt-6-luna`; the implementation smoke test used only Luna with medium reasoning.
Before larger paid runs, check a projected run budget. Per-request limits do not
enforce a provider-wide hard spending cap or limit the number of user submissions.

The [official Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna),
checked on 2026-09-28, lists standard rates of $0.10 per million input tokens and $0.50
per million output tokens. The two live implementation checks reported 929 input
and 82 output tokens in total, an estimated $0.000134 at those rates, not an invoice.
Recheck rates before the paid baseline. The provider follows the official
[structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs).

## Learning checkpoint

Read `Retriever.search` and the chunking test. With `--corpus sample`, compare
`Does dust cause false positives?` with `Can contamination trigger erroneous alarms?`.
Explain why lexical matching can behave differently for equivalent questions.
Then explain why a passage matching `illumination` cannot establish a numerical
defect-size limit. These are two different problems: retrieval recall and evidence
sufficiency. See the [local implementation checks](docs/retrieval-checks.md) for observed
rankings and limitations; reviewed retrieval and answer-quality comparisons are pending.

## Development disclosure

The initial code, fixtures, tests, CI configuration and documentation were generated
with AI assistance. The project owner provided the goals, constraints, technology
preferences and API budget. The owner reviewed and approved the 86 accepted technical
evaluation questions on 2026-10-01 after the recorded AI source review. Evaluation
of generated answers remains pending. Record subsequent contributions accurately;
do not present generated code as independently authored work.

See [the evaluation workflow](evaluation/README.md) for reproducible free runs,
the retrieval adapter interface, human review and remaining corpus work.
