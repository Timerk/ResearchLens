# Constrained evidence selection and repair diagnostics

These experiments ran on 2026-10-05 using the unchanged approved development
questions, approved evidence groups and 204 canonical passages. They make no
held-out searches or paid API calls. The shared evaluation scorer measures every
selected set against the original evidence labels. No annotations, corpus text,
passage IDs, answer settings or application defaults change.

The best fully evaluated configuration remains BGE-M3 plus BGE reranking of 20
candidates at **26/36 complete questions**, below the 29/36 provisional target.
The following oracle and reviewed-support results use annotations unavailable
to a real retriever. They must not be presented as retrieval quality improvements.

## Actual four-passage ceilings

The constrained oracle asks whether a complete subset of at most four passages
exists *inside each question's specific candidate pool*. It preserves OR between
alternative support sets and AND between their supporting spans. A partial piece
of one alternative cannot combine with a partial piece of another. Exhaustive
search over labeled candidate IDs returns the smallest witness, or the best
partial coverage if no complete witness exists. Excluding unlabeled candidates
is exact for this annotation-based objective.

| Candidate pool | Oracle complete@4 /36 | Actual selection in that pipeline /36 |
| --- | ---: | ---: |
| BGE top 20 | 31 | 26, BGE reranking |
| Qwen top 40 | 34 | 25, whole-question BGE reranking |
| BGE top 40 | 33 | 25, previously measured BGE reranking |
| BGE20 plus Qwen40 union | 34 | Not run |
| BGE20 plus Qwen20 union | 33 | Not run |

There are five recoverable selection failures within BGE20 and nine within
Qwen40 when compared with their respective reranking pipelines. Do not subtract
BGE's actual score from Qwen's ceiling. Every complete witness found here fits
within three passages, so the earlier unrestricted-pool coverage counts happen
to equal the four-passage ceilings for these inputs. The distinction still
matters and is covered by a synthetic five-passage counterexample test.

The larger union adds no ceiling over Qwen40. The smaller union does not exceed
either single-retriever 40-candidate control. We therefore did not add union
inference or a new deployment path. Both BGE40 and Qwen40 still lack labeled
complete support for `tech-changing-neighborhood` and
`tech-compare-localization-outputs`. These are candidate failures in those pools.

The five BGE20 selection failures and their complete witnesses are:

| Question | Supporting passages already in BGE20 |
| --- | --- |
| Glass lighting paraphrase | `pmc11510794:p22:w0` |
| Wafer noise/efficiency question | `pmc10934137:p14:w180`, `p1:w0`, `p16:w0` |
| Compare fusion | `pmc11768589:p5:w0`, `pmc11510794:p59:w0` |
| Stripe frequencies and phases | `pmc11768589:p18:w0`, `p17:w0` |
| Adaptive-binarization scope | `pmc11768589:p22:w0`, `p29:w0` |

IDs abbreviated after the first entry in a cell belong to that same document.
Full IDs, all pool memberships, witnesses, cohort labels and question-level
selections are in [the archived results](selection-diagnostics-results.json).
Annotations are conservative and non-exhaustive. These ceilings concern approved
support, not every possible semantically sufficient passage combination.

## Decomposition, support scoring and selection substitutions

All substitutions below use the identical frozen Qwen40 candidates. Generated
needs and original BGE scores come from the previous information-needs study.
Exact search enumerates cached four-passage combinations, not model calls.
Both greedy and exact rank-utility selection use the same maximum-per-query
objective, original-question weight 0.5 and `11 / (11 + rank)` utility.

| Requirements and support signal | Greedy complete /36 | Exact complete /36 |
| --- | ---: | ---: |
| Generated question needs, cached BGE scores | 25 | 25 |
| Approved group descriptions, new BGE scores | 25 | 26 |
| Approved groups, reviewed per-passage support utilities | 31 | 31 |
| Approved groups, reviewed joint AND/OR support | Not applicable | 34 |

For the second row, each BGE query is the original question plus
`Evidence requirement: <approved group description>`. The pinned reranker scores
92 requirements across 40 passages each, 3,680 pairs, once. Maximum pair length
is 383 tokens, with no clipping. The original whole-question scores are unchanged.
Scoring these extra requirements takes a median 2,217 ms per case in single
staged samples, excluding query encoding, original scoring and selection.

Approved descriptions are reviewed annotation text and can contain answer facts.
This is a label-assisted diagnostic substitution. We did not create or claim a
new independent human review of model-generated needs, and the two phrasing
systems do not have a reviewed one-to-one semantic alignment. The diagnostic
does not establish that all decomposition methods are equivalent.

For the third row, single-passage full support is 1, absent support is 0 and a
member of an N-passage joint alternative receives partial utility 1/N. The
original-question rank utility remains as a secondary signal. This substitutes
the support signal and its scale while retaining the selection engine. It uses
the same approved requirements as row two, rather than fabricating reviewed
support labels for generated needs.

The last row instead checks the original joint alternatives as sets. The
max-per-passage objective in row three cannot express that two partial passages
jointly complete a fact. Its greedy output still misses
`tech-wafer-exact`, `tech-stripe-frequencies` and `tech-adaptive-binarization`,
although their complete support is available. This is a representation issue
as well as a scoring issue. Exact optimization of an inadequate objective does
not correct it.

Exact selection of generated rank utilities gains stripe frequencies and training
computers relative to generated greedy selection, but loses AMFF layers and
network-input comparison. The net count stays 25. Exact approved-description
selection reaches 26 by gaining stripe frequencies, but loses AMFF layers against
the incumbent. Neither is adopted. Question-level gains and regressions are
retained rather than hidden by aggregate ties.

## Quoted support assessment and one repair pass

A bounded pilot tests all five BGE20 failures with complete four-passage witnesses,
the first incumbent success in each of three answerable cohorts, and the first
two negatives. This is a deliberately failure-enriched ten-question diagnostic,
not a representative benchmark or a new development winner.

Inference uses the previously downloaded, pinned Qwen3-4B-Instruct-2507 Q4_K_M
model and llama.cpp b11327 Vulkan runtime. Model license, revision, download
requirements and native-process guards remain documented in
[the information-needs study](information-needs-experiments.md).
Requests use temperature 0, seed 42, at most 768 output tokens, one local slot,
no retries and no paid API. The earlier copied-question needs are reused. No
approved requirements, labels or expected source IDs enter support inference.
Development labels only choose the pilot cases and score its outputs.

The model checks the original four-passage context and marks each requirement
full, partial or absent, providing exact source quotes and missing information.
When a requirement is missing, it assesses all requirements against each of the
20 cached candidates, including unused passages. Exact set selection prioritizes
full requirement coverage, then partial support, then retaining incumbent passages
and dense order. Several strong matches for one fact cannot compensate for an
unsupported fact. Two partial judgments are never automatically promoted to full
joint support. A final combined-context check can recognize joint sufficiency,
but it is a fallible diagnostic judgment, not a production answerability gate.

There is at most one repair, no additional retrieval and no second repair after
verification. This isolates repairs within pools already known to contain
sufficient labeled evidence. Searching beyond a deficient pool, generated
requirement quality and model-proposed joint support remain separate work.

The initial output schema fails on 9/10 cases due to repeated requirement IDs,
inconsistent status fields or altered quotes. It is archived as a failed
configuration, with errors retained. A separate schema correction uses fixed
requirement keys, status-dependent fields and quotes constrained to contiguous
source segments. Quotes are at most 300 characters; long sentences are split
at word boundaries. Postvalidation checks every quote and records its offsets.
This constrains output grounding, not whether a quote proves the requested fact.
The correction is a separate experiment, not an automatic inference retry.

Corrected pilot results:

| Outcome | Result |
| --- | --- |
| Valid cases | 10/10, no errors |
| Targeted failures repaired | 2/5, stripe frequencies and adaptive-binarization scope |
| Previously complete controls broken | 0/3 |
| Initial verifier falsely marks an incomplete set complete | 1, wafer noise/efficiency |
| Final verifier rejects a labeled-complete repair | 1, stripe frequencies |
| Final verifier rejects a complete success control | 1, training-split comparison |
| Negative cases marked complete | 0/2 |

The eight answerable pilot cases change from 3 to 5 complete evidence sets. We
do not add two to the incumbent's 26/36, because the other development questions
were not tested with this repair pipeline. The verifier's false-complete decision
prevents repair of the wafer question; its false-incomplete decisions show that
using it as a strict acceptance gate would also reject valid evidence. The two
negative examples do not establish abstention behavior generally.

The corrected pilot uses 157 local support requests. Summed single-stage request
times have a median about **30 seconds per pilot case**, excluding original
retrieval, with a range about 1.4 to 75.6 seconds. These timings include cases
where verification skips repair and cases assessing all 20 candidates. They are
not a controlled end-to-end throughput benchmark. Peak native private memory is
3.46 GiB, separate from Python and VRAM. All owned servers are stopped. The
incumbent remains around 0.48 seconds per query, so this pilot is much too costly
for adoption and does not reach our full-set completeness target.

## Implementation parity and reference-recall interpretation

A new cached Qwen4B embedding check compares our right-padding, last-nonpadding
pooling path with documented left-padding, final-token pooling and L2 normalization
on three development questions and three distinct canonical passages. Both paths
use the same pinned model, CPU bfloat16 and task-specific research instruction.
Vector cosines are 0.99980 to approximately 1.0; document rankings agree for all
three questions. Reencoded passage vectors agree with saved vectors to numerical
rounding. This is a bounded pooling/batching check, not full upstream-equivalence
or retrieval-quality evidence.

The existing reference check already compared 100 identical pairs per reranker
against CPU float32. BGE and Qwen top-four sets match on all five sampled questions;
Qwen order differs on one negative. Those templates and yes/no scoring do not
show a large implementation mismatch in this sample. See
[the Vulkan reference results](vulkan-reranking.md). We did not rerun them.

Original reference-passage recall counts all original reference IDs even when
approved alternatives are interchangeable. For example, the forward/backward
lighting question has two original references, but either approved passage alone
supports both facts. Complete evidence can therefore coexist with 50% original
reference recall.

Four questions have more than four original references, including 13 on the fusion
comparison. Even perfect corpus-wide four-passage selection has a mean original
reference-recall ceiling of **96.0%**. Within BGE20 it is 85.2%; within Qwen40 it
is 93.7%. These independently maximize original-ID recall, not recall constrained
to a simultaneously complete support set. The 80% recall target is feasible in
aggregate, but 100% on every question is not. Completeness remains the main metric.

## Reproduce and integrate

Run from `backend` using the existing pinned artifacts and model assets. Use new
output paths because experiments refuse to overwrite existing result directories.

```sh
rtk proxy ../.venv/Scripts/python.exe -m researchlens.selection_diagnostics --output ../evaluation/runs/selection-diagnostics-new/oracles.json
rtk proxy ../.venv/Scripts/python.exe -m researchlens.selection_diagnostics --stage reviewed-scoring --diagnostics ../evaluation/runs/selection-diagnostics-new/oracles.json --output ../evaluation/runs/selection-diagnostics-new/reviewed-scoring
rtk proxy ../.venv/Scripts/python.exe -m researchlens.repair_experiments --diagnostics ../evaluation/runs/selection-diagnostics-new/oracles.json --output ../evaluation/runs/support-repair-new
```

From the repository root:

```sh
rtk proxy .venv/Scripts/python.exe docs/embedding-parity-check.py --output evaluation/runs/embedding-parity-new.json
rtk proxy .venv/Scripts/python.exe docs/selection-diagnostics-results.py --output docs/selection-diagnostics-results-new.json
```

`selection_diagnostics` validates approved development inputs, artifact hashes,
canonical candidate text and stable saved runs. The pure `set_selection` and
`support_assessment` selectors consume cached utilities and do not read labels.
The repair pilot has no production `Retriever.search` integration. Canonical
passages, citations, question limits and the application's four-passage context
budget are unchanged. The production default remains TF-IDF and both frozen
experimental selections remain unchanged.

The archive retains plans, source/input hashes, candidate IDs, witnesses, full
score matrices, model judgments, source quotes, stage timing and paired outcomes,
including the failed initial schema. It omits repeated tokenizer sidecars and
large assets. Recorded source hashes identify the experiment snapshots before
later formatting/defensive validation edits. The archived first failed schema
is historical; the current reproduction command runs the corrected schema.

236 backend tests pass, with Ruff lint/format and Git whitespace checks. The new
offline tests cover impossible four-passage ceilings, joint alternatives, a greedy
trap, exact ties, grounded quotes, missing/duplicate fields and coverage-first
selection. They establish functionality rather than research quality. Independent
semantic review of generated needs, a full-set repair comparison, faster support
scoring, explicit predicted joint-support assessment, held-out performance and
generated-answer correctness/citations/abstention remain pending.
