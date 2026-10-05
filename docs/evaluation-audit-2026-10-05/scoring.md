# Scoring and cached-result audit

This is an AI-assisted audit dated 2026-10-05. It is not a new human approval of
the development questions or evidence labels. The original approved scoring
contract reproduces exactly. Its completeness measure asks whether retrieval
supplies the entire approved evidence package. It does not establish that a
generated answer would be correct, or that every package requirement is necessary
to answer the visible question.

## Reproduction

[replay.py](replay.py) calls the existing
[`ranking_metrics` and `evidence_coverage`](../../backend/researchlens/evaluation_evidence.py),
[`cutoff_summary`](../../backend/researchlens/evaluation_metrics.py),
[`minimal_supports`](../../backend/researchlens/retrieval_analysis.py), and the
application's [`prepare_answer_context`](../../backend/researchlens/answers.py).
It does not implement another relevance scorer, instantiate a retrieval model,
or call an answer provider.

The replay covers all 21 configurations in
[`retrieval-improvement-results.json`](../retrieval-improvement-results.json)
and all 10 configurations in
[`vulkan-reranking-results.json`](../vulkan-reranking-results.json). The selection
of archives covers the lexical baseline, dense controls, fusion variants and both
reranker families. It does not select configurations according to annotation-change
gains. The 1,550 saved case rankings reproduce their archived four-passage metrics
and summaries with no mismatch. Read-only verification of the original local
`run.json` files also reproduces all 6,150 saved case/cutoff combinations.

The existing validators reconstruct and verify the 204 canonical passages from
the four documents. They check all original reference locations and all 92 groups,
140 alternatives, and 165 evidence-span occurrences. There are 138 distinct
passage/range triples. Every range is in bounds, every exact quote matches its
canonical text slice, and every span belongs to an expected source. All four
original XML file hashes match the source manifest. These are integrity checks;
they cannot decide whether a quote proves a fact in context.

The source corpus SHA-256 is
`cda1b161618373b9c7b9701d3326fda4707f9501bbc3bf29c802d9a000908bce`.
The shared passage identity is
`c7bf2f1f6b9c866573669f946866b5b0635ae4afcee1d06511e3109ab47c1157`.
The approved labels' canonical JSON hash is
`8e1b118b740f615c5985eda60936b796cf7abb8c2c302b7845ffbcaa93b1973f`.
The replay records byte hashes separately from canonical JSON hashes and the
evaluator's normalized dataset digest. Those methods differ, including when Git
checkout line endings differ; the distinct hashes are not evidence of changed
questions. The Vulkan archive uses canonical JSON run hashes, whereas the earlier
retrieval-improvement archive records file-byte run hashes.

## What the original numbers mean

All metrics below use 36 answerable development cases. The 14 negatives are
unscored for positive retrieval relevance and completeness.

| Saved configuration, four passages | Original reference recall | Any-evidence hit | Any-evidence MRR | Mean group coverage | Complete evidence |
| --- | ---: | ---: | ---: | ---: | ---: |
| TF-IDF | 47.64% | 25/36 | 0.5579 | 55.19% | 15/36, 41.7% |
| BGE-M3 dense | 61.40% | 30/36 | 0.5926 | 70.79% | 22/36, 61.1% |
| Qwen3-Embedding-4B dense | 69.25% | 32/36 | 0.7153 | 78.29% | 24/36, 66.7% |
| Qwen4B, BGE reranker, 40 candidates | 71.66% | 33/36 | 0.8333 | 79.35% | 25/36, 69.4% |
| BGE-M3, BGE reranker, 20 candidates | 71.66% | 33/36 | 0.8333 | 80.28% | 26/36, 72.2% |

The incumbent's saved median query time is approximately 0.48 seconds. Replay
does not remeasure model latency. The earlier TF-IDF archive queried 40 passages
and saved its four-passage prefix; its timing is not a new application-limit
measurement. The separate approved model-comparison archive also reports 15/36
for TF-IDF with an actual limit of four.

Original reference-passage recall intersects the retrieved IDs with the original
question reference list. That denominator is unchanged by approved alternatives.
For example, either approved forward/backward illumination passage can support
the whole answer while retrieval of one original reference yields 50% reference
recall. This metric retains its historical meaning and results.

Any-evidence hit asks whether at least one retrieved ID appears anywhere in the
approved groups. MRR is the reciprocal rank of the first such ID, averaged over
all answerable cases. A passage that supplies only one member of a joint
alternative still earns the hit and its rank. These measures therefore do not
require even one complete factual group, let alone a complete answer. The
incumbent's 33/36 hits and 26/36 complete packages illustrate the distinction.

Group coverage uses OR between alternatives and AND between spans within an
alternative. A group succeeds when one whole alternative is available. Complete
evidence requires every group. The aggregate coverage is the mean of each
question's fraction of covered groups, rather than the fraction of all 92 groups
pooled together. Each question has equal aggregate weight, even when its group
count differs. Group boundaries can therefore affect partial coverage.

Source recall measures document presence, which is weaker still. The incumbent
has 98.61% source recall despite missing ten approved evidence packages.
Neither source presence nor valid citation IDs establish factual support.

The runner gives retrieval errors zero relevance and group coverage. Unknown
encoder ranges remain unknown, whereas missing passages are misses. An unlabeled
positive would be excluded from the labeled completeness denominator and exposed
through the labeled-case count. That does not affect these runs because all 36
positives have labels. Negatives retain null relevance/coverage/completeness;
returning nearby text is neither a positive success nor measured abstention.

The four-passage context preview uses the application's existing limits. Full
retrieval text and provider-visible text are distinct. The inspected archived
controls record no context truncation loss. Replay also checks the existing
context builder against canonical first-four text. No answer-generation accuracy,
citation quality or abstention behavior is measured.

## Feasibility and diagnostic limits

The original annotations have complete corpus-wide support using one passage for
18 questions, two for 16, and three for two. The actual candidate-pool ceilings
remain 31/36 within BGE20 and 34/36 within Qwen40. A union of those pools remains
34/36. These are exact feasibility results under the current labels, not semantic
validation of the labels and not deployable retrieval quality.

Original reference recall has a separate four-slot corpus-wide ceiling of
96.0399%, independently maximizing original-ID recall for each question. Four
questions cannot reach 100% at four passages:

| Case | Original references | Maximum original reference recall at four |
| --- | ---: | ---: |
| `tech-painted-exact` | 5 | 80.0% |
| `tech-autoencoder-exact` | 5 | 80.0% |
| `tech-compare-fusion` | 13 | 30.77% |
| `tech-changing-neighborhood` | 6 | 66.67% |

The corresponding mean ceilings inside the saved BGE20 and Qwen40 pools are
85.2% and 93.7%. Those optimizations need not choose the same sets as a
complete-evidence oracle. A target for one metric cannot be interpreted as a
target for another.

[`retrieval_analysis.analyze_run`](../../backend/researchlens/retrieval_analysis.py)
uses the run's returned passages as its candidate set. On a reranked run with
`limit=4`, its `candidate-pool-missing-evidence` diagnosis only establishes that
the returned four lack support. It cannot distinguish upstream top-20 candidate
failure from reranker selection failure. This audit uses the actual saved pools
in [`selection-diagnostics-results.json`](../selection-diagnostics-results.json)
for that distinction. This is an interpretation limit, not a defect in the
four-passage completeness arithmetic.

The evaluation README's later ranking paragraph says MRR uses expected passage
IDs. Its earlier alternatives paragraph and the implementation correctly specify
approved evidence IDs when labels exist. Update that stale sentence in a separate
documentation change. Do not change old MRR values to match the stale wording.

## Proposed contract and sensitivity analysis

The approved v2 metrics and labels remain the reference result. Proposed changes
are kept in a separate unreviewed overlay. Adding an alternative can correct
non-exhaustive support labels without changing a requested fact. Removing a group
from visible-question completeness changes the required answer scope and needs
its own explicit contract and approval. A qualification classified as conditional
remains mandatory when the answer chooses to make the claim that triggers it.

The replay applies each proposal individually and by declared category and
decision kind. It also records their combined sensitivity. It retains the
original metrics beside the proposed metrics, names every newly complete and
newly incomplete case, and lists remaining failures. The original reference list
never changes, so original reference recall is identical across these scopes.
Any-evidence MRR can change when group membership changes; it is reported within
its own scope instead of replacing the historical result.

These proposed results are post hoc development diagnostics. A change in the
number of complete evidence sets establishes neither a retrieval improvement nor
generated-answer correctness. It identifies which historical package failures
would stop being evidence failures under a justified visible-question contract.
Owner decisions and uncertainty about source context remain explicit in the
case audits. No proposal grants itself human approval.

The [proposed-revisions.json](proposed-revisions.json) overlay has 13 executable
changes. [replay-results.json](replay-results.json) retains all original results
and the 19 sensitivity scenarios. The categories are separated because the
adaptive-binarization interpretation is less certain than the self-contained
alternative passages.

| Saved configuration | Original complete /36 | Strict alternatives only | Contextual p22 alternative only | Question scope only | Combined proposals |
| --- | ---: | ---: | ---: | ---: | ---: |
| TF-IDF | 15 | 15 | 15 | 16 | 16 |
| BGE-M3 dense | 22 | 22 | 23 | 23 | 24 |
| Qwen4B dense | 24 | 24 | 25 | 26 | 27 |
| Qwen4B, BGE reranker, 40 candidates | 25 | 25 | 26 | 26 | 27 |
| BGE-M3, BGE reranker, 20 candidates | 26 | 26 | 27 | 27 | 28 |

For the incumbent, strict alternative additions change no group coverage or
complete-evidence result. The visible-question scope proposal alone changes
`tech-wafer-exact` from incomplete to complete. Its cached four passages already
support the requested TDI-stage/noise facts. Removing the efficiency qualification
from mandatory visible-question evidence produces 27/36, or 75.0%. The
qualification remains required for any extra efficiency claim.

Accepting p22 alone for the adaptive-binarization purpose is a separate contextual
judgment. The cached four include p22. This alternative produces a second gain
only if the owner accepts that the paragraph's stated purpose and preprocessing
steps jointly support that fact. With both judgments accepted, the incumbent
would have 28/36 complete visible-question evidence sets, or 77.8%, with 83.06%
mean group coverage. Original reference recall stays 71.66%, any-evidence hit
stays 33/36, and MRR stays 0.8333. The provisional 29/36 target is still unmet.

The AMFF conflict-scope proposal does not affect the incumbent because its
retrieved evidence already includes the conflict group. It changes some dense
controls, including BGE-M3 and Qwen4B. The proposed optional-detail removals for
augmentation and manual masks produce no incumbent completeness gain. The
daylight/tunnel issue remains a narrative proposal to split a compound group;
the executable overlay retains its explicitly requested uncontrolled-light
qualification. The wafer alternative is validated before the combined scenario
removes that conditional group; its separate scenario retains its independent
effect instead of counting the same correction twice.

These original ten incumbent failures make the practical limit clear:

| Case | Missing original package evidence | Original BGE20 diagnosis | Outcome under all proposed changes |
| --- | --- | --- | --- |
| `tech-glass-paraphrase` | Scratch detail/reflection limits; backward depth; backward detail loss | Selection failure | Still missing all three groups; p22 was available in BGE20 |
| `tech-wafer-exact` | Fixed-line-frequency and excluded-transmission efficiency scope | Selection failure | Visible question has sufficient cached evidence if the scope change is approved |
| `tech-compare-fusion` | Canopy lighting, RGB fusion and ADMF-Net feature fusion | Selection failure | Still missing all canopy groups; the selected four are all heater passages |
| `tech-stripe-frequencies` | Zero phase for both tested patterns | Selection failure | Still missing the phase group; p17 was available in BGE20 |
| `tech-adaptive-binarization` | Purpose of grayscale/adaptive binarization | Selection failure | Sufficient cached evidence only if the contextual p22 alternative is approved |
| `tech-both-checks-clean` | Structured-OK transition and both-modes final OK | Candidate-pool failure | Still missing both groups |
| `tech-moving-signal-addition` | Charge follows moving image and accumulates across stages | Candidate-pool failure | Still missing the charge-transfer mechanism |
| `tech-too-many-shortcuts` | Defect reconstruction weakens residual discrimination | Candidate-pool failure | Still missing residual-purpose support |
| `tech-changing-neighborhood` | Gaussian spread effects and schedule, epoch reset, fixed 11-by-11 footprint | Candidate-pool failure | Still missing all five groups |
| `tech-compare-localization-outputs` | Canopy oriented boxes and autoencoder residual localization | Candidate-pool failure | Still missing both output groups |

Thus the combined proposal leaves three selection failures and five BGE20
candidate failures. The five candidate failures remain candidate failures under
the proposed labels. The BGE20 ceiling remains 31/36 and the Qwen40 ceiling remains
34/36 in every scenario. Four returned passages remain sufficient in principle
under both scopes; the unsolved failures are not explained by a larger required
context budget. These statements concern source evidence, not generated answers.

## Reproduce locally

Run from the repository root with the existing environment. This command reads
only the named development archives and canonical corpus. It does not require
model weights or raw ignored run directories, and it never opens a held-out file.

```sh
rtk proxy .venv/Scripts/python.exe docs/evaluation-audit-2026-10-05/replay.py --overlay docs/evaluation-audit-2026-10-05/proposed-revisions.json --output evaluation/runs/audit-replay-new.json
```

Omit `--overlay` to reproduce only the approved contract. Optionally add
`--raw-runs-root <existing-development-runs-directory>` to verify original run
hashes, canonical retrieved text and every saved cutoff. The output path must be
new. The current audit used the prior worktree's existing environment and ignored
development run directories read-only. No approved dataset, evidence label,
review archive, passage text, citation ID or application setting was changed.
