# Judge revision using calibration only

Step 2 revises the rubric using only `calibration-grades.csv`. The sealed review
directory and the untracked complete grading drafts were not opened.

The model remains `gpt-6-luna` with medium reasoning and a 4,000-token output cap.
The structured judgment schema is unchanged. Version two clarifies that scoped
wording can preserve a qualification without a separate disclaimer; missing
substantive limitations still fail. It separates an individual citation's
partial support from the cited set's obligation to support every section claim.

Evidence receipts first use exact substring checks. A narrow fallback normalizes
whitespace, registered trademark marks and the two time-variable spellings
`∆t` and `Δt`. It does not rewrite numbers, units, words, negation or arbitrary
symbols. Missing or invented quotes remain unknown. Tests exercise altered values,
units, negation and invented text. Legacy scoring remains available for exact
replay of #16, including its original unknown receipts.

The guarded `answer-plan --review-half calibration` estimated a maximum reservation
of $0.0952104 for 23 judge calls and zero generation calls. `answer-run` used the
matching approval hash, `--max-cost-usd 3` and a persistent shared study ledger.
There were no retries. Calls with known usage release only the unused portion
of their conservative reservation. Unknown or failed calls retain the full
reservation. This ledger also covers the later validation and generation stages.

| Type | Revised accuracy | Revised kappa | Archived accuracy | Archived kappa |
| --- | --- | --- | --- | --- |
| Required claim | 6/6, 100% | 1.0 | 6/6, 100% | 1.0 |
| Qualification | 6/6, 100% | Undefined | 2/6, 33.3% | 0.0 |
| Forbidden claim | 6/6, 100% | Undefined | 6/6, 100% | Undefined |
| Abstention | 6/6, 100% | 1.0 | 6/6, 100% | 1.0 |
| Citation | 6/6, 100% | Undefined | 2/6, 33.3% | 0.0 |

All revised predictions are decidable, and all calibration owner grades are
decidable. For the three undefined kappas, both raters assign only PASS. The
numeric acceptance bar is not certified for those types despite 100% agreement.
These calibration results guide revision; they are not validation results.

The owner reports independent pre-adjudication grading agreement of 58/60,
96.7%, as a realistic ceiling for automated agreement. The owner adopted Codex's
verdicts in the two disagreements. Their IDs and pre-adjudication grades are
unavailable, so their effect cannot be separated. Final grades may favor a
judge from the same model family. Report this limitation with validation results.

The revision also wires BGE-M3 into the guarded answer runner for the planned
five-configuration development comparison. It does not change retrieval,
generation instructions, datasets, labels, corpus or application defaults.
The next commit records the freeze and decision rule before validation is opened.
