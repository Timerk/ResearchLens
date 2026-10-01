# Approved development model comparison, 2026-10-01

All nine retrieval configurations ran on the 50 approved development questions and
their separately approved evidence labels. Qwen3-4B dense has the highest complete
evidence rate in this development run: 24/36 answerable questions, or 66.7%. None
reaches the provisional 80% complete-evidence target. Hybrid helps MiniLM, leaves
Qwen3-0.6B's complete-evidence count unchanged, and reduces it for BGE-M3 and Qwen3-4B.
No held-out questions, settings tuning, answer generation or OpenAI calls occurred.

These results measure retrieval against the approved labels, not generated-answer
correctness or citation support. They replace neither the frozen held-out test nor
a separate answer/abstention evaluation. The historical 12-draft-question scores use
different questions and a different scoring contract and cannot be compared numerically.

## Protocol and provenance

- Implementation: `31d1e380dacc4b65b1974128f3ef2a09fb86db6d`, stacked on PR #8's
  approved-evidence commit `f079ed1`. The recorded dirty flag reflects unrelated
  untracked `.serena/`; executable code and the lockfile matched the archived commit.
- Same four CC BY 4.0 papers and 204 paragraph/180-word passages in every mode.
  Stable passage IDs, full attribution and source section/XML locations are unchanged.
- 50 approved development questions: 14 exact-terminology, 13 paraphrase, nine
  cross-document and 14 negatives. The 36 answerable questions have 92 groups,
  140 alternatives and 165 span occurrences. Seven unrelated and seven missing-evidence
  questions are visible in the reports but have no positive relevance score.
- Approved label canonical SHA-256:
  `8e1b118b740f615c5985eda60936b796cf7abb8c2c302b7845ffbcaa93b1973f`.
  Corpus SHA-256: `cda1b161618373b9c7b9701d3326fda4707f9501bbc3bf29c802d9a000908bce`.
  Shared passage identity:
  `c7bf2f1f6b9c866573669f946866b5b0635ae4afcee1d06511e3109ab47c1157`.
- Fixed settings from [the pinned encoding contracts](embeddings.md). MiniLM uses
  ONNX float32/256 tokens; BGE/Qwen use CPU Torch bfloat16/512 tokens. Hybrid uses
  20 lexical and 20 dense candidates, equal-contribution RRF k=60 and artifact-order
  ties. No threshold, reranker, diversity policy or parameter adjustment.
- Two sequential protocols, each in a fresh process per configuration. Actual
  limit 4 measures application retrieval; limit 10 scores prefixes at 1/4/10.
  The ranking pass reuses the exact vectors from the first pass. Five timed queries
  and one warmup per question give 250 timing samples per run, 4,500 across 18 runs.
- CPU only, Windows AMD64/Python 3.13.14, Ryzen 7 9800X3D, 32 GiB RAM. RX 6800 unused.
  Runtime versions and the lockfile hash are archived with the result excerpts.

Local full runs remain ignored under:

```text
evaluation/runs/approved-models-2026-10-01-k4/
evaluation/runs/approved-models-2026-10-01-ranking/
```

The first contains five ingested artifacts, nine existing-runner reports and its
stage manifest. Both contain `comparison.md` and TF-IDF-baseline `paired.json`.
[Selected result excerpts](approved-model-comparison-results.json) archive run IDs,
file/artifact/code hashes, settings, cutoff/cohort summaries and hybrid-versus-dense
paired changes. All scoring comes from the existing evaluation modules.

All 18 runs completed with zero errors and stable rankings across repeats. For every
configuration and all 50 questions, actual limit-4 passage IDs and metrics exactly
match the limit-10 ranking's first four results. Artifact, dataset, evidence-contract
and runtime identities were checked before extracting the archived summaries.

## Primary k=4 evidence results

Mean group coverage averages the fraction of satisfied groups per answerable question.
It accepts OR alternatives and requires every span of an AND alternative. Complete
evidence requires every group for a question, including labeled factual qualifications.
MRR considers the first passage belonging to any approved evidence group; it can be
high when the rest of the evidence is missing. Source presence alone is insufficient.

| Configuration | Mean group coverage | Complete evidence | MRR@4 |
| --- | ---: | ---: | ---: |
| TF-IDF | 55.2% | 15/36, 41.7% | 0.558 |
| MiniLM dense | 61.8% | 17/36, 47.2% | 0.544 |
| MiniLM hybrid | 66.2% | 18/36, 50.0% | 0.653 |
| BGE-M3 dense | 70.8% | 22/36, 61.1% | 0.593 |
| BGE-M3 hybrid | 67.8% | 21/36, 58.3% | 0.632 |
| Qwen3-0.6B dense | 61.3% | 18/36, 50.0% | 0.542 |
| Qwen3-0.6B hybrid | 62.2% | 18/36, 50.0% | 0.630 |
| Qwen3-4B dense | 78.3% | 24/36, 66.7% | 0.715 |
| Qwen3-4B hybrid | 68.7% | 21/36, 58.3% | 0.678 |

Qwen3-4B hybrid retrieves every expected source document at k=4, yet supplies complete
labeled evidence for fewer questions than dense retrieval. BGE-M3 hybrid raises MRR
while reducing coverage and the complete-evidence count. Aggregate ranking measures
therefore cannot replace complete-evidence scoring.

## Ranking depth and supplied context

Complete-evidence counts out of 36 answerable questions:

| Configuration | k=1 | k=4 | k=10 |
| --- | ---: | ---: | ---: |
| TF-IDF | 7 | 15 | 26 |
| MiniLM dense | 9 | 17 | 24 |
| MiniLM hybrid | 9 | 18 | 25 |
| BGE-M3 dense | 10 | 22 | 27 |
| BGE-M3 hybrid | 9 | 21 | 28 |
| Qwen3-0.6B dense | 8 | 18 | 23 |
| Qwen3-0.6B hybrid | 7 | 18 | 27 |
| Qwen3-4B dense | 13 | 24 | 27 |
| Qwen3-4B hybrid | 9 | 21 | 29 |

Qwen3-4B hybrid reaches 29/36 (80.6%) at k=10, but this is a ranking diagnostic.
The unchanged provider context selects only the first four passages. Context preview
therefore retains complete evidence for the same number of questions as k=4 in every
mode. In the limit-10 runs, selection loses at least one retrieved evidence group in
5–12 answerable cases per mode. No evidence loss from character truncation was
observed in either protocol. Increasing search depth alone does not supply more
evidence to the answer provider.

## Query cohorts and hybrid regressions

Complete-evidence counts at k=4, with denominators shown in the columns:

| Configuration | Exact terminology /14 | Paraphrase /13 | Cross-document /9 |
| --- | ---: | ---: | ---: |
| TF-IDF | 11 | 3 | 1 |
| MiniLM dense | 10 | 5 | 2 |
| MiniLM hybrid | 10 | 5 | 3 |
| BGE-M3 dense | 10 | 8 | 4 |
| BGE-M3 hybrid | 11 | 5 | 5 |
| Qwen3-0.6B dense | 10 | 6 | 2 |
| Qwen3-0.6B hybrid | 10 | 5 | 3 |
| Qwen3-4B dense | 11 | 8 | 5 |
| Qwen3-4B hybrid | 12 | 5 | 4 |

Hybrid improves exact terminology for BGE-M3 and Qwen3-4B, while both lose complete
support on three paraphrase questions. Equal lexical/dense fusion is consequently
not a reliable improvement across models on this development set.

The existing paired scorer compares group coverage, reciprocal rank and source recall.
An improvement can affect ranking alone; it need not make the evidence complete.
The 14 negatives are unscored in these paired outcomes.

| Hybrid versus its dense model | Improved | Worsened | Mixed | Unchanged |
| --- | ---: | ---: | ---: | ---: |
| MiniLM | 13 | 3 | 0 | 20 |
| BGE-M3 | 11 | 7 | 1 | 17 |
| Qwen3-0.6B | 11 | 6 | 0 | 19 |
| Qwen3-4B | 9 | 8 | 2 | 17 |

All four hybrids lose all labeled evidence for `tech-turn-and-flip-labels` compared
with their dense counterparts. Qwen3-4B hybrid also loses all labeled evidence for
`tech-manual-outline-union`, `tech-small-photo-supply` and
`tech-compare-evaluation-metrics`. BGE-M3 hybrid improves reciprocal rank by 0.5 on
`tech-compare-optical-cues` while reducing group coverage by 0.5 and losing completeness.
These cases warrant inspection before changing fusion settings.

MiniLM hybrid gains complete support for `tech-stable-camera` and
`tech-compare-data-expansion`. Qwen3-0.6B hybrid gains completeness on three questions
and loses it on three others: its unchanged aggregate count hides these exchanges.
The archive preserves per-question passage IDs, metric deltas and completeness changes.

## Unrelated and missing-evidence questions

TF-IDF returns neighbors for six of seven unrelated questions and all seven
missing-evidence questions. Every dense and hybrid configuration returns neighbors
for all 14 negatives. Returned neighbors do not establish that the question has a
supported answer, and no similarity threshold was calibrated. The answer provider's
abstention behavior is unchanged; its actual performance is unmeasured here because
these runs do not generate answers.

## Application-limit CPU measurements

These are the actual k=4 run's query medians and nearest-rank p95 over 250 successful
timed searches per mode. Warmups and setup are excluded. Peak RSS is each fresh
process's lifetime high-water mark, including index/model loading and native allocations.
Small timing differences between dense and hybrid do not establish a speed advantage.

| Configuration | Query median, ms | Query p95, ms | Peak RSS, GiB |
| --- | ---: | ---: | ---: |
| TF-IDF | 0.45 | 0.59 | 0.147 |
| MiniLM dense | 1.47 | 2.10 | 0.309 |
| MiniLM hybrid | 2.48 | 3.39 | 0.308 |
| BGE-M3 dense | 26.59 | 33.70 | 3.901 |
| BGE-M3 hybrid | 27.94 | 34.14 | 3.901 |
| Qwen3-0.6B dense | 45.70 | 57.87 | 1.692 |
| Qwen3-0.6B hybrid | 47.76 | 55.92 | 1.693 |
| Qwen3-4B dense | 217.43 | 248.41 | 8.117 |
| Qwen3-4B hybrid | 215.34 | 249.65 | 8.118 |

The largest model remains feasible on this machine. These measurements do not establish
concurrent server throughput or GPU performance. Cached-weight ingestion wall times
include process setup, tokenizer/model loading and encoding; they are not pure encoder
benchmarks. Rankings at limit 10 use a separate timing protocol.

## Reproduce

The k=4 command used the existing comparison helper without changing any settings:

```sh
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.compare_retrieval --evidence-labels ../evaluation/labels/technical-development.json --output ../evaluation/runs/approved-models-2026-10-01-k4
```

Choose fresh output directories when reproducing. The ranking pass runs this existing
CLI once per configuration, selecting the matching index and retriever. Example:

```sh
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.evaluation run --dataset ../evaluation/datasets/technical-development.json --other-split ../evaluation/datasets/held-out.json --source ../data/technical/documents.json --index ../evaluation/runs/approved-models-2026-10-01-k4/indexes/qwen3-4b.json --retriever embeddings --evidence-labels ../evaluation/labels/technical-development.json --limit 10 --cutoffs 1 4 10 --repeats 5 --warmups 1 --measure-memory --output ../evaluation/runs/approved-models-2026-10-01-ranking/qwen3-4b-embeddings
```

The [readiness documentation](retrieval-readiness.md) also gives a single helper command
for all ranking configurations, which independently re-ingests artifacts. This run
instead reuses indexes to ensure identical vector artifacts and avoid duplicate encoding.

## Limits and next decisions

Complete-evidence coverage is below the provisional 80% development goal in every
configuration. Qwen3-4B dense is the strongest observed starting point for further
development work; MiniLM hybrid is inexpensive and improves on MiniLM dense here.
Do not adopt hybrid universally or claim held-out superiority from these results.

No model/hybrid setting was tuned. Any subsequent configuration experiment belongs
on development only, with settings and labels fixed across compared modes. Freeze
the selected settings before the 36-question held-out evaluation.
Several questions reuse related concepts from four papers; they are not independent
observations or evidence of performance on a broader research corpus.

Actual encoder token retention and truncation frequency remain unknown because the
adapters do not publish tokenizer measurements. Full returned passages can contain
evidence outside the encoded prefix. The approved labels are conservative and not
exhaustive, and the corpus is a partial prose extraction. Answer correctness, citation
support and abstention quality remain pending; nearest neighbors do not prove an answer
exists. No API calls or paid-generation cost occurred.
