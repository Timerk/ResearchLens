# Archived judge against owner calibration grades

Step 1 uses only the 30 committed calibration grades. It does not read the
sealed validation files or the untracked complete grading drafts.

| Judgment type | Accuracy, all six items | Cohen's kappa | Unknown predictions |
| --- | --- | --- | --- |
| Required claim | 6/6, 100% | 1.0 | 0 |
| Qualification | 2/6, 33.3% | 0.0 | 0 |
| Forbidden claim | 6/6, 100% | Undefined | 0 |
| Abstention | 6/6, 100% | 1.0 | 0 |
| Citation | 2/6, 33.3% | 0.0 | 2 |

There are no UNCERTAIN owner verdicts. The grading rules reserve UNCERTAIN for
ambiguous requirements or missing adjudication evidence. It is not converted
into PASS or FAIL. Any UNCERTAIN owner grade or unknown judge prediction receives
no agreement credit in the all-item accuracy. Cohen's kappa uses only decidable
binary pairs. Counts and exclusions remain explicit. For citations, the binary
comparison is 2/4, 50%; the required all-item accuracy is 2/6.

Forbidden-claim kappa is undefined because both raters assign only PASS. Perfect
agreement in that stratum does not certify violation detection. Only required
claims and abstention meet both numeric thresholds on this calibration sample.
Calibration thresholds are diagnostic, not validation acceptance.

The baseline uses the frozen sample key's effective #16 predictions, including
the original deterministic status and evidence-quote checks. It does not make
paid calls or reinterpret the archived scores. The JSON records hashes,
confusion counts, both accuracy denominators and the uncertainty policy.

Reproduce from the repository root into a new output file:

```powershell
rtk proxy uv run --directory backend python -m researchlens.answer_judge_review --output ../evaluation/runs/calibration-baseline-replay.json
```
