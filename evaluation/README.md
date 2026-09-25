# Evaluation procedure

No technical evaluation results exist yet. The three synthetic documents and backend
tests are development material, not a held-out evaluation set. Seven passing tests do
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
