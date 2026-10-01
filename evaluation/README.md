# Evaluation foundation

This workflow compares retrieval implementations on fixed questions and passages.
Four technical papers are available. The project owner approved the 86 accepted
technical questions on 2026-10-01 after the recorded AI source review.
The three synthetic cases remain smoke tests. Model quality and generated-answer
quality have not been evaluated on this human-approved set. Nearest neighbors and valid citation
IDs are not proof of support.

## Run free development diagnostics

From the repository root (Python 3.13 and committed `uv.lock`):

```sh
rtk proxy uv sync --locked --python 3.13
rtk proxy uv run --directory backend python -m researchlens.ingest --corpus technical
rtk proxy uv run --directory backend python -m researchlens.evaluation run --dataset ../evaluation/datasets/technical-development.json --other-split ../evaluation/datasets/held-out.json --retriever tfidf --repeats 5 --warmups 1 --measure-memory --output ../evaluation/runs/technical-k4
rtk proxy uv run --directory backend python -m researchlens.evaluation run --dataset ../evaluation/datasets/technical-development.json --other-split ../evaluation/datasets/held-out.json --limit 1 --repeats 5 --warmups 1 --measure-memory --output ../evaluation/runs/technical-k1
rtk proxy uv run --directory backend python -m researchlens.evaluation report ../evaluation/runs/technical-k4 ../evaluation/runs/technical-k1 --output ../evaluation/runs/technical-comparison.md
```

To run the original smoke tests, ingest `--corpus sample`, select
`--dataset ../evaluation/datasets/development.json`, and pass
`--source ../data/sample_documents.json`. The runner's source default matches the
technical ingestion CLI default. Do not mix the sample questions with a technical index.
On Windows, `py -m uv` can replace `uv`. Without RTK, omit `rtk proxy`.

Evaluation is manual. CI tests the tooling; it does not run a quality benchmark or
publish evaluation artifacts. The default CLI makes zero paid API calls regardless
of `.env` or `ANSWER_PROVIDER`. `--mode local-preview` also records the app's preview,
which does not generate answers. Each new output directory receives `run.json`,
`review.json` and `report.md`. Existing outputs are never overwritten.
`evaluation/runs/` is ignored by Git; archive deliberately selected, reviewed artifacts
when publishing results. Review licensed/private passage text before sharing it.
Never save API credentials.

## Datasets and source review

`evaluation_schema.py` defines strict Pydantic contracts; `Dataset.model_json_schema()`
exposes JSON Schema. Unknown fields, inconsistent reviews, duplicate IDs/questions,
missing references/claims and one-source comparisons fail validation.

- `datasets/development.json`: three AI-authored, unreviewed synthetic smoke cases.
- `datasets/technical-development.json`: 50 approved technical development cases,
  version `4-human-reviewed`; the development dataset remains editable (`draft`).
- `datasets/held-out.json`: 36 approved cases, version `3-human-reviewed-frozen`.
  The accepted subset is `frozen`, with its current file hash in `human-review.json`.
- [PR 8 review](reviews/2026-10-01-pr8/README.md): all 100 input decisions, 14
  rejected originals, source conflicts, alternative evidence and full-source scope.
  The original reviewer is Codex / GPT-6.1-Sol, identified as AI, dated 2026-10-01.
- [Human approval](reviews/2026-10-01-pr8/human-review.json): the project owner's
  confirmation on 2026-10-01, all 86 accepted case IDs and new version/freeze hashes.
  Case status remains `approved`; reviewer identity now identifies the human owner.
  The earlier AI review and all 14 rejected originals remain unchanged.

| Question type | Development | Held-out |
| --- | ---: | ---: |
| Exact technical terminology | 14 | 10 |
| Paraphrases | 13 | 9 |
| Cross-document questions | 9 | 7 |
| Unanswerable: unrelated or missing evidence | 14 | 10 |
| **Total technical questions** | **50** | **36** |

Unanswerable cases include 7 unrelated / 7 missing-evidence development questions
and 5 unrelated / 5 missing-evidence held-out cases. Paraphrases use everyday
descriptions of technical mechanisms; some original pairs retain technical names.
Cases cover optical cues, acquisition, labels, data preparation, network/loss roles,
evaluation and limitations across the four papers. They are correlated: paraphrases
and comparisons can reuse evidence within a split. More questions on four papers
do not create independent observations or broaden the corpus. Balance was not
preserved by adding replacement drafts merely to restore the original counts.

The source review checked semantic overlap and removed a development comparison
that exposed the held-out moving-chart blur target. Both sets still use the same
papers and related concepts; remaining partial context reuse is documented in the
review. All original tables, mathematical markup and 38 publisher figures were
inspected. No held-out retrieval, rankings, failure reports, model selection or
settings tuning informed this review. Do not inspect held-out rankings while tuning.

Each dataset records split/version/material/status, the source-file hash and original
source checksums/DOIs/dates. Cases record expected source IDs, specific passage/paragraph
and XML section/locator references, required claims/qualifications, forbidden claims,
expected abstention and review provenance. Page numbers are null for XML/text sources;
never invent PDF pages. References and original-source versions are checked against
the index. `validate_dataset_references(dataset, artifact)` provides a metadata-only
authoring check for either split without running retrieval or certifying support.
The execution guard in `validate_artifact` still requires held-out to be frozen and
every case to be approved. Approval records the named reviewer; the structural
validator cannot establish that a reviewer is human or that evidence is factual.
The full original XML and attribution are preserved in `data/technical/`.

For missing-evidence questions, references identify nearby context to inspect; they
are not positive relevance labels or proof that the requested information is absent.
Unrelated cases have no expected sources. Review absence against the full papers,
including omitted tables and figures, rather than relying on the prose extraction.

The technical prose extraction omits figures, tables and formula details. Source
review must check the originals, absence claims and alternative supporting passages.
Original-only evidence is recorded separately from retrieval references; do not
invent passage IDs for unextracted tables or formulas. Alternative prose passages
are relevance labels and may support only part of a multi-claim answer; retrieving
one does not certify complete factual support. Passage recall still measures the
fraction of listed relevant passages retrieved, not the fraction of claims proved.
Automated validation is not scientific review. New drafts use `unreviewed` with null
reviewer/date; reviewed decisions require truthful identity/date. Only approved
cases can be frozen. Owner approval is separate from the earlier AI source review
and does not claim a new exhaustive scientific source audit or generated-answer review.

Keep development and held-out questions separate. Freeze held-out before model/settings
selection; never tune on it. CLI overlap checks catch IDs/normalized identical questions,
while semantic/paraphrase leakage requires source review. Log exposure, retire a set
whose failures inform tuning, and use fresh questions for a subsequent quality claim.
Synthetic tests and draft retrieval diagnostics do not establish model superiority.

## Shared artifacts and controlled comparisons

`artifacts.load_artifact(path, source=...)` is shared with retrieval loading and accepts
schema-1 passages and schema-2 artifacts. Schema 2 can contain PR #9's
`embeddings.encoding`, `passage_ids`, `vectors` and `vectors_sha256`. A schema-2
passage-only artifact is valid for lexical retrieval. The validator checks:

- Corpus hash, unique passage IDs and chunking; when source is supplied, re-chunked
  passages must match text and all attribution/source locations.
- Embedding row order, dimensions, finite/nonzero values, L2 norms when declared and
  the little-endian float32 checksum. Encoding metadata uses an explicit allowlist.

The actual embedding adapter also verifies that its query encoder matches the saved
model, pinned revision and encoding. Evaluation never loads weights, computes document
vectors or substitutes a temporary schema-1 view.

Run schema 2 stores a shared passage fingerprint of the corpus hash, chunking and ordered
full normalized passage records: IDs, text, title, URL, license, kind, paragraph,
attribution and XML locations. Comparisons require matching dataset, corpus, chunking
and shared passage identity. Model vectors/encoding may differ and receive separate
full embedding-artifact and encoding hashes. Changing any shared input blocks a
controlled comparison. Old run schema 1 retains its strict full-artifact check;
regenerate legacy runs before mixing with new ones.

## Retrieval adapter and model configuration

The injected Python interface remains:

```python
class Search(Protocol):
    def search(self, question: str, limit: int = 4) -> list[SearchHit]: ...

run_evaluation(dataset, artifact, retriever, retrieval_config,
               execution=ExecutionConfig(repeats=5, warmups=1, measure_memory=True))
```

Return ranked, unique SearchHits from the exact pinned artifact, at most `limit`.
Scores are implementation-specific and must be finite. Build/load outside the query
loop, pass setup times explicitly, and call `validate_splits` before custom runs.
Injected adapters own their lifecycle and are trusted executable code.

CLI `--retriever tfidf|embeddings|hybrid` delegates to
`retrieval.load_retriever(backend, path, source=...)`. This branch provides the lexical
factory adapter; PR #9 owns embedding implementation/selection with that same interface.
Unavailable adapters fail explicitly rather than silently using TF-IDF. No second
encoder, hybrid algorithm or multi-model orchestration is implemented here. MiniLM,
BGE-M3, Qwen3-Embedding-0.6B and Qwen3-Embedding-4B are planned retrieval comparisons,
not measured model results in this PR.

After the retrieval adapter and a separate schema-2 technical index are available:

```sh
rtk proxy uv run --directory backend python -m researchlens.evaluation run --dataset ../evaluation/datasets/technical-development.json --other-split ../evaluation/datasets/held-out.json --source ../data/technical/documents.json --index ../data/minilm-index.json --retriever embeddings --repeats 5 --warmups 1 --measure-memory --output ../evaluation/runs/technical-minilm
rtk proxy uv run --directory backend python -m researchlens.evaluation report ../evaluation/runs/technical-k4 ../evaluation/runs/technical-minilm --output ../evaluation/runs/model-comparison.md
```

Strict `RetrievalConfig` records implementation/version/k, model/pinned revision,
runtime/version/backend, device, precision/quantization, dimensions, weights/tokenizer,
pooling, normalization, query/document instructions, maximum tokens, truncation, batch
size, CPU intra/inter-op thread settings and text representation. Hybrid settings include both candidate counts and
RRF k or weighted-score fusion settings. Named fields are allowlisted; never serialize
a client, credentials or whole environment/settings object.

PR #9's encoding fields populate the evaluation configuration. Runtime/device/precision,
quantization/truncation/batch size missing from its metadata remain null (unknown), never
guessed from a model name. Ask the adapter to publish truthful metadata or supply a
complete `--retrieval-config path.json` with selected backend and actual implementation
class. Declared encoding fields must match the artifact; `--limit` can override k.
Evaluation cannot verify arbitrary adapter settings from a label. Verify actual setup
before publishing a reproducible baseline. Versions of installed relevant libraries,
OS/architecture, lockfile, Git commit/dirty flag and evaluation code hash are recorded.

## Ranking, timing and memory

Source/passage recall and full cross-document source coverage are retained. The first
relevant passage rank and reciprocal rank use expected passage IDs, so rank three
contributes 1/3 rather than 1. MRR at k includes all answerable cases with misses/retrieval errors
as zero. Source/passage recall also have failure-inclusive summaries alongside scored
counts. Unanswerable/unrelated cases have no relevance score. Incomplete draft relevance
judgments may underestimate recall/MRR; review acceptable evidence before model selection.

Index read, validation and factory/model construction are recorded separately as
`index_load_time_ms`. Ingestion happens outside evaluation: supply an externally
measured `--ingestion-time-ms` or ExecutionConfig duration; omission means unknown.
Warmups are separate from timed query attempts. Repeats call local retrieval only;
answer generation is called at most once per case. Each timed attempt records latency,
IDs and errors; changed rankings are flagged. Failure stops remaining repeats without
retry and remains in the result set. Reports show sample counts, median/max query
latency, whole-case duration and setup costs. Use identical timing protocols in comparisons.

`--measure-memory` records native process lifetime peak RSS (Windows peak working set;
Unix `ru_maxrss`). This includes native allocations, but is a coarse high-water mark
rather than isolated per-model/per-query memory. Unavailable measurements are null.
Use a fresh process per model and distinguish cache-only/cold model load from warmed
queries. CPU speed and RAM feasibility for the 4B model require measurement in retrieval
work. API cost is zero for local runs; CPU time and RAM still matter.

## Optional generated-answer review

An optional `AnswerProvider.answer(question, passages) -> Answer` records answer
sections/citations, status, supplied references, latency, usage and errors. Mocks have
zero API cost. Retrieval-only runs cannot establish correctness or abstention quality.
No-match is a retrieval outcome, not proof that the corpus lacks an answer.

`review.json` is bound to the run ID and canonical run hash. Generated answers start
pending; retrieval/preview/error entries are explicitly not-applicable. Human reviewers
inspect every material claim against full sources and record per-section correctness
(correct/incorrect/unclear), citation support (supported/unsupported/unclear), evidence
notes, overall correctness/support, required claims and qualifications, forbidden claims,
and full/partial/no abstention. Complete reviews require identity/date and all judgments.
Valid citation IDs never automatically earn factual-support scores. Reports separate
automatic statuses from human judgments and expose review completion and errors.

There is no paid CLI mode. Injecting the existing OpenAIProvider requires reviewed
cases, gpt-6-luna/medium, the matching bounded output limit (currently 2,000), zero
client retries, the prompt hash and a positive dated cost estimate before any call.
The provider supplies at most four 3,000-character passages within 16,000 serialized
context characters; returned references retain full originals. Review truncation when
assessing evidence available to the model. Retrieval k may exceed model context size.

Before a deliberately authorized live pilot, obtain current rates and conservatively
estimate `(input_tokens * input_rate + max_output_tokens * output_rate) / 1_000_000`
over all planned requests, including prompt/context/schema overhead. Record assumptions,
date and budget. Estimates are not spend caps or billing totals. Prefer mocks/local
retrieval; no paid generation is needed for embedding comparisons.

Errors retain stable stage/code fields instead of exception strings that may expose
credentials. Failed paid requests can leave usage/cost unknown, including invalid
answers whose usage the current provider cannot return. Known sums and unknown counts
stay separate; no-call requests cost zero. Do not claim statistical certainty from a
small dataset. Dirty-worktree results require archived corresponding code before being
published as a reproducible baseline.

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
