# Generated answer quality

## Current decision, 2026-10-15

Keep the current application defaults. The no-tier default remains TF-IDF with
four passages. Explicit hardware tiers retain their existing character budgets;
this study does not make those budgets the universal application policy.

The owner completed grading before calibration. The revision was committed,
then its prompt, rubric, `gpt-6-luna` model ID, schema and checks were
[frozen](../evaluation/reviews/2026-10-14-answer-judge/frozen-judge.json) with the
[decision rule](../evaluation/reviews/2026-10-14-answer-judge/context-decision-rule.json).
Only after that commit was the sealed validation CSV opened and its SHA-256
verified against `owner-review.md`. Validation was evaluated once. No judge
revision or paid retry followed it.

| Judgment type | Archived calibration accuracy / kappa | Frozen validation accuracy / kappa | Decision use |
| --- | --- | --- | --- |
| Required claim | 100% / 1.0 | 100% / 1.0 | Included |
| Qualification | 33.3% / 0.0 | 50% / 0.0 | Excluded |
| Forbidden claim | 100% / undefined | 100% / undefined | Excluded |
| Abstention | 100% / 1.0 | 100% / 1.0 | Included |
| Citation | 33.3% / 0.0 | 100% / undefined | Excluded |

Each half has six items per type. The validation qualification stratum contains
one UNCERTAIN owner verdict. It receives no accuracy credit and is excluded from
binary kappa, leaving 3/5 agreement among decidable pairs. The two old calibration
unknown citation receipts also receive no accuracy credit. Revised calibration
agreement is 100% for all types, but qualification/citation/forbidden kappas are
undefined there because both raters assign only PASS. Citation and forbidden
validation kappas are likewise undefined, so neither meets the requested
kappa >= 0.6 AND agreement >= 80% bar. No claim of violation-detection reliability
follows from their perfect observed agreement.

The owner and Codex graded independently and reported 58/60, 96.7%, agreement
before adjudication. The owner adopted
Codex's verdicts in the two disagreements; their original grades and IDs were
not retained. Final grades may favor a model from the same family. Small-sample
100% figures against those grades do not remove that limitation.
Full baseline and frozen metrics, confusion counts and exclusions are in
the [calibration](../evaluation/reviews/2026-10-14-answer-judge/calibration-baseline.json)
and [one-time validation](../evaluation/reviews/2026-10-14-answer-judge/validation-results.json)
records.

All 250 requested current-corpus development evaluations completed without
provider/scoring errors: 249 generation calls and 155 frozen-judge calls.
The approved PR #15 development rankings were validated against today's
readable-formula corpus, dataset and labels; no retrieval was repeated.

| Configuration | Complete required claims /36 | False abstentions /36 | Correct generated negative abstentions /14 |
| --- | --- | --- | --- |
| TF-IDF, four passages | 19 | 14 | 13 |
| Qwen3-4B, four passages | 26 | 7 | 14 |
| Qwen3-4B, 12k characters | 27 | 3 | 14 |
| Qwen3-4B, 16k characters | 32 | 1 | 14 |
| BGE-M3, 16k characters | 32 | 0 | 14 |

The registered primary comparison is Qwen 12k versus Qwen four, which holds
retrieval fixed and tests the existing full tier's budget. It has four gains and
three losses across all 36 answerable pairs, with two-sided exact McNemar p=1.0.
It fails the p < 0.05 improvement condition. Negative abstention remains 14/14.
The unsupported-claim and forbidden-claim guards are unassessable because their
judgment types did not pass validation. Excluding them does not satisfy those
AND conditions. Qualifications and the composite do not enter the decision.

Qwen 16k versus four has six gains, zero losses and nominal p=0.03125. It is a
descriptive secondary comparison, not a replacement for the registered primary;
its safety endpoints are also uncertified. The
[applied decision](../evaluation/reviews/2026-10-14-answer-judge/context-decision.json)
therefore retains the defaults. The
[current results](https://github.com/Timerk/ResearchLens/blob/archive/evaluation-2026-10/docs/answer-quality-current-results.json) (archived) preserve reliable paired
metrics and separate uncertified diagnostics. Do not interpret changes from the
old study as a causal estimate of formula rendering: corpus, judge and generated
responses differ.

`answer-plan` ran before each paid stage. The current-corpus run's conservative
reservation was $2.9711926. All Phase 2 calls share a persistent $3 ledger,
with reservation before each request and reconciliation only from reported usage.
All 449 calls have known usage; total cost at the supplied uncached rates is
$0.2469009, including calibration and validation. This is not an independently
verified billing total. There was no held-out generation or retrieval, and no
dataset, label or corpus edit. Raw receipts remain in local ignored storage;
the [evidence manifest](../evaluation/reviews/2026-10-14-answer-judge/phase2-evidence-manifest.json)
pins the bundle, plan, ledger and review predictions.

The guarded commands now also accept `--bge-run` with `bge16k` and
`--review-archive`/`--review-half` for judging saved answers without generation.
Paid runs use `--max-cost-usd 3 --study-ledger PATH`. Optional `--jobs 4` runs
disjoint cases, checks their unique complete coverage, and shares that ledger.
Resume reuses checkpoints and refuses unresolved or repeated paid calls.
Parallel resume verifies the saved plan, cost cap, ledger path and worker layout
before writing files or starting workers. The execution record is saved before
the first worker starts. Older runs without that record remain readable for
offline reporting; the CLI refuses to resume them.
The frozen contract is verified before validation and current-corpus planning.

## Historical study, 2026-10-13

The remaining sections preserve the original experiment and its recommendation.
Its counts use the original judge and corpus, not the calibrated results above.

The 2026-10-13 results and evidence manifest below describe the pre-rendering corpus.
Readable formulas and evidence migrations were approved and adopted on 2026-10-14.
Their [development retrieval rerun](formula-adoption-results.md) does not update
these paid answer-quality measurements. The original answer-quality corpus, label,
run and review hashes remain unchanged; no paid rerun was performed during adoption.

## Recommendation

Keep the application default at four passages. Qwen at 12k improves complete
required-claim coverage from 25/36 to 28/36, but the paired gain is uncertain.
At 16k it reaches 32/36, with only exploratory nominal significance. Citation
support still has failures, and the qualification judge disagrees substantially
with the independent audit. Neither larger context has a sufficiently reliable
overall quality result to justify changing the default.

The owner approved a $2.30 hard cap on 2026-10-13. All 200 development
question/configuration evaluations completed, using 199 generation calls and
122 judge calls. Recorded token usage costs $0.1471 at the supplied rates.
There were no paid retries. The four-passage application settings are unchanged.

The [machine-readable results](answer-quality-results.json) contain all six
paired comparisons and every cohort/metric. The
[evidence manifest](../evaluation/answer-quality-evidence-manifest.json) records
checksums for the saved runs, raw-judgment bundle and independent reviews. Raw
records stay in ignored `evaluation/runs/answer-quality-2026-10-13/` storage;
they are not included in a fresh source checkout. The
[spot-check notes](../evaluation/answer-spot-check-notes.json) retain the audit
decisions and evidence notes. The [approved plan](../evaluation/answer-plan.json)
pins the inputs and estimates.

## Scope and controlled comparison

The study uses all 50 approved technical development questions, comprising 36
answerable questions and 14 negatives. The negative cohorts contain seven
unrelated and seven missing-evidence questions. The answer commands never load
the held-out dataset. Approved datasets, evidence labels and canonical corpus
remain unchanged. Formula rendering is a separate change.

Four configurations use the same generation provider and prompt:

| Configuration | Retrieval candidates | Provider context |
| --- | ---: | --- |
| TF-IDF | 40 | First four passages |
| Qwen3-4B dense | 40 | First four passages |
| Qwen3-4B dense | 40 | 12,000 serialized characters |
| Qwen3-4B dense | 40 | 16,000 serialized characters |

Generation calls the actual `OpenAIProvider.answer`, including its structured
output validation, instructions, medium reasoning, 2,000-token output limit and
zero retries. Context selection uses `prepare_answer_context`, preserving the
3,000-character passage cap and ranked-prefix behavior. The default evaluation
configuration is TF-IDF with four passages, the least expensive baseline.

For the completed study, the input rankings were the archived
`context-budget-reviewed-2026-10-13` TF-IDF and Qwen dense runs used in
[the context study](context-budget.md). Replaying those recorded canonical hits
holds retrieval fixed while measuring generation. The plan records their full
hashes, encoding revision and shared passage identity. A fresh ranking can also
be produced with the same runner. Different ranking files require a new plan and
approval, even when the passage selections are identical.

## Scoring

Per case, the runner records a decision for each required claim, qualification
and forbidden claim. It reports claim coverage and qualification preservation as
fractions, plus binary all-claims, all-qualifications and no-forbidden-claims
outcomes. The composite answer-correct outcome requires the appropriate answer
or abstention status, all required content, no forbidden assertions, valid IDs
and supported citations. Negative qualifications describe why the question is
unanswerable. They do not require prose from the provider's section-free
abstention format.

Citation ID membership is deterministic. Exact extracted section text can be
checked directly against the cited visible passage. Other semantic support
decisions use the judge. Every citation must support at least part of its
section, and the citation set must support every part. Approved evidence spans
and their OR/AND alternatives are supplied to the judge. Their offsets refer to
the canonical text; the judge sees only the text actually supplied to generation.
A supported semantic judgment must include verbatim evidence quotes which the
runner checks against that visible text. Topic overlap and a valid ID alone do
not establish support. Evidence labels are not assumed to enumerate every valid
additional claim.

Empty generated abstentions and missing claims are scored locally. No-match,
provider error and malformed output do not count as generated abstentions.
For the 14 negatives, only `insufficient_evidence` with no sections earns a
correct abstention. False abstentions on answerable cases fail answer correctness.
Unknown semantic decisions remain null and are never credited as successes.

The judge uses pinned `gpt-6-luna`, medium reasoning, a versioned prompt constant
and a 4,000-token cap. The plan pins both prompts and output schema hashes. Each
raw Responses judgment, token usage, reasons and quoted evidence is saved before
scoring. The runner stops on the first provider or judge error and preserves the
generation checkpoint. Explicit `--resume` continues the exact same plan and cap
from its saved ledger without repeating paid calls. Completed saved judgments
can be rescored locally. Multiple subclaim decisions for one citation are combined
conservatively; missing or unexpected citations still fail validation.

## Judge reliability

The [Phase 1 owner grading packet](../evaluation/reviews/2026-10-14-answer-judge/owner-grading.md)
contains 60 blind, individual judgment items from the archived development
outputs. It splits questions between 30 calibration and 30 validation items,
with all five judgment types and all four configurations in each half.
The owner completed grading, recorded in
[owner-review.md](../evaluation/reviews/2026-10-14-answer-judge/owner-review.md).
The packet remains pristine; the separate key and diagnosis reveal model outcomes.
Calibration, freeze and one-time validation are reported above. The archive has no predicted forbidden
violations or invalid citation IDs, so those failure strata cannot be supplied.

Each completed configuration produces `spot-check.json` with two preselected
cases per cohort, ten cases total. Sampling uses a stable case-ID hash and does
not depend on judge outcomes. An independent reviewer scores the saved answers
against the approved claims and visible evidence, records evidence notes, and
then compares those scores with the judge using `answer-reliability`.

The reliability output reports agreement counts and exact 95% binomial intervals
for each metric, with semantic judge decisions separated from deterministic
status and ID checks. Report the reviewer identity, disagreements and unresolved
cases with the final study. Agreement on this small stratified development sample
is a diagnostic, not proof that the judge is reliable on future questions.

Codex GPT-6.1-Sol audited 40 saved responses, using the same ten preselected
questions across the four configurations. This is an independent model audit,
not a human review. The audit read answer sections, cited visible passages and
approved requirements before inspecting the corresponding judge scores. Its
qualification criterion accepts correctly scoped claims without requiring
verbatim caveat wording. Judge-only agreement excludes deterministic abstentions
and ID checks:

| Configuration | Required claims | Qualifications | Citation support | Composite |
| --- | ---: | ---: | ---: | ---: |
| TF-IDF, four passages | 3/3 | 1/3 | 3/3 | 2/3 |
| Qwen, four passages | 3/3 | 1/3 | 3/3 | 1/3 |
| Qwen, 12k characters | 6/6 | 1/6 | 6/6 | 1/6 |
| Qwen, 16k characters | 6/6 | 1/6 | 5/5, one unresolved | 1/6 |

The 18 judged sampled answers give 18/18 agreement on required-claim completion
and only 4/18 on qualifications. These are repeated configurations of ten
questions, not 40 independent questions. Per-configuration exact intervals are
in the JSON; even 6/6 agreement has a 95% lower bound of 54.1%.

The disagreement concerns the rubric as well as the judge. For example, answers
that say the classifiers were pretrained on ImageNet do not claim new study-wide
ImageNet training, but the judge often demands an explicit disclaimer. It also
rejects an explicitly "Ideally" qualified SNR relation for not separately saying
it is not guaranteed under every noise condition. All nine cross-document
questions fail the judge's qualification metric at every context size.

Keep those raw scores and audit disagreements visible. The audit does not replace
the full-run judge scores or approve the datasets again. Resolve the qualification
criterion with the owner and independently adjudicate disputed cases before
using the composite metric to promote a default.

## Results

Claim and qualification fractions are per-question means over the 36 answerable
cases. Completion requires every requirement for that question. The composite
includes the 14 negatives and the disputed qualification judgments, so it is
reported as a judge diagnostic rather than a calibrated correctness rate.

| Measure | TF-IDF, four | Qwen, four | Qwen, 12k | Qwen, 16k |
| --- | ---: | ---: | ---: | ---: |
| Complete required claims /36 | 15 | 25 | 28 | 32 |
| Mean required-claim coverage | 43.1% | 70.8% | 79.2% | 88.9% |
| All qualifications preserved, judge /36 | 8 | 8 | 10 | 8 |
| Mean qualification preservation, judge | 23.6% | 23.6% | 27.8% | 25.0% |
| Forbidden-claim violations /50 | 0 | 0 | 0 | 0 |
| Citation IDs valid /answered | 22/22 | 29/29 | 35/35 | 36/36 |
| All citations supported /answered | 18/22 | 25/29 | 30/35 | 31/36 |
| Unresolved citation-support cases | 0 | 0 | 1 | 1 |
| False abstentions /36 | 14 | 7 | 1 | 0 |
| Generated abstention correct /14 | 13 | 14 | 14 | 14 |
| Judge composite correct /50 | 19 | 20 | 21 | 20 |

Citation-support denominators above include all answered cases; unresolved cases
receive no credit. Machine-readable rates and paired tests exclude unresolved
decisions and report their counts. The unresolved cases are
`tech-compare-training-computers` at 12k and `tech-moving-signal-addition` at 16k.
Their judge-supplied evidence quotes fail the exact visible-text check. The
independent audit supports the sampled 16k moving-signal answer, while the runner
retains its conservative unresolved citation score.

Each configuration has four answered cases with unsupported citations. This
includes irrelevant extra citations, even when another citation supports the
claim. Larger contexts reduce false abstentions and increase the number of
supported answers, but do not eliminate citation distractors. Zero forbidden
assertions and correct generated abstentions on the negative cohorts provide
some evidence of distractor resistance on these development questions.

TF-IDF's seventh unrelated case returned `no_matches` safely, with no API call;
it is counted separately from generated abstentions. There are no remaining
provider or scoring errors. One duplicate citation/subclaim judgment was
rescored locally after a checkpointed stop. Replaying all saved judgments through
the final scorer reproduces all 200 score records exactly.

## Cohorts

Complete required-claim counts:

| Cohort | TF-IDF, four | Qwen, four | Qwen, 12k | Qwen, 16k |
| --- | ---: | ---: | ---: | ---: |
| Exact terminology /14 | 12 | 13 | 12 | 14 |
| Paraphrase /13 | 3 | 8 | 9 | 9 |
| Cross-document /9 | 0 | 4 | 7 | 9 |

All-qualification counts under the judge's strict interpretation:

| Cohort | TF-IDF, four | Qwen, four | Qwen, 12k | Qwen, 16k |
| --- | ---: | ---: | ---: | ---: |
| Exact terminology /14 | 7 | 5 | 7 | 6 |
| Paraphrase /13 | 1 | 3 | 3 | 2 |
| Cross-document /9 | 0 | 0 | 0 | 0 |

For unrelated negatives, generated abstention is 6/7 for TF-IDF plus one safe
no-match, and 7/7 for each Qwen context. Missing-evidence negatives are 7/7 for
every configuration. Required-claim and qualification relevance scores are
not applicable to negatives. The JSON contains citation, forbidden-claim,
composite and paired results for every cohort as well.

## Cost estimate and approval

The owner supplied GPT-6 Luna prices on 2026-10-13: $0.10 per million input
tokens and $0.50 per million output tokens. The same model judges the answers.
The dated price file records this provenance; the prices were not independently
verified. No cache discount is assumed.

| Configuration | Generation estimate | Judge estimate | Conservative reservation |
| --- | ---: | ---: | ---: |
| TF-IDF, four passages | $0.053 | $0.114 | $0.510 |
| Qwen, four passages | $0.054 | $0.117 | $0.524 |
| Qwen, 12k characters | $0.063 | $0.125 | $0.607 |
| Qwen, 16k characters | $0.067 | $0.129 | $0.647 |
| Total | $0.237 | $0.485 | $2.288 |

The approximate total is $0.72 for 199 generation calls and at most 199 judge
calls. One TF-IDF question has no retrieved passages and makes no paid call.
Judge estimates allow up to 2,000 answer tokens in their input and maximum output
for every possible judge call. Abstentions avoid judging and reduce actual cost.

The reservation uses UTF-8 byte bounds, JSON escaping allowance and an 8,192-token
schema/framing allowance per call. It also reserves the full output caps,
including reasoning tokens. Offline `o200k_base` token estimates are estimates,
not billed usage or a verified model tokenizer contract. Recorded API usage
provides the eventual measured token cost.

`answer-plan` prints generation and judge estimates and exits without creating a
paid client. `answer-run` requires the matching approval hash and a finite,
positive `--max-cost-usd`. It rejects a plan exceeding that cap before client
construction and reserves cost before each call. Failed calls still consume
their reservation. A persistent cost ledger records reservations before network
requests. The owner approved this plan with a $2.30 cap.

Recorded usage after completion:

| Configuration | Mean generation input tokens /question | Generation cost | Judge cost | Total |
| --- | ---: | ---: | ---: | ---: |
| TF-IDF, four passages | 900 | $0.00699 | $0.01407 | $0.02106 |
| Qwen, four passages | 987 | $0.00841 | $0.01769 | $0.02611 |
| Qwen, 12k characters | 2,731 | $0.01692 | $0.02933 | $0.04625 |
| Qwen, 16k characters | 3,565 | $0.02099 | $0.03273 | $0.05371 |
| Total | | $0.05331 | $0.09382 | $0.14713 |

These are uncached-rate costs from API token usage, not a verified billing total.
All usage is known. TF-IDF's mean includes its zero-call question. The measured
generation input includes provider framing/schema overhead, unlike the offline
context-study estimate. The reservation ledger finished at $1.05083, below the
approved cap. No API requests were repeated when resuming the checkpoint.

## Paired statistics and cohorts

`answer-report` reuses the existing runner's dataset, corpus and scoring-contract
comparison checks. It requires complete 50-question development runs from one
approved plan. It reports all six configuration pairs, both overall and by exact
terminology, paraphrase, cross-document, unrelated and missing-evidence cohort.

Binary metrics use two-sided exact McNemar tests, including gain/loss
discordances and excluded unknown pairs. Rates include exact 95% Clopper-Pearson
intervals. Fractional coverage measures report mean paired differences and
paired percentile bootstrap intervals from 10,000 samples with seed 20261013.
P-values are exploratory and unadjusted for multiple comparisons. Small curated
development cohorts cannot establish a population advantage or substitute for
held-out confirmation. Report unknowns and errors alongside any claimed gains.

Complete required-claim outcomes, paired over the 36 answerable questions:

| Comparison | Gains | Losses | Exact p |
| --- | ---: | ---: | ---: |
| TF-IDF four to Qwen four | 10 | 0 | 0.001953 |
| TF-IDF four to Qwen 12k | 14 | 1 | 0.000977 |
| TF-IDF four to Qwen 16k | 17 | 0 | 0.0000153 |
| Qwen four to Qwen 12k | 6 | 3 | 0.507813 |
| Qwen four to Qwen 16k | 8 | 1 | 0.039063 |
| Qwen 12k to Qwen 16k | 5 | 1 | 0.218750 |

The 16k-versus-four nominal p=0.039 does not survive correction for even the two
larger Qwen contexts, or the six claim-completion comparisons. The raw composite
has no significant gain in any pair; every Qwen-to-Qwen composite comparison has
p=1. Its poor qualification agreement prevents a stronger interpretation.
Citation-support comparisons likewise all have p=1 on their shared scored
answered cases. Different answer/abstention rates make those citation denominators
smaller than 36; inspect paired counts in the JSON.

The mean per-question required-claim coverage changes are:

| Comparison | Mean paired change | Paired bootstrap 95% interval |
| --- | ---: | ---: |
| Qwen four to Qwen 12k | +8.3 percentage points | -6.9 to +23.6 |
| Qwen four to Qwen 16k | +18.1 percentage points | +4.2 to +33.3 |
| Qwen 12k to Qwen 16k | +9.7 percentage points | -1.4 to +22.2 |

The Qwen16k complete-claim rate is 88.9%, with an exact 95% interval of
73.9%-96.9%. Qwen12k's 77.8% has an interval of 60.8%-89.9%. These intervals
describe this development experiment's uncertainty; the questions were used for
retrieval selection and are not a frozen held-out result.

## Reproduction and validation

All commands are part of `python -m researchlens.evaluation`, with `PYTHONPATH=backend`.
Prepare canonical lexical and pinned Qwen embedding indexes using the existing
ingestion workflow. To create free rankings without loading another split:

```text
evaluation answer-rank --index data/index.json --retriever tfidf --output tfidf-ranking.json
evaluation answer-rank --index PATH_TO_QWEN_INDEX --retriever embeddings --output qwen-ranking.json
```

Use archived ranking files instead for an exact replay of the context study.
Compute a plan before any paid run:

```text
evaluation answer-plan --index data/index.json --tfidf-run tfidf-ranking.json --qwen-run qwen-ranking.json --prices evaluation/answer-prices.json --configurations tfidf4 qwen4 qwen12k qwen16k --output plan.json
```

After the owner approves the printed estimate and hash, use the same arguments
with `answer-run`, a new output directory, `--approve-plan-sha256 HASH` and
`--max-cost-usd 2.30`. An optional `--env-file` reads existing credentials without
copying or recording them. The paid commands pin their model independently of
the application environment.

```text
evaluation answer-report OUTPUT/tfidf4/run.json OUTPUT/qwen4/run.json OUTPUT/qwen12k/run.json OUTPUT/qwen16k/run.json --output paired-quality.json
evaluation answer-reliability --run OUTPUT/qwen12k/run.json --review OUTPUT/qwen12k/spot-check.json --output reliability.json
```

Pass `--reviews` with one completed spot-check file per run, in run order, to add
reliability estimates to the report. Use
`--archive evaluation/runs/answer-quality-2026-10-13/evidence.json.gz` to package
full runs, raw receipts, reviews and prompts in ignored storage. Commit compact
summary statistics, audit notes and checksum manifests. Keep raw bundles out of
source control.

All reporting, archiving and saved-judgment replay are offline. The local bundle
can be read with `json.loads(gzip.decompress(Path(path).read_bytes()))`. Verify its
file SHA-256 against `archive.sha256` in the manifest. Structured report, run and
review hashes use `researchlens.artifacts.canonical_hash`, so JSON formatting does
not affect verification. The checked-in report uses one statistical record per
line for review; its contents match the full report in the saved bundle.

Tests cover abstention semantics, citation membership versus support, fabricated
quotes, incomplete judgments, duplicate citation subclaims, unresolved scores,
cost reservations, rejected provider references, and resume without repeated
paid calls. Final Ruff lint/format and all backend tests pass. The application
configuration remains unchanged.
