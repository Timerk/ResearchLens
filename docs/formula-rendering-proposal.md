# Readable MathML, approved and adopted

The project owner reviewed [the span and reference migration](formula-remapping-review.md)
and approved it on 2026-10-14. The reason is "source text change from formula rendering".
`mathml-readable-v2` is now the canonical extraction. The
[approval record](../evaluation/reviews/2026-10-14-pr15/approval.json) records previous,
candidate and adopted hashes, all development groups and the 11 held-out reference changes.

Phase 1 started at main `d001d2b` and imported only the requested formula paths from
`b9fa7c5`. Its commit `e6237c2` is preserved as `b398004` after the requested rebase
on main `051381c`, which includes PRs #14 and #16. Phase 2 adds adoption commits.
The PR is not merged.

## Canonical extraction

The renderer restores 122 formulas and retains four unsupported `mmultiscripts`
formulas as `[formula omitted]`. It preserves `σ`, `k`, scripts and grouped fractions
without computing an expression or inserting a numeric parameter value. Invalid
operand counts, mixed content and unsupported structures trigger whole-formula fallback.

Overbars and limits use `over(base; annotation)` and `under(base; annotation)`
instead of exponentiation. Fence separators and mathematical font variants remain
explicit. `backend/researchlens/mathml.py` contains the unchanged approved renderer;
the canonical corpus extractor calls it. Original XML, licensing, paragraph selection,
source versions, sections and XML locators are unchanged.

| Article | Rendered formulas | Still omitted | Changed paragraphs |
| --- | ---: | ---: | ---: |
| Canopy, PMC11510794 | 20 | 0 | 5 |
| Heater, PMC11768589 | 0 | 0 | 0 |
| Wafer, PMC10934137 | 22 | 0 | 7 |
| Autoencoder, PMC11121878 | 80 | 4 | 22 |
| Total | 122 | 4 | 34 |

The adopted corpus hash is
`f293a02c7afaf38f06ec17d6443f7289fd3a7d3091cf11cf0d4f865ee0e3a675`.
The reviewed candidate hash was
`fe1c769f0ab662ac36cafd55982dbcc19c390b53f81fedff7852cc02aae23d26`.
Only attribution wording changed between candidate and canonical corpus, to record
owner approval instead of proposal status. All rendered document text is identical.
The manifest, corpus notices, active dataset pins, labels and retrieval selection
pins now describe the adopted extraction. Historical reviews keep their original hashes.

## Approved development spans

All 165 original occurrences map by exact paragraph alignment. Complete formula
placeholders are replaced in source order; all surrounding prose must match exactly.
No fuzzy matching or semantic relabeling was used.

| Classification of original occurrences | Count |
| --- | ---: |
| Unchanged quote, passage ID and offsets | 132 |
| Shifted only, quote preserved | 14 |
| Quote text changed | 19 |
| Cannot map | 0 |

The approved labels retain 36 cases, 92 groups and 140 alternatives. Two original
spans split into required AND fragments, giving 167 current span fragments. These
are `training samples.` in `tech-autoencoder-exact` and the fixed 11 × 11 footprint
sentence in `tech-changing-neighborhood`. No group, description, claim index or OR
alternative was removed. All current quotes validate against canonical passages.

`evaluation/labels/technical-development.json` records approval by the project owner
on 2026-10-14 and pins development version `5-readable-formulas-approved`. The
previous labels and dataset are archived byte-for-byte in
`evaluation/reviews/2026-10-14-pr15/`. Earlier question approvals remain unchanged.

## Held-out migration and freeze

Held-out has passage references only. The 62 previous reference occurrences classify
as 51 unchanged, seven text changes and four ID changes. None is unmappable. All
retain the same source, paragraph, section and XML locator. The four ID changes
split old-window coverage across two candidate windows, giving 66 current references.

The active `evaluation/datasets/held-out.json` is version
`4-readable-formulas-frozen`. The previous `3-human-reviewed-frozen` file remains
byte-for-byte in `evaluation/reviews/2026-10-14-pr15/datasets/held-out.json`.
Only the corpus pin, version/notes and reviewed reference mapping changed. All
question, answer, claim and other case content is preserved as opaque data.
The migration derives from the corpus change, not held-out model results. No held-out
retrieval or answer inspection ran, and no held-out span labels were created.

## Adopted development retrieval

All four hardware tiers were rebuilt against the new canonical corpus with fresh
vectors. TF-IDF, BGE-M3 dense and Qwen3-4B dense ran through the existing evaluator
at 40 candidates and `--context-budgets 4 12000 16000`. Runs use one attempt and
no warmup; no latency comparison is claimed. No generation or paid API calls ran.

| Model | Complete at four passages /36 | Complete at 12k /36 | Complete at 16k /36 |
| --- | ---: | ---: | ---: |
| TF-IDF | 15 | 26 | 26 |
| BGE-M3 dense | 21 | 28 | 30 |
| Qwen3-4B dense | 24 | 29 | 33 |

Qwen meets all five targets at 12k and 16k, with MRR 0.741. BGE meets three targets
at 12k and four at 16k. Every adopted total reproduces the reviewed phase-1
candidate total. `tech-changing-neighborhood` remains incomplete at every budget.
TF-IDF has 80% group coverage but misses the split fixed-footprint evidence.

[Current results](formula-adoption-results.md) and their
[JSON summary](formula-adoption-results.json) include all five targets, per-question
scores, tier validation and run hashes. [Phase-1 intervention results](formula-rendering-results.md)
remain as historical evidence; all paired exact McNemar p-values were 1.0.
The PR #16 paid answer-quality study also retains its original pre-rendering pins.
No new generated-answer or held-out quality claim follows from these retrieval runs.

## Reproduction

With locked dependencies and pinned model weights cached, run from `backend`:

```sh
rtk proxy python -m researchlens.corpus
rtk proxy python -m researchlens.formula_experiments --adopted --output ../evaluation/runs/readable-formulas-adopted-fresh
rtk proxy python -m researchlens.formula_report --adopted --output ../evaluation/runs/readable-formulas-adopted-fresh
```

The driver rebuilds `data/tiers/full.json`, `standard.json`, `light.json` and
`minimal.json`, validates each artifact and runs development retrieval only.
Large indexes, logs and full rankings stay ignored. The corpus and labels are
canonical tracked files; only summaries of evaluation runs are committed.
`researchlens.formula_adoption` records the one-time approved migration and refuses
to overwrite its approval archive.

Backend tests verify offline corpus reproducibility, exact label validation,
historical review hashes, both required split spans, preserved held-out content
and the 11 approved reference changes. Owner approval and adoption are complete.
