# Evaluation procedure

No technical evaluation results exist yet. The three synthetic documents and backend
tests are development material, not a held-out evaluation set. Passing tests do
not demonstrate RAG answer quality.

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
