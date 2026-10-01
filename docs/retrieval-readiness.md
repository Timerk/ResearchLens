# Retrieval evaluation readiness, 2026-10-01

PR #9 is rebased onto PR #8's approved-evidence commit
`f079ed1ad4c76c280d090c0b905fc23b0af3074a`. It is ready for local development
comparisons. PR #8 remains open, so this is a stack, not a merge to main.

The foundation has 50 approved development questions and 36 approved frozen held-out
questions. Separate owner approval covers the revised development labels: 92 groups,
140 alternatives and 165 span occurrences for the 36 answerable cases. The 14
development negatives remain unscored. The approval, AI audit and fix records retain
their original bytes and separate provenance. Retrieval work does not edit datasets,
evidence labels, source documents or review archives.

## Integration changes

- Rebase conflict resolution retains the new frontend layout/test workflow and its
  source-support wording, plus the warning that retrieval can return unrelated passages.
- The existing comparison command now passes `--evidence-labels` and `--cutoffs` to
  every retrieval mode. Its manifest records the label hash and review status.
- The existing runner creates `comparison.md` and `paired.json`, comparing each
  configuration against the first TF-IDF baseline. No second scoring framework.
- Stale dataset/label identity, unavailable cutoffs and invalid repeat limits fail
  before ingestion. Corpus/span/artifact compatibility remains the runner's check.

## Local verification

The real-model readiness probe uses TF-IDF, pinned MiniLM dense and MiniLM hybrid in
fresh processes on all 50 development cases. It runs one timed search per question,
with zero warmups, separately at actual limit 4 and at limit 10 with cutoffs 1/4/10.
It is an integration check, not a performance benchmark or model/settings selection.

Outputs use approved labels and remain ignored:

```text
evaluation/runs/readiness-approved-2026-10-01-k4/
evaluation/runs/readiness-approved-2026-10-01-ranking/
```

Each directory contains ingestion/model artifacts, the stage manifest, three existing
runner run/review/report directories, a comparison and paired per-question changes.
All six runs completed without errors. Their k=4 retrieved IDs and scored metrics
agree with the limit-10 prefix for all 50 questions in each configuration. Both
manifests and every run bind the same approved label hash. No held-out retrieval,
generation, OpenAI calls or settings tuning occurred. API cost is zero.

The probe identifies implementation commit
`d05eda3e2916ab35a57b2d6272013ddd2cf1deb8`. Its dirty flag reflects unrelated
untracked `.serena/`; documentation changes follow the probe. Older draft-label
readiness outputs remain separate and are not compared with approved-label results.

- Backend: 178 tests pass with optional model packages; 176 pass and two Torch tests
  skip in an isolated base environment. Existing Starlette/httpx warning remains.
- Ruff lint/format and Git whitespace checks pass.
- Frontend type/format checks, 21 component tests, production build and three Chromium
  smoke tests pass. Windows checkout line endings were restored to the pinned archive
  bytes and frontend formatting expectations without changing tracked source content.

## Start the development comparison

From the repository root, using fresh output directories:

```sh
rtk proxy uv sync --locked --extra embeddings --extra embedding-models --python 3.13
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.compare_retrieval --evidence-labels ../evaluation/labels/technical-development.json --output ../evaluation/runs/approved-models-k4
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.compare_retrieval --evidence-labels ../evaluation/labels/technical-development.json --limit 10 --cutoffs 1 4 10 --output ../evaluation/runs/approved-models-ranking
```

Defaults select all four pinned CPU embedding models, dense/hybrid modes, TF-IDF,
five timed repeats and one warmup per question. The two commands independently
ingest model artifacts; cached weights avoid first-download costs. k=4 is the primary
application metric; limit-10 query timings are a separate protocol. Ingestion wall
time includes process setup and any downloads, not pure encoding.

Freeze any chosen model/hybrid settings before held-out evaluation. The helper is
development-only; its other-split argument validates separation without querying
held-out questions. Record any configuration tuning and preserve original reports.

## Remaining limitations

Actual tokenizer-based passage visibility measurements are not implemented in the
embedding adapters. The new runner marks encoder token counts, truncation frequency
and evidence visibility unknown rather than inventing them. Ranking and full-passage
evidence coverage can run now; measured embedding-truncation analysis remains separate
integration work. Provider-context visibility preview is available without paid calls.

The [full approved development comparison](approved-model-comparison.md) now records
all nine configurations, separate k=4/ranking runs and paired regressions. The
[old 12-question measurements](model-comparison.md) remain historical and cannot be
compared with this scoring contract. Answer correctness,
citation support and abstention quality require a separate fixed-generation evaluation.
