# Readable MathML candidate, phase 1

The isolated `mathml-readable-v2` candidate restores 122 formulas in retained prose.
Four unsupported `mmultiscripts` formulas remain `[formula omitted]`. Canonical
documents, original XML, manifest, corpus hashes, approved development labels and
the frozen held-out dataset remain unchanged. Corpus adoption and label approval
are pending the project owner's decision.

This branch starts at main `d001d2b`, after PR #9 merged. Only the requested formula
paths were imported from `b9fa7c5`. The v1 summary remains as a historical estimate;
its generated corpus is retained locally in ignored
`evaluation/runs/mathml-readable-v1-import/`. New corpus, index, proposed labels and
full evaluation outputs also stay ignored. Only summaries and review documents
are committed.

## Renderer review

The renderer keeps symbols such as `σ` and `k`, separates adjacent tokens, and
groups fractions, subscripts and superscripts explicitly. It never evaluates an
expression or inserts a numeric parameter value. Token children, mixed content,
invalid operand counts and unsupported structures trigger whole-formula fallback.
Spacing text is allowed without introducing numbers or operators.

The prototype incorrectly represented `mover` as exponentiation. V2 uses explicit
`over(base; annotation)` and `under(base; annotation)` notation, so an overbar or
limit cannot masquerade as a power. It respects empty fence separators and repeats
the last declared separator as MathML specifies. Font variants with mathematical
meaning remain explicit, for example `bold(x)` and `double-struck(R)`. This is
readable source transcription, not scientific approval of the equations.

| Article | Rendered formulas | Still omitted | Changed paragraphs |
| --- | ---: | ---: | ---: |
| Canopy, PMC11510794 | 20 | 0 | 5 |
| Heater, PMC11768589 | 0 | 0 | 0 |
| Wafer, PMC10934137 | 22 | 0 | 7 |
| Autoencoder, PMC11121878 | 80 | 4 | 22 |
| Total | 122 | 4 | 34 |

V2 preserves canonical paragraph selection, section names, XML locators, licensing
and original-source SHA-256 values. It records the renderer/remapper hashes and
protected input hashes in the [candidate summary](../data/technical/prototypes/mathml-readable-v2/summary.json).
Re-extraction must match the canonical documents before a candidate can be built.

## Exact development span migration

All 165 approved span occurrences were checked against exact canonical substrings.
Each paragraph is aligned by replacing complete `[formula omitted]` tokens in
source order. All surrounding prose must match exactly. This avoids fuzzy matching
and ambiguity from repeated quotes. Boundaries inside a replaced placeholder are
unmappable rather than guessed.

| Classification | Occurrences |
| --- | ---: |
| Unchanged quote, passage ID and offsets | 132 |
| Shifted only, quote preserved | 14 |
| Quote text changed | 19 |
| Cannot map | 0 |

Two occurrences cross candidate windows and become AND fragments in the same
alternative: `training samples.` in `tech-autoencoder-exact`, and the fixed
11 × 11 footprint sentence in `tech-changing-neighborhood`. No group, description,
claim index or OR alternative was removed. Every proposed quote validates against
the candidate index. Candidate labels have `unreviewed` status with no reviewer
or approval date. The original approval is not transferred to changed text.

The [remapping review](formula-remapping-review.md) lists all 33 changed occurrences
with old and new quotes side by side. Proposed complete labels are in
`evaluation/runs/readable-formulas-v2-final/development-labels.json`; the exact
165-occurrence migration record is `remapping.json` beside them. These files are
reproducible outputs, not replacements for approved labels.

## Held-out references and freeze

Held-out has no approved span labels. Only its 62 passage references and frozen
source/corpus pins were inspected offline. No held-out answer or claim guided the
renderer, and no held-out retrieval ran.

| Reference classification | Occurrences |
| --- | ---: |
| Unchanged | 51 |
| Text changed, same ID covers aligned range | 7 |
| ID changed, including split-window coverage | 4 |
| Unmappable | 0 |

All proposed references retain the same source, paragraph, section and XML locator.
The review lists every reference occurrence and proposed ID. The four ID changes
include old windows whose content now needs two candidate windows; merely checking
that the old ID still exists would miss this.

Original `source_versions` still match. The frozen corpus pin
`cda1b161618373b9c7b9701d3326fda4707f9501bbc3bf29c802d9a000908bce`
differs from candidate
`fe1c769f0ab662ac36cafd55982dbcc19c390b53f81fedff7852cc02aae23d26`.
Adoption therefore requires a new held-out dataset version and owner approval.
The frozen held-out dataset was not edited. No candidate held-out dataset or span
labels are retained.

## Development retrieval findings

[Results](formula-rendering-results.md) report all five targets for TF-IDF, BGE-M3
dense and Qwen3-4B dense at four passages, 12k and 16k serialized characters, paired
exact McNemar tests and per-question changes. The [JSON summary](formula-rendering-results.json)
records run hashes, runtime and encoding settings, index provenance and score deltas.

Every configuration ran through the existing evaluation CLI with `--limit 40
--context-budgets 4 12000 16000`. Canonical runs were repeated locally. Dense indexes
reuse 162 byte-identical passage inputs under the same pinned encoder settings and
re-encode all 45 changed candidate passages. Runs use one query attempt, no warmup,
no generation and no paid API calls. No latency comparison is claimed.

| Model | Complete at four passages, old/new | Complete at 12k, old/new | Complete at 16k, old/new |
| --- | ---: | ---: | ---: |
| TF-IDF | 15/15 | 26/26 | 26/26 |
| BGE-M3 dense | 22/21 | 29/28 | 30/30 |
| Qwen3-4B dense | 24/24 | 30/29 | 33/33 |

All counts use 36 answerable development questions. Qwen retains all five targets
at 12k and 16k. BGE meets three of five at candidate 12k, down from four, and four
of five at 16k. Every paired McNemar p-value is 1.0; these small changes provide
no evidence of a population improvement. Candidate scores remain provisional until
the proposed mappings receive review.

`tech-changing-neighborhood` remains incomplete at every tested context. TF-IDF
top-four group coverage rises from 20% to 80%; the missing fixed-footprint span
now requires `p29:w0` AND `p29:w180`. BGE and Qwen still miss required groups.
Qwen's `p31:w0` rank improves from 23 to 20; BGE's worsens from 11 to 12.
The premise that no model retrieves any relevant neighborhood passage in the top
40 does not hold for the current approved-label baseline. Complete evidence is
still missing, which is the material failure.

BGE loses `tech-adga-shapes` completeness at four passages and `tech-wafer-exact`
at 12k. Qwen loses `tech-too-many-shortcuts` at 12k. Both 16k complete counts remain
unchanged. Formula restoration repairs referents but does not establish better
retrieval, generated-answer correctness or scientific fidelity.

## Reproduction

Use the locked Python environment with the local embedding-model and development
dependencies. From `backend`, with fresh candidate and run directories:

```sh
rtk proxy python -m researchlens.formula_prototype --destination ../evaluation/runs/readable-formulas-v2-final
rtk proxy python -m researchlens.formula_experiments --candidate ../evaluation/runs/readable-formulas-v2-final --indexes /path/to/canonical/indexes --output ../evaluation/runs/readable-formulas-development-v2
rtk proxy python -m researchlens.formula_report --candidate ../evaluation/runs/readable-formulas-v2-final --output ../evaluation/runs/readable-formulas-development-v2 --publish-summaries
```

The canonical index directory must contain validated `tfidf.json`, `bge-m3.json`
and `qwen3-4b.json` artifacts for the unchanged corpus. Build them separately with
`researchlens.ingest` if absent. The measured run used the pinned CPU encoders,
bfloat16, 512 tokens, batch size one and eight threads. Model weights must already
be cached for the candidate builder, which uses `download=False`.

The candidate corpus, passage index, proposed labels and development dataset
reproduced byte-for-byte in a second fresh build. All 215 backend tests pass.
Focused tests cover grouping, whole-formula fallback, overbar notation, fence
separators, atomic alignment, repeated quotes, AND splits and held-out reference
splits. Ruff checks and formatting pass.

Stop at this draft PR. The owner must decide whether to adopt the corpus, approve
the proposed development span migrations and create a new frozen held-out dataset
version. No canonical promotion is part of phase 1.
