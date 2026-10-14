# Held-out retrieval pre-registration

Registered on 2026-10-14, before any held-out search, on a new branch from
`origin/main` at `e57ffb2`, after PR #15. This document is immutable after its
registration commit. Questions, answers and claims were not inspected. Only
reference counts, source counts, abstention flags, query styles and dataset pins
were inspected. No dataset, label or corpus change is permitted.

## Frozen inputs and configurations

Use `evaluation/datasets/held-out.json`, version `4-readable-formulas-frozen`.
Its LF-normalized SHA-256 is
`920f1415d14d974ce489e91386227d3f306837f22944958763d8235495ea9312`.
The adopted corpus SHA-256 is
`f293a02c7afaf38f06ec17d6443f7289fd3a7d3091cf11cf0d4f865ee0e3a675`.
Use the adopted 207-passage tier artifacts, validated against this corpus.
Existing local artifacts may be copied into ignored `data/tiers/`.

| Configuration | Candidates | Answer context |
| --- | ---: | --- |
| TF-IDF baseline | 4 | Four passages, maximum 16,000 serialized characters |
| BGE-M3 dense | 40 | 16,000 serialized characters |
| Qwen3-4B dense | 40 | 12,000 serialized characters |
| Qwen3-4B dense | 40 | 16,000 serialized characters |

Freeze the encoding-v2 settings from development and PR #14 tiers. Dense models
use CPU Torch 2.14.1+cpu, bfloat16, no quantization, 512 tokens, right truncation,
batch size one, eight intra-op threads, one inter-op thread, passage text only,
L2 normalization and cosine ranking. BGE-M3 revision is
`5617a9f61b028005a4858fdac845db406aefb181`, CLS pooling, 1,024 dimensions,
empty query/document prefixes. Qwen revision is
`5cf2132abc99cad020ac570b19d031efec650f2b`, last-nonpadding-token pooling,
2,560 dimensions, empty document prefix and the existing research-question
instruction in `embedding_models.QUERY_INSTRUCTION`. No hybrid, reranker,
diversity, threshold tuning or automatic tier fallback. TF-IDF uses the existing
PassageIndex lexical settings and positive-score filtering.

Use `prepare_answer_context` unchanged, with a 3,000-character passage cap.
Character budgets measure the JSON passage-item list with default separators and
ASCII escaping. Stop before the first item that overflows. Do not skip items.
Retrieve each question once per backend, with no warmups or timing repeats.
Qwen's single 40-candidate ranking is shared by the two frozen context profiles;
profiling is deterministic serialization, not another search. No generation or
paid API calls. Run output directories must be new and must never be overwritten.

## Population and metric definitions

There are 36 cases, with 26 answerable cases and 10 expected-abstention cases.
Answerable cases have 54 distinct within-case passage references in total.
Their reference-count distribution is ten cases with one, nine with two, three
with three, three with four and one with five. Seven answerable cases reference
two documents. Positive query styles are ten exact, nine paraphrase and seven
cross-document cases.

All ten unanswerable cases are excluded from every quality metric and paired
test. Five have no references; five have related references that cannot establish
an answer. Empty reference sets never count as vacuous complete-evidence success.
Keep their retrieval and error records, but do not infer abstention quality.

| Target | Definition | Denominator |
| --- | --- | --- |
| Passage recall@4 >=80% | For each answerable case, distinct reference IDs in the first four ranked passages divided by distinct reference IDs; average those fractions | 26 cases, macro average |
| At least one valid evidence passage in context >=90% | At least one referenced passage ID with nonempty visible text in the serialized context | 26 cases |
| Complete evidence >=80% | Every distinct referenced passage ID has nonempty visible text in the serialized context | 26 cases |
| Both documents >=90% | Every expected document appears among supplied context passages, whether or not the passage is a reference | Seven cross-document cases |
| MRR@4 >=0.65 | Reciprocal rank of the first referenced ID in the first four ranked passages, or zero if absent; average | 26 cases |

These are passage-level proxies. Without span labels, ID presence cannot prove
that the needed text survives truncation, that a claim is supported or that all
qualifications are present. Complete evidence requires all references, with no
OR alternatives. Development completeness instead required all approved evidence
groups, including OR alternatives, AND fragments and visible span endpoints.
Development evidence hit and MRR used labeled evidence relevance. Its adopted
12k/16k report measured recall and reciprocal rank over the whole supplied
context, despite the original top-four targets. Therefore report strict recall@4
and MRR@4 as the literal targets, plus whole-context reference recall and MRR as
predeclared development-comparison diagnostics. Do not substitute those diagnostics
for literal target passes. Development-versus-held-out comparisons are approximate
where rank cutoffs or evidence definitions differ. Four-passage baselines have
matching cutoffs but still differ in labeled relevance.

## Statistics and decision rule

Pass/miss uses unrounded point estimates against the five thresholds, not an
interval bound. Report two-sided exact 95% Clopper-Pearson intervals for binary
context hit, complete evidence and both-document rates. Macro recall and MRR are
not binomial proportions, so Clopper-Pearson is inapplicable. For their uncertainty,
report distribution-free 95% Hoeffding intervals for means of bounded [0,1]
case scores: clip mean +/- sqrt(log(40)/(2*n)) to [0,1]. Also report a diagnostic
micro passage-recall count with Clopper-Pearson interval, explicitly noting that
within-question references are dependent and it is not the macro target.

For each dense configuration against TF-IDF, apply two-sided exact McNemar to
paired complete-evidence outcomes as the primary comparison, denominator 26.
Also report paired context-hit tests over 26 and both-document tests over seven.
List gains, losses and exact p-values, without model-superiority claims. These
nine planned tests are unadjusted; give Holm-adjusted p-values across all nine.
Do not apply McNemar to fractional recall or reciprocal rank.

Technical retrieval failures remain zero scores. If execution crashes or records
technical errors, preserve the failed outputs, fix only the technical cause,
commit the fix before retrying and document the affected configuration and attempt.
Only the same frozen configuration may be retried. No label inspection for tuning,
settings changes, dataset edits, model selection or additional held-out searches.

## Execution and reporting

Before retrieval, commit any general runner/scorer changes and pass Ruff and
tests using synthetic cases. The existing runner validates frozen held-out status,
corpus references and split separation. Extend passage-reference scoring without
creating held-out span labels or changing development group scoring. Record code
commit, source hashes, dataset/corpus hashes, artifact hashes, installed versions,
execution settings and failures in ignored `evaluation/runs/`.

Commit `docs/held-out-results.md`, a summary JSON and a one-line README statement.
Include all configurations, metrics, denominators, intervals, target passes/misses,
paired statistics and the adopted development comparison. Report every miss
without proposing a post-hoc fix. Open a PR with this registration commit visibly
preceding runner and results commits. Do not merge.
