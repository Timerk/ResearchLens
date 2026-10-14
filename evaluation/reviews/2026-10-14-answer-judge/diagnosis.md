# Diagnosis of the archived answer judge

Read this after blind owner grading. These findings describe #16's old-corpus
development outputs, not the current readable-formula corpus. The independent
reviewer was Codex GPT-6.1-Sol, not a human. Disagreements identify a rubric dispute;
they do not establish which model is correct. The owner review will settle it.

The compressed evidence bundle matches #16's manifest, and all four run hashes
and four review hashes verify. Replaying the saved judgments through the current
scorer reproduces all 200 score records exactly. The reported 4/18 symptom is
qualification preservation among semantically judged, sampled answers, not
overall agreement across all judgment types.

## What disagrees

The following counts compare the saved per-answer audit with the scorer.
The 18 semantic answers are repeated configurations of six questions. The
audit has 40 responses overall, with deterministic checks counted separately.

| Judgment type | Semantic agreement | Deterministic agreement | Interpretation |
| --- | --- | --- | --- |
| Complete required claims | 18/18 | 6/6 section-free positive answers | No observed semantic disagreement in this small audit. |
| All qualifications | 4/18 | 6/6 section-free positive answers | Four agreements on normal-only training; 14 disagreements on scope and disclaimers. |
| No forbidden claims | 18/18 | 22/22 section-free answers | Every prediction says no violation; sensitivity is untested. |
| All citations supported | 17/17, one unresolved | Not applicable | One sampled supported answer loses verification because its quote is not verbatim. |
| Negative abstention | Not a semantic judgment | 16/16 | All audited negatives are correct section-free abstentions. |
| Citation IDs valid | Not a semantic judgment | 18/18 | All supplied IDs are valid; entailment remains a separate question. |

Qualifications account for all 14 binary disagreements in the 18-answer semantic
comparison. Their breakdown is ImageNet initialization, four; ideal SNR scaling,
three; camera fixture scope, three; and cross-document comparisons, four.
The six section-free positive answers fail content completeness locally and
agree with the audit. Counting those deterministic outcomes would obscure the
semantic qualification failure.

## Qualification failure mechanism

The version-one prompt asks whether the answer "explicitly conveys" every
qualification. Several approved qualifications combine a positive scope with
a prohibition against overinterpretation. The audit accepts an answer whose
wording retains the scope without asserting the prohibited interpretation.
The judge often requires a separate disclaimer for the prohibited interpretation.

For ImageNet initialization, the answer says the transferred classifiers were
pretrained on ImageNet. The judge acknowledges pretraining, then fails it for not
explicitly distinguishing initialization from new training on all ImageNet.
For SNR scaling, the answer begins "Ideally" and gives square-root scaling. The
judge acknowledges ideality, then requires a separate denial of a measured
guarantee under every noise condition. For the camera fixture, an answer explains
fixed camera/sample geometry, but the judge requires an explicit statement that
this is not a measured registration-error bound.

This demand is inconsistent with its normal-only training judgments. Those pass
because the answer places artificial defects in stage two and normal-only samples
in stage one, without separately denying real-defect training in stage one.
The key question is whether scoped wording conveys the approved guard, and which
limitations require affirmative explanation. A blanket rule that every absent
forbidden assertion satisfies every qualification would also be wrong.

Compound qualifications add another ambiguity. In the training-split comparison,
the answer explicitly counts canopy image pairs and heater images. The judge
still fails the qualification for not explicitly saying these are different
counting units or addressing independence after augmentation. It also demands
a disclaimer against common-benchmark ranking even though the answer reports
different datasets' split proportions. For localization outputs, it demands an
explicit different-task disclaimer despite distinct output descriptions.
The owner must decide which omitted limitations matter and assess every part
of a compound qualification. The sampling packet preserves those requirements
unchanged and lets the owner flag ambiguity as UNCERTAIN.

All nine cross-document questions fail the all-qualifications metric in each
configuration. That aggregate shows a systemic criterion problem, but does not
prove all those answers preserve every qualification. Only four answered
cross-document responses were in the independent audit.

## Citation failures and unresolved support

The archive distinguishes three checks: valid citation IDs, each citation's
partial support, and the whole citation set's support for every section claim.
An irrelevant extra citation fails even if another citation supports the answer.
Each configuration has four answered cases with at least one unsupported citation.
Those are answer failures under the saved rubric, not established judge errors.
The audited determinate citation outcomes agree on 17/17.

Two effective citation-support outcomes are unresolved despite raw positive
semantic judgments. The verifier requires quotes to be verbatim visible text:

- Qwen 16k, moving-signal addition: the quoted `Δt` uses Greek capital delta,
  while the passage has `∆t`, the increment symbol. The charge-transfer passage
  otherwise matches. The independent audit accepts support, but the scorer
  retains an unknown because its exact-quote receipt fails.
- Qwen 12k, training-computer comparison: the quote substitutes `Intel core`
  for the visible `Intel®core`. The hardware assertion is present, but the
  modified quotation does not verify it. This case was outside the audit sample.

These are character substitutions in evidence receipts, not evidence that the
passage lacked the stated content. Broadly relaxing quote verification could
also accept invented evidence; any fix belongs in calibration and must preserve
that safeguard. The old formula omissions are a separate source limitation.
Do not silently substitute today's readable formulas into an archived judgment.

Calibration also includes determinate citation failures where a fragment does
not establish a Gaussian-blur claim, and where a passage describes a comparison
to be performed while the answer states that it was performed. These exercise
entailment and temporal scope, rather than citation-ID membership alone.

## What the archive cannot establish

Claim-completion agreement is promising on the sampled answers, but measures
coverage, not independent evidence entailment for every required claim. Citation
support supplies the evidence check. Neither 18/18 nor 17/17 establishes broad
judge reliability, especially without observed error examples in that audit.

All forbidden-assertion outcomes are negative, so agreement alone cannot show
that the judge detects an actual violation. If human grades also contain only
acceptable answers, kappa is undefined and this judgment type cannot meet the
requested reliability bar from these archives alone.

Abstention and ID checks are deterministic. Across the full study there are 14,
7, 1 and 0 false abstentions on answerable questions for TF-IDF four, Qwen four,
Qwen 12k and Qwen 16k. The TF-IDF unrelated `no_matches` case is safe behavior but
does not satisfy the specified generated-abstention outcome. It must not be
relabeled to improve agreement. No negative answer invents a requested result.

The prepared sample addresses the old audit's lack of failing examples by
stratifying on archived outcomes, within the limits documented in the review
README. It supplies no new labels and no human ground truth yet. Current-corpus
answer generation and a default-budget decision remain pending owner grading.
