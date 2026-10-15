# Readable formulas: adoption and retrieval, 2026-10-14

This is the summary of the formula rendering study. The proposal, the reviewed span
remapping, phase-1 results and the migration tooling are archived in the
[`archive/evaluation-2026-10`](https://github.com/Timerk/ResearchLens/tree/archive/evaluation-2026-10)
tag: [proposal](https://github.com/Timerk/ResearchLens/blob/archive/evaluation-2026-10/docs/formula-rendering-proposal.md),
[remapping review](https://github.com/Timerk/ResearchLens/blob/archive/evaluation-2026-10/docs/formula-remapping-review.md) and
[phase-1 results](https://github.com/Timerk/ResearchLens/blob/archive/evaluation-2026-10/docs/formula-rendering-results.md).

## Canonical extraction

The renderer restores 122 formulas and retains four unsupported `mmultiscripts`
formulas as `[formula omitted]`. It preserves `σ`, `k`, scripts and grouped fractions
without computing an expression or inserting a numeric parameter value. Invalid
operand counts, mixed content and unsupported structures trigger whole-formula fallback.
`backend/researchlens/mathml.py` contains the approved renderer; the canonical corpus
extractor calls it. Original XML, licensing, paragraph selection, source versions,
sections and XML locators are unchanged.

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

## Owner approval and migration

The project owner reviewed the span and reference migration and approved it on
2026-10-14. The reason is "source text change from formula rendering". The
[approval record](../evaluation/reviews/2026-10-14-pr15/approval.json) records previous,
candidate and adopted hashes, all development groups and the 11 held-out reference changes.

All 165 original development span occurrences map by exact paragraph alignment: 132
unchanged, 14 shifted only and 19 with changed quote text. None is unmappable. The
approved labels retain 36 cases, 92 groups and 140 alternatives. Two original spans
split into required AND fragments, giving 167 current span fragments.

Held-out has passage references only. Its 62 previous reference occurrences classify
as 51 unchanged, seven text changes and four ID changes, giving 66 current references.
Only the corpus pin, version/notes and reviewed reference mapping changed. No held-out
retrieval or answer inspection ran, and no held-out span labels were created.

## Development retrieval on the adopted corpus

The owner approved and adopted the corpus, development spans and held-out reference migration on 2026-10-14. All four application tier indexes were rebuilt with fresh vectors against this corpus. TF-IDF, BGE-M3 dense and Qwen3-4B dense ran on all 50 development questions through the existing runner at 40 candidates and `--context-budgets 4 12000 16000`. The 14 negatives are unscored. No held-out retrieval, answer generation or paid API call ran.

Five thresholds: mean reference-ID recall ≥80%, evidence hit ≥90%, all-group complete evidence ≥80%, both sources ≥90% of nine cross-document questions, and MRR ≥0.65. Complete evidence uses visible quote spans, including every required AND fragment. Reference recall retains the legacy passage-ID definition.

| Model | Context | Reference recall | Hit /36 | Complete /36 | Both sources /9 | MRR | Targets met |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| tfidf | 4 | 48.8% | 25 | 15 | 8 | 0.562 | 0/5 |
| tfidf | 12000 | 70.3% | 30 | 26 | 9 | 0.587 | 1/5 |
| tfidf | 16000 | 73.9% | 31 | 26 | 9 | 0.588 | 1/5 |
| bge-m3 | 4 | 61.2% | 29 | 21 | 7 | 0.588 | 0/5 |
| bge-m3 | 12000 | 82.1% | 34 | 28 | 9 | 0.610 | 3/5 |
| bge-m3 | 16000 | 85.8% | 36 | 30 | 9 | 0.614 | 4/5 |
| qwen3-4b | 4 | 69.9% | 32 | 24 | 6 | 0.731 | 1/5 |
| qwen3-4b | 12000 | 85.2% | 35 | 29 | 9 | 0.741 | 5/5 |
| qwen3-4b | 16000 | 88.6% | 35 | 33 | 9 | 0.741 | 5/5 |

### Tier artifacts

| Tier | Model | Passages | Corpus pin valid |
| --- | --- | ---: | --- |
| minimal | TF-IDF | 207 | yes |
| light | Qwen/Qwen3-Embedding-0.6B | 207 | yes |
| standard | BAAI/bge-m3 | 207 | yes |
| full | Qwen/Qwen3-Embedding-4B | 207 | yes |

Qwen retains all five targets at 12k and 16k. Scores reproduce the phase-1 candidate totals with approved labels and newly encoded canonical indexes. `tech-changing-neighborhood` remains incomplete at every tested context. TF-IDF has 80% group coverage but misses the split fixed-footprint evidence; BGE and Qwen miss other required groups.

The full per-question records and validated tier manifests remain in ignored `evaluation/runs/readable-formulas-adopted-2026-10-14`. The archived [JSON summary](https://github.com/Timerk/ResearchLens/blob/archive/evaluation-2026-10/docs/formula-adoption-results.json) includes all answerable question scores, current pins and artifact/run hashes. The light tier was rebuilt and validated but its retrieval quality was not remeasured.

The pre-rendering paid answer-quality study remains historical evidence with its original pins. These retrieval-only measurements do not update answer correctness, citation support or held-out performance claims.

## Reproduction

Reproduce from tag `archive/evaluation-2026-10`. The `formula_experiments` and
`formula_report` drivers that rebuilt the tier indexes and wrote these results, and
the one-time `formula_adoption` migration, were removed from main after adoption.
Backend tests on main still check the renderer, offline corpus reproducibility and
that the active corpus, labels and held-out file match the approval record.
