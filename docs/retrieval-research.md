# Retrieval research

The application supports TF-IDF, pinned CPU embeddings, weighted hybrid fusion,
optional MiniLM CPU reranking and a character-budgeted answer context. TF-IDF and
the four-passage context remain the defaults. See [embedding setup](embeddings.md)
for installation and supported configuration.

## Result

The owner approved and adopted readable formula extraction on 2026-10-14.
[Current development results](formula-adoption-results.md) confirm Qwen3-4B dense
still meets all five targets at 12k and 16k, with 29/36 and 33/36 complete evidence
and MRR 0.741. All four hardware-tier indexes were rebuilt against the adopted corpus.
The phase-1 intervention and older experiments below retain their original pins.

Retrieval was not the binding constraint. Candidate rankings already contained
complete approved evidence for 31-34 of 36 answerable development questions. The
provider, however, received only four short passages, about 3,000 of its 16,000
allowed serialized characters. Filling that budget in ranked order meets all five
development retrieval targets with Qwen3-4B dense at 12k and 16k characters. See
the [context budget study](context-budget.md) for measurements, statistics and the
development-selected configuration.

## Archived experiments

The experiments that led here are kept under the Git tag
[`research/retrieval-2026-10`](https://github.com/Timerk/ResearchLens/tree/research/retrieval-2026-10).
They are not part of the application or the maintained evaluation code. The tag
contains their modules, tests, study documents, result archives and archive scripts.
Summary result JSON files there link to full per-case archives by commit hash.

| Study (archived) | What it established |
| --- | --- |
| [Approved CPU comparison](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/approved-model-comparison.md) | Nine model/hybrid configurations at four passages; Qwen3-4B dense best with 24/36 complete. |
| [Retrieval improvements](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/retrieval-improvements.md) | Weighted fusion, MiniLM reranking and diversity did not beat Qwen3-4B dense at four passages. |
| [Vulkan reranking](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/vulkan-reranking.md) | GPU BGE reranking over BGE-M3 reached 26/36 at four passages; evaluation-only backend. |
| [Complementary selection](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/complementary-selection.md) | Query splitting and metadata reranking regressed. |
| [Information needs](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/information-needs-experiments.md) | Fixed-pool selectors and contextual vectors gave no better result. |
| [Selection diagnostics](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/selection-diagnostics.md) | Candidate-pool ceilings showed ordering, not recall, limited four-passage results. |
| [Historical CPU comparison](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/model-comparison.md) | Earlier draft-label results; not comparable with approved-label scores. |

Generated runs, vectors, weights and logs belong in ignored `evaluation/runs/` or
the model cache.

## Status

Hardware tiers, startup memory checks and readable formula extraction are implemented.
The one-time [held-out confirmation](held-out-results.md) has run. Qwen3-4B passes four
of five strict targets and misses recall@4 at 77.6%. The current-corpus
[answer-quality study](answer-quality.md) kept the four-passage default because the
registered comparison did not show an improvement. The [results page](results.md)
summarizes the whole sequence. Keep the approved datasets, labels and source text fixed
for later comparisons.
