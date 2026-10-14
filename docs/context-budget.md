# Serialized answer context studies

## Adopted formula corpus, 2026-10-14

The owner approved readable MathML extraction and evidence migration on 2026-10-14.
The [canonical rerun](formula-adoption-results.md) rebuilt all four tier indexes and
reconfirmed all five targets for Qwen at 12k and 16k. Qwen's complete counts are
24/36 at four passages, 29/36 at 12k and 33/36 at 16k; MRR is 0.731, 0.741 and
0.741 respectively. At 12k and 16k, reference recall is 85.2% and 88.6%, evidence
hit is 35/36, and both sources are present for all nine cross-document questions.
BGE complete counts are 21/36, 28/36 and 30/36; TF-IDF has 15/36, 26/36 and 26/36.

[Active selection pins](development-selected-context-budget.json) now describe the
adopted corpus and approved labels. No held-out retrieval or paid API call ran.
The historical study below and its original hashes remain evidence for the previous
corpus. Its 30/36 Qwen12k count is superseded by the current 29/36 measurement.

## Historical pre-rendering study, 2026-10-13

The smallest tested character budget that reaches the provisional 80% target is
12,000 serialized characters. Qwen3-4B dense supplies complete approved evidence
for 30/36 answerable development questions, or 83.3%, at a mean estimated input
of 2,572 tokens. BGE-M3 dense and BGE-M3 plus BGE reranking over 40 candidates each
reach 29/36 at about 2,532 tokens. TF-IDF reaches 26/36 even at 16,000 characters.
The application default remains four passages pending results review.

These are context evidence scores. Answer quality with more context, distractor
handling, factual correctness, abstention behavior and citation support remain
unmeasured. No answers were generated, no paid API calls occurred, and no held-out
searches ran. Approved datasets and labels, canonical documents, original XML and
canonical hashes are unchanged.

## Protocol and provenance

- Same 50 approved development questions, with 36 answerable and 14 negatives.
  Positive cohorts contain 14 exact-terminology, 13 paraphrase and nine
  cross-document questions. Seven missing-evidence and seven unrelated questions
  retain per-question token estimates but receive no positive evidence score.
- Same four licensed technical papers and 204 canonical paragraph/180-word
  passages. Dataset SHA-256 is
  `0bd3499a71d908b7482d55e87110115b428b0ede5a7803b0c9e86ba0d8feb5df`.
  Approved label canonical SHA-256 is
  `8e1b118b740f615c5985eda60936b796cf7abb8c2c302b7845ffbcaa93b1973f`.
  Corpus SHA-256 is
  `cda1b161618373b9c7b9701d3326fda4707f9501bbc3bf29c802d9a000908bce`;
  shared passage identity is
  `c7bf2f1f6b9c866573669f946866b5b0635ae4afcee1d06511e3109ab47c1157`.
- TF-IDF, Qwen3-4B dense and BGE-M3 dense replay the successful, stable limit-40
  rankings in `retrieval-improvements-2026-10-02`. TF-IDF can return fewer than 40
  positive-score hits. This is an actual lexical retrieval outcome, not a missing
  archive. No dense vectors or ranking scores were recomputed.
- BGE20 means `BAAI/bge-reranker-v2-m3` over 20 BGE-M3 dense candidates. Its archived
  limit-four baseline remains 26/36. Larger budgets use a separate 40-candidate
  configuration. The pinned Vulkan adapter scored all 2,000 development
  question/passage pairs locally on the RX 6800, with host cache disabled and the
  existing 511-token reject-overflow policy. All 50 rankings succeeded. The final
  scoring pass replays those complete 40-item rankings. Candidate depth changes
  are therefore explicit, rather than treating the 20-candidate baseline as a
  source of 40 reranked results.
- The existing `run_evaluation`, evidence span scorer and comparison report do
  all scoring. A manifest records the fixed budget grid and selection rule before
  scoring. Input archive paths, SHA-256 values, run IDs, artifact hashes, runtime
  settings and executable source hashes are retained. Runs identify PR #9 head
  `8b86909` plus the measured implementation's source hashes and dirty-code flag.
  Replay timings are not model latency measurements.

Full context selections, visible character ranges and group records remain under
`evaluation/runs/context-budget-reviewed-2026-10-13/`. The new local reranking
measurement is in `evaluation/runs/context-budget-2026-10-13/bge-m3-bge-rerank40/`.
The [result summary](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/context-budget-results.json),
kept under the archive tag, pins those full archives. It includes all 850
per-question token estimates across 17 configuration/budget combinations, cohort
counts, confidence intervals and paired comparisons.

## What the provider receives

`prepare_answer_context` now accepts `passages` or `characters`. The first retains
the existing selection of at most four passages. Character mode walks the ranked
results and stops before the next complete item would exceed its budget. Neither
mode enlarges the 3,000-character per-passage cap. Character mode does not skip a
higher-ranked item to fit a smaller later passage, or consult evidence labels.

The cap measures the serialized passage-item JSON list using the provider's
`json.dumps` defaults, including IDs, kind, keys, brackets, separators and ASCII
escaping. The question and instructions sit outside that passage-list cap and
are included in the token estimate. The exact question/passages input serializer
is shared between the provider and evaluator. Evidence scoring checks approved
span endpoints against the text actually visible after truncation, preserving OR
alternatives and AND combinations. Retrieval failures count as context misses.

This corrects the optimistic raw-text-only estimates in the task context. For
Qwen, 8k/12k/16k serialized budgets score 26/30/33 complete questions rather than
28/31/34. Serialized overhead reduces how far the ranked prefix fits. The ranking
itself is unchanged. The four-passage controls reproduce the prior 15/24/22/26
counts for TF-IDF, Qwen dense, BGE dense and BGE20.

## Complete evidence and token cost

All counts below use 36 answerable questions. Mean group coverage averages each
question's fraction of covered groups. "Asked" includes only IDs starting with
`part-`; it is a diagnostic scoring view and does not alter approved labels.

| Configuration | Budget | All groups complete | Asked groups complete | All-group coverage | Mean estimated input tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| TF-IDF | 4 passages | 15 | 17 | 55.2% | 826 |
| TF-IDF | 8k chars | 25 | 28 | 77.2% | 1,749 |
| TF-IDF | 12k chars | 26 | 29 | 78.6% | 2,535 |
| TF-IDF | 16k chars | 26 | 29 | 80.0% | 3,303 |
| Qwen3-4B dense | 4 passages | 24 | 27 | 78.3% | 879 |
| Qwen3-4B dense | 8k chars | 26 | 28 | 83.7% | 1,751 |
| Qwen3-4B dense | 12k chars | 30 | 31 | 89.8% | 2,572 |
| Qwen3-4B dense | 16k chars | 33 | 34 | 94.4% | 3,414 |
| BGE-M3 dense | 4 passages | 22 | 24 | 70.8% | 883 |
| BGE-M3 dense | 8k chars | 27 | 29 | 84.4% | 1,698 |
| BGE-M3 dense | 12k chars | 29 | 30 | 87.2% | 2,531 |
| BGE-M3 dense | 16k chars | 30 | 31 | 90.3% | 3,347 |
| BGE-M3 + BGE20 | 4 passages | 26 | 28 | 80.3% | 936 |
| BGE-M3 + BGE40 | 4 passages | 25 | 27 | 79.4% | 944 |
| BGE-M3 + BGE40 | 8k chars | 27 | 29 | 83.1% | 1,711 |
| BGE-M3 + BGE40 | 12k chars | 29 | 31 | 87.8% | 2,532 |
| BGE-M3 + BGE40 | 16k chars | 30 | 32 | 90.3% | 3,340 |

Token counts are offline `o200k_base` estimates of the exact input JSON plus
instructions. They exclude Responses framing, output schema and provider-internal
tokens. They are not billed usage or a verified tokenizer contract for the answer
model. No dollar cost is inferred. Per-question estimates, including negatives,
are in the archive. The table averages only the 36 answerable questions; Qwen12k
averages 2,606 over all 50 questions.

Qwen12k has a median of 2,588 estimated tokens and range 2,391-2,822. It supplies
14.9 passages and 11,472 serialized characters on average. Relative to four
passages, the mean input estimate rises by 1,693 tokens, or 2.93 times. Qwen16k
adds three complete questions over Qwen12k for another 842 mean tokens. It reaches
33/36, or 91.7%, with a mean 20.4 supplied passages.

## Cohorts

All-group complete counts; denominators are 14 exact, 13 paraphrase and nine
cross-document questions. Both negative cohorts contain seven cases at every
budget and have no complete-evidence score. The JSON includes their counts and
null relevance rates, rather than counting them as successes.

| Configuration | Budget | Exact | Paraphrase | Cross-document |
| --- | --- | ---: | ---: | ---: |
| TF-IDF | 4 / 8k / 12k / 16k | 11 / 13 / 13 / 13 | 3 / 6 / 6 / 6 | 1 / 6 / 7 / 7 |
| Qwen3-4B dense | 4 / 8k / 12k / 16k | 11 / 12 / 13 / 13 | 8 / 9 / 11 / 12 | 5 / 5 / 6 / 8 |
| BGE-M3 dense | 4 / 8k / 12k / 16k | 10 / 11 / 13 / 13 | 8 / 9 / 9 / 9 | 4 / 7 / 7 / 8 |
| BGE-M3 + BGE20 | 4 | 11 | 8 | 7 |
| BGE-M3 + BGE40 | 4 / 8k / 12k / 16k | 11 / 12 / 13 / 13 | 8 / 8 / 9 / 9 | 6 / 7 / 7 / 8 |

Qwen12k recovers `tech-glass-paraphrase`, `tech-compare-fusion`, `tech-amff-layers`,
`tech-adaptive-binarization`, `tech-moving-signal-addition` and
`tech-too-many-shortcuts`. It still misses all-group completeness for
`tech-wafer-exact`, `tech-both-checks-clean`, `tech-changing-neighborhood` and the
three localization/network comparison questions. At 16k, `tech-both-checks-clean`,
`tech-compare-network-inputs` and `tech-compare-network-roles` also become complete.
The localization comparison, changing-neighborhood question and wafer qualification
remain incomplete.

## Qualification view and owner decision

Eight questions contain groups excluded by the `part-` rule:

| Question | Excluded group IDs |
| --- | --- |
| `tech-wafer-exact` | `efficiency-scope` |
| `tech-wafer-paraphrase` | `cds-incomplete` |
| `tech-amff-layers` | `architecture-conflict` |
| `tech-aw-ssim-combination` | `component-calculations` |
| `tech-manual-outline-union` | `visibility-scope` |
| `tech-daylight-interference` | `containment-scope` |
| `tech-too-many-shortcuts` | `residual-purpose` |
| `tech-changing-neighborhood` | `gaussian-spread`, `fixed-footprint` |

Four questions change their complete-evidence outcome in at least one tested
context: wafer-exact, amff-layers, too-many-shortcuts and changing-neighborhood.
The other four excluded-group questions have identical completeness outcomes
across the tested contexts. Specific outcome differences are:

| Configuration | Budget | Becomes complete in asked-only view |
| --- | --- | --- |
| TF-IDF | 4 | wafer-exact, too-many-shortcuts |
| TF-IDF | 8k / 12k / 16k | wafer-exact, too-many-shortcuts, changing-neighborhood |
| Qwen dense | 4 | wafer-exact, amff-layers, too-many-shortcuts |
| Qwen dense | 8k | wafer-exact, too-many-shortcuts |
| Qwen dense | 12k / 16k | wafer-exact |
| BGE dense | 4 | amff-layers, too-many-shortcuts |
| BGE dense | 8k | wafer-exact, too-many-shortcuts |
| BGE dense | 12k / 16k | too-many-shortcuts |
| BGE20 | 4 | wafer-exact, too-many-shortcuts |
| BGE40 | every tested budget | wafer-exact, too-many-shortcuts |

These abbreviated names retain the `tech-` prefix in the approved dataset. Group
coverage can also change without changing completeness. In the asked-only view,
BGE dense and BGE40 reach 29/36 already at 8k. The official target and treatment of
qualifications remain the project owner's decision. This study keeps all groups
for selection and leaves the approved labels untouched.

## Project retrieval targets

The project's five initial retrieval targets were defined for the top four passages.
Here they are measured on the passages the provider actually receives. Recall,
evidence hit and MRR use the same definitions as the existing runner. The four-passage rows
reproduce its archived Qwen values: 69.3% reference recall, 32/36 hits and MRR 0.715.
Rank positions are the passage order within the supplied context. These values derive
from the recorded context selections in the full runs, not a separate retrieval.

| Configuration | Context | Reference recall (≥80%) | Evidence hit (≥90%) | Complete (≥80%) | Both sources /9 (≥90%) | MRR (≥0.65) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Qwen dense | 4 passages | 69.3% | 88.9% | 66.7% | 6 | 0.715 |
| Qwen dense | 12k chars | 85.2% | 97.2% | 83.3% | 9 | 0.725 |
| Qwen dense | 16k chars | 88.6% | 97.2% | 91.7% | 9 | 0.725 |
| BGE dense | 12k chars | 82.1% | 94.4% | 80.6% | 9 | 0.609 |
| BGE dense | 16k chars | 85.2% | 100.0% | 83.3% | 9 | 0.614 |
| BGE40 | 12k chars | 82.3% | 97.2% | 80.6% | 9 | 0.859 |

Qwen dense meets all five targets at 12k and 16k on this development set. BGE dense
misses only MRR; BGE40 meets all five at 12k but uses the evaluation-only Vulkan
reranker. The project owner accepted context-equivalent 12k/16k measurement as
sufficient for these targets. Held-out confirmation, answer quality and lower-memory
deployment remain separate work.

## Paired statistics and uncertainty

The scorer adds two-sided exact McNemar tests on paired complete-evidence outcomes,
with gain/loss discordances, and exact 95% Clopper-Pearson binomial intervals.
Negatives and unknown scores are excluded from the paired test. Every positive
pair here is measured; its denominator is 36.

| Comparison, all groups | Gains | Losses | Exact p |
| --- | ---: | ---: | ---: |
| Qwen4 to Qwen8k | 2 | 0 | 0.5000 |
| Qwen4 to Qwen12k | 6 | 0 | 0.03125 |
| Qwen4 to Qwen16k | 9 | 0 | 0.00390625 |
| Qwen4 to BGE20 at four passages | 3 | 1 | 0.6250 |
| Qwen12k to BGE dense12k | 3 | 4 | 1.0000 |
| Qwen12k to BGE40 at 12k | 2 | 3 | 1.0000 |
| BGE20 to BGE40 at four passages | 0 | 1 | 1.0000 |

All tested model/budget pairs and both scoring views are in the archive. These
development comparisons use unadjusted exploratory p-values. Qwen12k's nominal
p=0.03125 does not survive a correction for its three tested larger budgets.
Differences of 1-3 complete questions out of 36 are not significant at 5% under
the exact paired test. This set cannot establish a small model advantage.

| All-group context | Complete rate | 95% binomial CI |
| --- | ---: | ---: |
| Qwen4 | 24/36, 66.7% | 49.0%-81.4% |
| Qwen12k | 30/36, 83.3% | 67.2%-93.6% |
| Qwen16k | 33/36, 91.7% | 77.5%-98.3% |
| BGE dense12k / BGE40 at 12k | 29/36, 80.6% | 64.0%-91.8% |

Meeting the development count target does not establish an 80% population success
rate. These are curated development questions used for selection, not a frozen
held-out result. Evidence availability also does not establish answer quality.

## Development selection and application settings

[The development-selected configuration](development-selected-context-budget.json)
pre-registers Qwen dense with 40 retrieval candidates and a 12,000-character
serialized context, retaining the 3,000-character passage cap and all-group
target. It preserves the incumbent model; the one-question differences at 12k
do not justify a model-superiority claim. No held-out search has followed this
selection. The existing four-passage config and application default remain intact.

To opt into the measured context after review, use `ANSWER_CONTEXT_MODE=characters`,
`ANSWER_CONTEXT_CHARS=12000` and `ANSWER_CONTEXT_CANDIDATES=40`. The API then
retrieves the larger candidate ranking instead of silently retaining its default
four-hit search. An enabled application reranker must have at least that many
candidates. This setting does not install the evaluation-only Vulkan adapter into
the application.

Rendering omitted formulas as readable text is deferred to a separate PR. It changes
the canonical corpus and requires label remapping and owner approval.

## Reproduction and validation

The study driver (`researchlens.context_experiments`), the Vulkan reranking adapter
and the archive script are kept under the
[`research/retrieval-2026-10`](https://github.com/Timerk/ResearchLens/tree/research/retrieval-2026-10)
tag, together with reproduction instructions. They replay archived rankings and are
not part of the maintained code.

For direct runner use, `evaluation run --limit 40 --context-budgets 4 8000 12000
16000` adds the same profiles to a normal retrieval run. It rejects larger-context
profiling when fewer than 40 ranking candidates are configured. The token
estimator is part of the dev dependencies.

Tests cover default behavior, API candidate depth, serialized escaping/overhead
boundaries, ranked-prefix overflow, actual mock-provider input versus offline
profiles, visible-span truncation, qualification views, failed retrieval scoring
and exact statistics.
