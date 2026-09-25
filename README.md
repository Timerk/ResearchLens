# ResearchLens

An independent portfolio project for exploring a curated technical document collection.
The intended application will answer research questions with
inspectable supporting passages and distinguish findings from suggestions.

The first slice runs Angular and FastAPI end to end with three **synthetic test documents**.
It retrieves passages using TF-IDF word matching. It does not yet call an LLM, compute
semantic embeddings, or determine whether evidence is sufficient. Do not treat the
fixtures as technical findings.

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
No API key is needed. `.env.example` explains the current configuration status;
the preview does not load an environment file.

Try `Does dust cause false positives?` and inspect the first reference. Then try
`Who composed Beethoven symphonies?` for the no-match state.

## Verify

```sh
rtk proxy uv run pytest -q
rtk proxy uv run ruff check backend
rtk proxy uv run ruff format --check backend
```

From `frontend`, run `rtk npm run build`. GitHub Actions runs these checks after
the project is pushed. CI has not yet been run on GitHub.

## Architecture and boundaries

```text
JSON documents → paragraph/word chunking → versioned passage artifact
                                                   ↓
Angular → POST /api/ask → TF-IDF retrieval → answer provider → passage references
```

- `backend/researchlens/ingest.py` validates text documents, preserves metadata,
  and writes a corpus hash and deterministic passage IDs. Rebuild after corpus edits.
- `retrieval.py` rebuilds a small TF-IDF matrix at startup. Cosine similarity ranks
  shared words. A positive score is not proof of answerability.
- `answers.py` defines the provider boundary and an honest local preview. A later
  provider will receive the question and retrieved passages, never the entire corpus.
- `api.py` owns HTTP validation and request timing. Missing or corrupt indexes
  stop startup with an actionable message.
- Angular displays plain text and expandable reference metadata. Its development
  proxy sends `/api` to FastAPI. There is no separate CORS configuration.

The saved artifact stores normalized text, paragraph numbers, and word offsets.
Its IDs are stable for unchanged input, not across arbitrary source revisions.
There is no PDF extractor or production deployment configuration yet.

For this corpus size, disk files and an in-memory index are enough. Keep LangChain,
a vector database, graph infrastructure, authentication, and agent orchestration out
until a concrete requirement justifies them.

## Milestones

1. Local preview: complete implementation and automated checks. Browser verification
   is pending because no browser connection was available in the development session.
2. Baseline RAG: curate 15–30 authorized documents; record source URL, author, date,
   license and permission evidence. Add PDF/text extraction with page references,
   local embeddings, and an LLM provider with structured citations, timeouts,
   token accounting and explicit insufficient-evidence responses.
3. Evaluation: review roughly 20 held-out questions, run retrieval and answer
   evaluation, report failures and costs, and capture a demonstration.
4. Extensions: demonstrate Azure deployment, compare a defined graph approach with
   the same baseline, then expose search/source retrieval through Python MCP.

Available budget is approximately $5 each on OpenAI and Anthropic. Start with
`gpt-6-luna`, subject to account availability, and reserve Haiku for comparison.
No API calls have been made. Before paid runs, cap output, disable uncontrolled
retries, and check a projected run budget. Application estimates do not enforce a
provider-wide hard spending cap.

The [official Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna),
checked on 2026-09-25, lists standard rates of $0.10 per million input tokens and $0.50
per million output tokens. At 4,000 input and 600 output tokens, a request would cost
$0.0007, before additional reasoning tokens, retries or other charges. This is a
planning example, not measured project usage. Recheck rates before the paid baseline.

## Learning checkpoint

Read `Retriever.search` and the chunking test. In the running app, compare
`Does dust cause false positives?` with `Can contamination trigger erroneous alarms?`.
Explain why lexical matching can behave differently for equivalent questions.
Then explain why a passage matching `illumination` cannot establish a numerical
defect-size limit. These are two different problems: retrieval recall and evidence
sufficiency. We will use both observations when adding embeddings and generation.

## Development disclosure

The initial code, fixtures, tests, CI configuration and documentation were generated
with AI assistance. The project owner provided the goals, constraints, technology
preferences and API budget. Manual code review, technical-source review and evaluation
judgments by the owner are still pending. Record subsequent contributions accurately;
do not present generated code as independently authored work.

See [the evaluation procedure](evaluation/README.md) for what remains before reporting
answer quality.
