# Owner grading of the answer judge

Phase 1 is complete. The next action belongs to the owner. Grade only
[owner-grading.md](owner-grading.md), or return a CSV with `item_id,verdict,notes`.
Enter PASS, FAIL or UNCERTAIN for all 60 items and give a short reason.
Allow about 90-150 minutes. Do not read the scoring key, sampling summary,
diagnosis or previous audit before grading.

The packet contains each question, its approved requirement, the answer and the
exact cited visible passages from #16. Claim, qualification and forbidden-claim
items show the entire answer so omissions and contradictions elsewhere remain
visible. Citation items show the target section and its citation set. Section-free
responses have no cited passages. Source attribution is at the end of the packet.
Configuration names, judge verdicts, judge reasons, case IDs and half membership
are absent. The owner can grade this checkout without access to the raw archive.

## Sample and limitations

There are 12 items for each of five judgment types, six per half. Every type in
each half includes all four configurations. Each configuration contributes 15
items overall. All five development question cohorts appear in each half.
The 60 items cover 37 distinct questions. No question crosses halves, including
answers generated under different configurations. A question contributes at most
three items, and at most one item per type.

The archived independent audit's ten questions and both publicly documented
quote-validation problems are assigned to calibration. The remaining question
assignment uses a fixed hash seed. Integer constraints select a sample with at
least two passing and two failing decisions per type and half where both exist.
Both unresolved citation decisions appear in calibration. Both individual
citation support and collective section support appear in each half. The sample
also includes false abstention, correct negative abstention and the safe
`no_matches` response that is not a generated abstention.

These are individual judgments, not the previous audit's per-answer aggregates.
Claim coverage asks whether an approved claim is conveyed; evidence entailment
is assessed separately by the citation items. Status correctness is a
deterministic check of the approved answer/abstention expectation. Citation-ID
membership is also deterministic and is part of the citation rubric.

Some requested strata do not exist in #16:

- No forbidden-claim violations were predicted in any configuration. All 12
  forbidden-claim items therefore test predicted absence of a violation. They
  cannot establish sensitivity to actual violations. If the owner also grades
  every item PASS, Cohen's kappa is undefined, even with perfect agreement.
- All supplied citation IDs were valid. Invalid-ID detection has no natural
  failure examples here. Citation semantic failures are included.
- Qwen 16k has no incorrect response statuses, and Qwen 12k has only one.
  A complete configuration-by-type-by-outcome factorial sample is impossible.
- The two unresolved citation cases were already diagnosed publicly and remain
  in calibration. There are no untouched unresolved cases for validation.

Do not manufacture examples or change answers, questions, evidence, labels or
corpus to fill these gaps. Report unavailable strata and undefined kappa honestly.
Six validation items per type are a small diagnostic. The outcome-stratified
sample does not estimate full-run prevalence, and repeated questions across types
are not independent observations.

## Files for the evaluator

The following files reveal sampling or model outcomes. Keep them separate from
the owner's grading view:

- `scoring-key.json` pins item identity, half, configuration, target index,
  archived run hash and baseline prediction. PASS always means acceptable behavior;
  forbidden-claim assertion decisions are inverted. Single-citation predictions
  include the original scorer's verbatim-quote validation and conservative
  combination of duplicate subclaim decisions. Raw predictions are retained too.
- `sampling-summary.json` records pool and sample counts and replayed audit totals.
- `diagnosis.md` documents the archive findings, without treating the model audit
  as human ground truth.

The key pins the pristine packet's UTF-8 SHA-256. Preserve the pristine committed
packet and return grades in a copy or CSV. Sample identity and membership are
frozen by this commit. Do not rerun selection after seeing any owner verdicts.

## Boundary before Phase 2

On receipt, validate that all 60 IDs occur exactly once and verdicts are valid.
Use only calibration verdicts, notes and disagreements to revise the judge.
Keep validation verdicts and notes sealed. The current archived judge can be
measured on both halves, but seal its validation comparison until the judge is
frozen. Report that baseline beside the frozen judge's one validation evaluation.
Record the frozen prompt, rubric, model, schema and deterministic checks before
opening validation grades. Never tune on validation disagreements or rerun
validation after tuning.

Report agreement and Cohen's kappa separately for every judgment type and half,
with confusion counts, denominators and unresolved items. Unknown predictions or
UNCERTAIN human verdicts must remain visible; do not discard them to improve the
agreement percentage. Report kappa only for decidable binary pairs and label
undefined values. The requested acceptance bar is kappa >= 0.6 and agreement
>= 80% per type. A missing class or undefined kappa cannot certify that bar.

This phase makes no paid calls and does not improve or freeze the judge yet.
It does not generate answers, use held-out material or change application defaults.
The decision rule and current-corpus comparison belong after owner grading.

## Offline reproduction

The raw archive remains in local ignored storage. Its checksum is
`4ac385031e32826141aaa2b7c3072a883f0f2198aa605664697407f3554df9ea`.
Use the path in `evaluation/answer-quality-evidence-manifest.json`, or the same
archive in another worktree. From the repository root, with RTK on PATH:

```powershell
rtk proxy uv run --directory backend python -m researchlens.answer_grading --archive ABSOLUTE_ARCHIVE_PATH --output ../evaluation/runs/new-owner-grading-replay
```

The command verifies the compressed archive and each run/review hash, asserts
the development split, and reproduces all 200 archived score records before
sampling. It uses no corpus/index files and constructs no paid client. It refuses
to overwrite a grading packet. The fixed seed and hash-based objective make
selection repeatable in the recorded environment; the committed key is authoritative.
