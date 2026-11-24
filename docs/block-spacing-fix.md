# List-item spacing fix, 2026-11-24

This is a source text change to the technical corpus made after the formula adoption.
All published evaluation numbers predate it. This page records what changed, why the
evaluation inputs stay pinned to the earlier corpus, and why the change should not
materially affect the published results.

## What was wrong

Extraction flattens each XML `<p>` by joining element text and tails. When a paragraph
contains a list, as in `<p>…as follows:<list><list-item><p>An automated…</p></list-item>…`,
the item paragraphs were joined with no whitespace between them. The corpus then held
words such as `follows:An` and `achieved.A`, and cited passages on the site showed them.

Now `<list>`, `<list-item>`, a nested `<p>` and other JATS block elements (`def-list`,
`disp-quote`, `label`, `title` and similar, listed in `BLOCK_ELEMENTS` in
`backend/researchlens/mathml.py`) are separated by a space. Inline markup such as
`<italic>`, `<sub>`, `<sup>` and `<xref>` stays unspaced, so `CO<sub>2</sub>` still
reads `CO2`. List markers are not invented: ordered lists render without numbers, as
before. Formula rendering is unchanged.

## What changed in the corpus

Ten joins in four paragraphs of two articles. All of them were list items:

| Article | Paragraph | XML location | Joins |
| --- | --- | --- | ---: |
| Canopy, PMC11510794 | p5 | `./body/sec[1]/p[4]` | 3 |
| Canopy, PMC11510794 | p34 | `./body/sec[3]/sec[3]/p[6]` | 1 |
| Autoencoder, PMC11121878 | p6 | `./body/sec[1]/p[5]` | 2 |
| Autoencoder, PMC11121878 | p10 | `./body/sec[1]/p[9]` | 4 |

For example, `summarized as follows:An automated prototype system` is now
`summarized as follows: An automated prototype system`, and
`non-defective regions.Noise-free normal background` now has a space after the period.
The list in PMC11768589 sits outside a paragraph, so each item was already its own
paragraph. After the fix the corpus has no match for `[a-z)\]][.:;][A-Z]`, and a test
checks that.

Only whitespace changed: each changed paragraph is identical to the old one with spaces
removed. Paragraph count, sections, XML locations and all 207 passage IDs are unchanged.
Six passages have different text:

| Passage | Characters before → after |
| --- | --- |
| `pmc11510794:p5:w0` | 822 → 825 |
| `pmc11510794:p34:w0` | 1169 → 1158 |
| `pmc11510794:p34:w180` | 527 → 541 |
| `pmc11121878:p6:w0` | 771 → 773 |
| `pmc11121878:p10:w0` | 1243 → 1232 |
| `pmc11121878:p10:w180` | 356 → 371 |

Split words now count as separate words, so the 180-word windows of p34 and p10 move by
up to four words: a few trailing words of `w0` now start `w180`.

| Hash | Corpus |
| --- | --- |
| `f293a02c7afaf38f06ec17d6443f7289fd3a7d3091cf11cf0d4f865ee0e3a675` | Adopted 2026-10-14 corpus, pinned by all evaluation inputs |
| `4636a0aaecee97a80f458b245f8cce79315afd8abe1013cea38792bf8f42917b` | Live corpus with block spacing (`mathml-readable-v2+block-spacing`) |

`documents.json`, `manifest.json` and `NOTICE.txt` were regenerated with
`python -m researchlens.corpus`. The attribution text of every passage now mentions the
change. `data/demo/recorded-answers.json` was regenerated with
`python -m researchlens_eval.demo_recordings`, which changed only that attribution text.

## Evaluation inputs stay pinned

The development dataset, the development evidence labels, the frozen held-out set and
the owner approval record all pin the adopted corpus `f293a02c…`. They are unchanged, and
the runner refuses to score them against the live corpus. Migrating them would be a
source text change that needs owner review, as the
[formula adoption](formula-adoption-results.md) did. Four of the 167 development span
occurrences would need new offsets: three in `pmc11510794:p5:w0` (`tech-compare-fusion`)
and one in `pmc11121878:p6:w0` (`tech-too-many-shortcuts`). Each quote is still present
verbatim, shifted by one to three characters. No quote text changes. One held-out
reference points to `pmc11121878:p10:w0`, whose ID is unchanged.

The extractor keeps the old behaviour behind `separate_blocks=False`, like
`readable_formulas=False` for formulas. To reproduce a published result, rebuild the
adopted corpus byte for byte and point ingestion and the runner at it:

```sh
mkdir -p evaluation/runs/adopted-corpus
uv run --directory backend python -m researchlens.corpus --adopted-corpus ../evaluation/runs/adopted-corpus/documents.json
uv run --directory backend python -m researchlens.ingest --source ../evaluation/runs/adopted-corpus/documents.json --destination ../evaluation/runs/adopted-corpus/index.json
# Then pass --source and --index with these two files to the evaluation runner.
```

`evaluation/runs/` is ignored by Git. Dense indexes need `--retrieval embeddings` and
`--embedding-model` at ingestion, as in the [evaluation workflow](../evaluation/README.md).
The first command fails if the rebuilt file does not hash to `f293a02c…`. The tests use the
same reconstruction to keep validating the approved labels and the frozen held-out
references.

## Why the published numbers should not change materially

- **Retrieval.** TF-IDF indexes of both corpora were compared on all 50 development
  questions. The top four passages are identical for all 50 questions, and every
  reference passage keeps its rank in the top 40. Six questions differ lower down,
  first at ranks 7 to 34. No held-out question was searched for this check.
- **Dense models.** The BGE-M3 and Qwen3 tiers were not re-encoded. BGE-M3 needs 5 GiB
  of free RAM and the machine had 1.9 GiB. Six of 207 passage vectors will move slightly,
  because a few tokens change at word boundaries. The effect is unmeasured. It is
  expected to be small because the words and their order are unchanged.
- **Evidence scoring.** Labels match quote text at character offsets. On the live corpus
  the four shifted spans would not match until migrated. That is why the evaluation
  stays pinned to the adopted corpus instead of being scored on the live one.
- **Context budgets.** The six passages change by −11 to +15 characters. That could move
  a budget cut at 12,000 or 16,000 characters by one passage only where a cut falls
  exactly at one of these passages.
- **Answer quality.** The 2026-10-13 answers were generated on the pre-formula corpus
  and are recorded verbatim. This fix does not touch them. Two demo examples
  (`canopy-heater-fusion` and `rotation-augmentation`) cite affected passages. Their
  excerpts still show the joined words, because that is the text the model saw.

No paid API call and no held-out retrieval ran for this change.

## Deployment

The live corpus hash changes, so the server's existing tier indexes fail the corpus pin
check at startup. After releasing a tag with this change:

```sh
./deploy/deploy.sh <tag> --reingest
dc run --rm --no-deps backend python -m researchlens.ingest --tier minimal
```

`--reingest` rebuilds the light index before the stack starts. It uses Qwen3-0.6B, which
is already cached in its volume, and takes a few minutes on CPU. The `tier-indexes`
volume also holds a minimal TF-IDF index that hides the one built into the image. Rebuild
it too, or the fallback tier stays stale. [deployment.md](deployment.md#operations)
lists both commands under "Rebuild the light index after a corpus change". Without
`--reingest`, the backend refuses the stale light index and the deploy fails. It does
not serve stale passages.
