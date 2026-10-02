# Complementary evidence selection experiment

This experiment tests recommendations from the project owner's
`rag-performance-investigation-2026-10-02.md`. It uses the existing evaluation
runner and approved development evidence groups. It does not change application
defaults, the answer provider, canonical passage text, citation IDs, or labels.
Held-out searches and generated-answer tests remain pending.

## Fixed experiment

The predefined eight configurations compare Qwen3-4B dense, BGE-M3 dense and
BGE-M3 with BGE reranking over 20 candidates against five selection variants.
The variants test Qwen and BGE dense facet selection, BGE reranking with title
and section context, and BGE facet reranking with and without that context.
Every configuration returns four canonical passages. The dense vectors are
unchanged, so this study tests metadata enrichment only in reranking.

The selector uses the original question and indexed document metadata, never
evaluation claims, labels or expected document IDs. It adds at most two queries.
Distinctive words in each document's title and first passage identify studies.
For a multipart question matching exactly two studies, it adds a query focused
on each study and restricts that query's candidate route to that document.
Otherwise, explicit question clauses such as "what ... and how ..." are split,
retaining an introductory topic and a matched study title where available.
Each internal query is limited to 2,000 characters. These English rules can miss
implicit comparisons or mistakenly identify a study; they are experimental.

The original top 20 candidates are retained. Additional routes contribute
candidates in alternating rank order until the union reaches at most 40.
Single-query cases have only 20 candidates. Candidate metrics at 40 therefore
measure the actual union, which can contain fewer than 40 distinct passages.
This union is ordered by candidate insertion, not a fused relevance ranking.

Each candidate is scored against each query using cosine similarity or the
local BGE cross-encoder. Rank utilities are `11 / (11 + zero_based_rank)` within
the query's allowed document set. Greedy selection maximizes the weighted
improvement over the best utility already selected for each query. The original
query has weight 0.5 when subqueries exist; subqueries have weight 1. Once no
query improves, original-query utility fills the remaining slots. This favors
different requested parts but does not prove factual coverage or answerability.

Metadata reranking inputs are `Title: <title>`, `Section: <section path>`, a blank
line, and canonical passage text. Pair measurements count this actual enriched
input. Truncated, stale or unordered measurements fail. Canonical coverage
ranges are recorded only after verifying complete encoding, preserving the
shared evaluator's text/hash contract. The selection sidecar records every
query's measurements; standard reranker diagnostics describe the original query.

## Reproduce

From the repository root, with previously ingested pinned model artifacts and
the prepared Vulkan runtime:

```sh
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.selection_experiments --runtime ../.venv/vulkan --indexes ../evaluation/runs/approved-models-2026-10-01-k4/indexes --output ../evaluation/runs/selection-improvements-new
rtk proxy uv run python docs/selection-results.py evaluation/runs/selection-improvements-new docs/complementary-selection-results.json
```

Each configuration runs in a fresh child process with one warmup and three timed
repeats on all 50 development questions. There are 36 answerable cases and 14
negative cases. Metrics exclude negatives where support is undefined. The plan,
source hashes, corpus/vector hashes, approved label hashes, document profile hash,
and runtime settings are saved before any searches. No inference cache, paid
API, model download, automatic retry, or held-out search is used. The GPU server
keeps its host prompt cache disabled and its existing memory guard.

`EvidenceSelector.search(question, limit)` can be injected into
`run_evaluation` like the existing retrievers. `selection_settings` records its
strict configuration. `get_encoding_diagnostics` delegates to the unchanged
dense artifact. `get_reranking_diagnostics(question)` exposes canonical-mapped
measurements. `RecordingSearch` adds observation without changing inference.
Quality scoring remains in `evaluation.py` and `evaluation_evidence.py`.

## Results

None of the five new variants beats the incumbent BGE-M3 plus ordinary BGE
reranking over 20 candidates. Retain the existing frozen experimental selection
in `development-selected-vulkan-retrieval.json`. Application defaults stay unchanged.

| Configuration | Complete evidence@4 /36 | Median query ms | p95 query ms |
| --- | ---: | ---: | ---: |
| Qwen3-4B dense control | 24 | 217.6 | 251.8 |
| BGE-M3 dense control | 22 | 25.3 | 28.9 |
| BGE-M3 + BGE20 control | 26 | 487.4 | 685.5 |
| Qwen3-4B + split queries and selection | 22 | 236.0 | 866.3 |
| BGE-M3 + split queries and selection | 21 | 27.9 | 108.1 |
| BGE-M3 + BGE20 with title/section context | 25 | 585.1 | 834.6 |
| BGE-M3 + split queries + BGE40, plain text | 22 | 605.8 | 3,569.8 |
| BGE-M3 + split queries + BGE40, title/section | 22 | 784.5 | 4,361.2 |

All three controls reproduce every saved passage ranking, not just aggregate
scores. All eight configurations finish all 50 cases: 1,200 timed searches, zero
case errors, and no unstable repeat rankings. One warmup per case is additional.
The runtime source snapshot is commit `ea9e857`, with individual source hashes
in the manifest. Untracked research notes and result documentation account for
the worktree's dirty provenance; runtime source matches the recorded commit.

| Configuration | Hit@4 /36 | Approved group coverage@4 | MRR@4 | Both sources /9 | Reference passage recall@4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen dense | 32 | 78.3% | 0.715 | 6 | 69.3% |
| BGE dense | 30 | 70.8% | 0.593 | 7 | 61.4% |
| BGE + BGE20 | 33 | 80.3% | 0.833 | 8 | 71.7% |
| Qwen split selection | 31 | 74.7% | 0.602 | 8 | 63.5% |
| BGE split selection | 29 | 67.2% | 0.484 | 9 | 56.0% |
| BGE + BGE20 metadata | 33 | 78.9% | 0.812 | 7 | 72.9% |
| BGE split + BGE40 plain | 33 | 76.4% | 0.736 | 9 | 66.8% |
| BGE split + BGE40 metadata | 32 | 77.0% | 0.757 | 9 | 67.8% |

Reference recall uses the original passage references. Group coverage and
completeness accept approved alternative support sets. They are distinct metrics.
Both-source representation is also weaker than complete evidence: the two split
reranking configurations include both sources for 9/9 comparisons but complete
only 4/9, versus 7/9 for ordinary BGE20.

| Configuration | Terminology /14 | Paraphrase /13 | Cross-document /9 |
| --- | ---: | ---: | ---: |
| Qwen dense | 11 | 8 | 5 |
| BGE dense | 10 | 8 | 4 |
| BGE + BGE20 | 11 | 8 | 7 |
| Qwen split selection | 11 | 8 | 3 |
| BGE split selection | 10 | 7 | 4 |
| BGE + BGE20 metadata | 11 | 8 | 6 |
| BGE split + BGE40 plain | 10 | 8 | 4 |
| BGE split + BGE40 metadata | 10 | 8 | 4 |

The metadata-only variant improves reference recall while losing complete
support for `tech-compare-training-splits`. It has no completeness gains against
BGE20. The other four variants likewise have no completeness gains against their
respective dense or reranked controls. Qwen split selection loses
`tech-compare-data-expansion` and `tech-compare-evaluation-metrics`; BGE split
selection loses `tech-stable-camera` against BGE dense. Against BGE20, plain split
reranking loses `tech-amff-layers`, `tech-compare-training-splits`,
`tech-compare-training-computers`, and `tech-compare-evaluation-metrics`.
Metadata split reranking loses the same first three and
`tech-compare-data-expansion`. Full paired outcomes against Qwen dense are in
[the shared runner's paired report](complementary-selection-paired.json).

## Failure diagnosis and resources

The rules split 21/50 questions. Some study matches are wrong: for example,
`tech-glass-paraphrase` acquires a second route for the transfer-learning paper,
and `tech-wafer-paraphrase` acquires one for the autoencoder paper. Distinctive
vocabulary in a document profile is insufficient evidence that the user named
that study. The source restriction can then spend a slot on irrelevant evidence.
The original candidate pool is preserved, but final selection can still regress.

For Qwen split selection, original top-20 candidates complete 33/36 questions;
the union completes 34/36, while final selection completes only 22/36. BGE's
original top 20 complete 31/36 and its split-query union completes 32/36; final
selection completes 21/36 without reranking or 22/36 with reranking. The
metadata-only pool contains 20 candidates and completes 31/36, not a distinct
40-candidate measurement. Pools range from 20 to 40 actual candidates. These
measurements describe candidate insertion prefixes, not a single fused ranking.

The greedy maximum-rank utility selects the best-ranked passage per query. It
does not identify multiple facts or qualifications within a query, and a
study-focused copy of the whole question is not a precise subquestion. Once
query maxima are covered, original-query ranking fills remaining slots. This
experiment rejects these particular decomposition and selection rules; it does
not show that all complementary-evidence methods fail.

Maximum measured pair inputs are 414 tokens for metadata-only reranking, 413
for plain split reranking, and 472 for metadata split reranking, all within the
511-token guard. All recorded enriched pairs are untruncated. Selection sidecars
retain measurements from the last attempt of each case, not every repeat.
The dense embedding representation and its previous visibility measurements are
unchanged. Increasing the context window would not address the measured failures.

Native GPU-server private-memory peaks are 2.20 GiB for the control, 2.35 GiB for
metadata-only reranking, 2.33 GiB for plain split reranking, and 2.46 GiB for
metadata split reranking. Fresh-process Python peak working sets are about
3.92 GiB for BGE configurations and 8.14 to 8.21 GiB for Qwen configurations.
These are separate process high-water measurements, not simultaneous totals or
VRAM measurements. All owned benchmark servers are stopped after their runs.

The next experiment should test more conservative study identification and
explicit factual subquestions, with candidate-union and selector-only ablations
to isolate their contributions. Metadata enrichment of dense vectors, lexical
inputs, and neighboring-passage representations were not tested here. They
require a separately versioned encoding experiment; canonical chunk changes
also require renewed evidence mapping and review.

[Archived metrics and selection diagnostics](complementary-selection-results.json)
include the fixed plan, runtime/input/source hashes, actual candidate counts,
per-question outcomes, query routes, cohorts and memory summaries. Full generated
run files remain ignored under `evaluation/runs/selection-improvements-2026-10-02`.
This small, correlated four-paper development study does not establish general
quality. Retrieval evidence does not establish generated-answer correctness,
citation support or abstention. All 14 negatives still receive nearest neighbors;
no similarity threshold or answerability claim was introduced. API cost is zero.
