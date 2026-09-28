# Evaluation procedure

No technical evaluation results exist yet. The three synthetic documents and backend
tests are development material, not a held-out evaluation set. Passing tests do
not demonstrate RAG answer quality.

## Reproduce the free development evaluation

From the repository root (Python 3.13 and the committed `uv.lock`):

```sh
rtk proxy uv sync --locked --python 3.13
rtk proxy uv run --directory backend python -m researchlens.ingest
rtk proxy uv run --directory backend python -m researchlens.evaluation run --dataset ../evaluation/datasets/development.json --other-split ../evaluation/datasets/held-out.json --output ../evaluation/runs/retrieval-k4
rtk proxy uv run --directory backend python -m researchlens.evaluation run --dataset ../evaluation/datasets/development.json --other-split ../evaluation/datasets/held-out.json --limit 1 --output ../evaluation/runs/retrieval-k1
rtk proxy uv run --directory backend python -m researchlens.evaluation report ../evaluation/runs/retrieval-k4 ../evaluation/runs/retrieval-k1 --output ../evaluation/runs/comparison.md
```

On Windows, `py -m uv` can replace `uv`. Without RTK, omit `rtk proxy`.
Use a fresh output directory/name for every run/report: existing artifacts are never
overwritten. `evaluation/runs/` is ignored by Git. Archive explicitly selected,
reviewed artifacts when publishing results. Do not commit credentials.

The default CLI path constructs only the local TF-IDF retriever and makes **zero API
calls**, regardless of `.env` or `ANSWER_PROVIDER`. `--mode local-preview` additionally
records the app's preview response. This is not generated-answer evaluation.
CLI output consists of `run.json`, a blank `review.json`, and `report.md`.
Repeat the `report` command after human review to include judgments. Compare runs
only with identical dataset and passage-artifact hashes; configuration differences
are recorded. Timing and run IDs vary, while pinned inputs and retrieval results are
reproducible. Git attributes enforce LF corpus bytes across Windows/Linux; rebuild
an older index after normalizing an existing checkout with `git add --renormalize`
only if you intend to stage those files. A fresh checkout already applies the rule.

## Dataset contract and current status

`backend/researchlens/evaluation_schema.py` defines strict, versioned Pydantic contracts
(`Dataset.model_json_schema()` exposes the JSON Schema). Unknown fields and inconsistent
reviews, duplicate IDs/questions, missing evidence, and one-source comparisons fail validation.

- `datasets/development.json`: three AI-authored, **unreviewed synthetic** examples
  covering factual, cross-document and missing-evidence questions. All reviewer/date
  fields are null. These may be used for implementation and tuning.
- `datasets/held-out.json`: deliberately empty, `pending-real-corpus`. It cannot run.
  No curated real documents are available in this checkout. Creating roughly 20
  real-corpus questions (8 factual, 8 comparison, 4 unanswerable) is **pending**.
  Do not pad the held-out set with synthetic questions or invent publications.

Each dataset records its split, version, material, status and raw source-file SHA-256.
Each case records category, expected source IDs, passage/paragraph/page references,
required claims, required qualifications, forbidden unsupported claims, expected
abstention, reviewer, date and review status. Text fixtures have no pages: use null,
never an invented page number. Passage/source/paragraph consistency is checked against
the pinned index; future PDF page references must be checked against full sources by
humans because today's passage API does not expose page numbers. For unanswerable
cases, references identify related context or explicitly missing measurements, not
positive answer evidence. They do not receive a recall score.

After real-corpus curation, draft questions as `unreviewed`, have a human check every
expectation against the **full sources**, fill identity/date, then mark `approved`.
Pin the corpus hash and freeze the reviewed held-out dataset (`status: frozen`).
Rejected questions must be corrected and reviewed again before freezing. Human review
cannot be inferred from schema validation. The CLI checks IDs and normalized questions
against the other split; semantic/paraphrase leakage still requires human inspection.
Never tune on held-out questions. Freeze before tuning, log access/exposure, and retire
an exposed held-out set if its failures inform changes; use a new version and fresh
questions for subsequent quality claims.

## Retrieval and generation integration

The app's retrieval API is unchanged. Embedding work can plug into:

```python
class Search(Protocol):
    def search(self, question: str, limit: int = 4) -> list[SearchHit]: ...

run_evaluation(dataset, artifact, retriever, retrieval_config,
               provider=None, generation=None)
```

Build/load the index outside the timed loop, then inject the implementation. Return
ranked, unique `SearchHit` objects from the exact pinned passage artifact, at most
`limit`; scores can be implementation-specific. Do not rewrite passage IDs or text.
Record implementation/version, k, model/revision, embedding artifact hash,
normalization and score threshold using `RetrievalConfig`; extend the strict schema
with explicit fields for other ranking options rather than dumping a client or env.
Local embeddings can therefore be evaluated without modifying the CLI or app API by
calling this Python entry point from an integration script. No embedding implementation
is included here. Call `validate_splits` before custom runs, as the CLI does.

An optional `AnswerProvider.answer(question, passages) -> Answer` records generated
sections/citation IDs, answer status, supplied passage references and token metadata.
Use `GenerationConfig(provider="mock")` for fake providers; mock usage is simulated,
with zero API cost. A custom adapter is trusted executable code: it must truthfully
declare its configuration and avoid remote requests in offline mode. The runner cannot
prove arbitrary Python adapters are offline. Providers own their lifecycle and closing.

There is intentionally **no paid CLI mode**. The Python runner accepts the existing
`OpenAIProvider` only with declared `gpt-6-luna`, medium reasoning, output limit matching
the provider (currently 2,000 tokens), zero client retries, and the SHA-256 of
`answers.INSTRUCTIONS`. It rejects unreviewed questions and requires a positive dated
`estimated_run_cost_usd` and `pricing_date` before invoking that provider. It never
loads keys or constructs a live client on its own. Construct and close a live provider
only in a deliberately authorized integration script; never serialize `Settings`.
The existing provider bounds context to four passages, each truncated to 3,000
characters, within a 16,000-character serialized context cap. Its returned references
retain full text; review the truncation boundary when assessing support available to
the model. Retrieval k can exceed four, so retrieved and model-supplied IDs can differ.

Before any live test, obtain current input/output rates and estimate
`(input_tokens * input_rate + max_output_tokens * output_rate) / 1_000_000`, summed
over requests with a conservative input allowance for instructions, question, context
and structured-output schema. Record rates, date, assumptions and budget alongside the
run. Estimates are not a hard spend cap. Prefer mocks and retrieval-only runs; do not
run broad paid evaluations on draft questions. No paid calls were used for this tooling.

## Artifacts and human review

Run artifacts snapshot the dataset/expectations, source and passage-artifact hashes,
chunking configuration, Git commit/dirty flag, evaluation code hash, Python/package
versions and lockfile hash, retrieval/model configuration, timestamp and run ID.
Per case they save ranked passage IDs/text/scores, answer sections and citations,
retrieval/generation/total latency, token usage, cost and errors. Outputs are intended
for local use; review licensed/private source text before sharing an artifact. Never
report a dirty-worktree run as a reproducible published baseline without archiving the
corresponding code. Index load/build time is excluded; the first request can be cold.

Errors stay in the result set, including retrieval successes followed by generation
failures. Only stable stage/error codes are saved: exception strings may contain
credentials or provider request data. On provider errors, usage/cost remains **unknown**,
including invalid completed answers whose usage the current provider cannot return.
No-call retrieval and previews cost zero. Known sums and unknown counts are separate;
do not interpret known sums as final billing totals. Per-request paid estimates may
remain null because the provider does not hardcode billing rates.

`review.json` is bound to the run ID and full canonical run hash. Reviewers inspect the
run's question, expectations, retrieved context and each answer section against full
sources, then record:

- Per section: correctness (`correct/incorrect/unclear`), citation support
  (`supported/unsupported/unclear`) and concrete evidence notes. Check every material
  claim within the section, including scope and qualifications; split notes by claim.
- Per answer: correctness (`correct/partial/incorrect/unclear/not-applicable`), overall
  citation support, whether required claims/qualifications are met, forbidden claims,
  and full/partial/no abstention (or `not-applicable` for retrieval/preview/errors).
- Reviewer, date and `status: complete` only after all judgments are filled. A blank
  template is pending, never a completed human review. Use notes for source/page
  evidence, missing claims, contradictions and error diagnosis.

**Valid citation IDs alone do not establish factual support.** Retrieval-only runs
have no correctness, citation-support or generated-abstention scores. No-match is a
retrieval outcome, not proof that the corpus cannot answer. Automatic status counts
are explicitly separate from human judgments; partial answers require manual review.
Reports show recall denominators/errors, comparison coverage, abstention counts,
review completion, latency and known/unknown usage. Do not rank model quality from
unreviewed examples or claim statistical certainty from a small held-out set.

After the authorized corpus is fixed, draft 20 questions: eight factual, eight
cross-document comparisons and four unanswerable questions. The owner must manually
review each question against full source documents, confirm supporting passages and
record review status before any reported evaluation. Unanswerable questions should
include plausible in-domain requests whose missing facts cannot be established merely
by retrieving related text.

Each case should record `id`, `question`, `category`, `expected_source_ids`, specific
page/passage references, required claims, forbidden unsupported claims, expected
abstention behavior, reviewer and review date. Suggestions should be assessed separately
from documented findings. Preserve source versions and the corpus hash.

Keep tuning questions in a separate development file. Freeze the held-out questions
before model/prompt tuning. If failures motivate tuning, disclose that exposure and
use new held-out questions for a fresh comparison.

## Run and assess

1. Record the commit, corpus hash, chunking parameters, embedding model/revision,
   retrieval settings, provider/model, prompt version and run time.
2. Save retrieved passage IDs, answer text, citations, wall-clock latency, input/output
   tokens, provider errors and estimated cost per request. Never save API credentials.
3. Compute source recall at k as retrieved expected sources divided by expected sources
   for answerable questions. Report cross-document coverage separately. Do not assign
   recall to questions with no expected sources.
4. Manually mark each material claim correct/incorrect/unclear, and cited support
   supported/unsupported/unclear. Valid citation IDs alone cannot establish support.
5. Report abstention on unanswerable cases and false abstention on answerable cases,
   with counts and concrete failures. Distinguish partial answers from full abstention.
6. Report per-request latency, median and maximum, noting cold starts and sample size.
   Record provider failures as failures rather than dropping them. Price estimates must
   include the pricing date and distinguish unknown usage from zero usage.

Use a small pilot on development questions to estimate cost before the held-out run.
Reserve $1 for the first evaluation, within the available $10 total credit. Do not
claim statistical certainty or model superiority from 20 examples.

## Initial implementation verification, 2026-09-25

- Local backend: 7 tests passed. One upstream Starlette warning says its httpx test
  client integration is deprecated; tests still completed successfully.
- Angular production build: passed.
- Live HTTP check through Angular's development proxy: frontend returned HTTP 200;
  the dust question returned `fixture-dark-field:p2:w0` first; the Beethoven question
  returned `no_matches`. This does not verify browser rendering or interactions.
- API usage: none; API cost: $0.
- Browser interaction and screenshots: pending, no browser connection available.
- Semantic retrieval, answer correctness and abstention quality: not measured.

These are implementation checks only. Replace this section with a linked, reproducible
evaluation artifact when the real corpus and reviewed questions are ready.

## OpenAI integration verification, 2026-09-28

- Backend: 27 tests passed, covering configuration, citation validation, abstention,
  no-call retrieval misses, request limits, and safe API failures. Tests use mocks;
  the real `.env` cannot turn the automated suite into paid requests.
- Angular production build and backend lint/format checks: passed.
- Two live requests through FastAPI's test client used only `gpt-6-luna`, with
  `reasoning.effort=medium`, at most 2,000 output tokens and no automatic retries:
  - `Does dust cause false positives?` returned `answered`, citing
    `fixture-dark-field:p2:w0` and explicitly describing a fictional experiment.
    Usage: 428 input / 48 output tokens; server latency: 4,056.97 ms.
  - `What is the minimum detectable defect size in micrometers for bright-field imaging?`
    returned `insufficient_evidence` with no generated claims.
    Usage: 501 input / 34 output tokens; server latency: 1,876.17 ms.
- `Who composed Beethoven symphonies?` returned `no_matches`, with no API request.
- Total measured usage: 929 input / 82 output tokens. Estimated cost: $0.000134,
  using the [Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna)
  rates checked that day ($0.10/M input, $0.50/M output). This is not billed usage verification.
- Browser rendering and interactions remain unverified: no browser was connected.
- These synthetic smoke questions are development cases, not held-out quality evaluation.
