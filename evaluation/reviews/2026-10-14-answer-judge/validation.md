# One-time frozen validation

Step 4 opened validation after freeze commit `4c6cc7e`. The common Git directory
was resolved with `git rev-parse --git-common-dir`. The sealed validation CSV's
SHA-256 matches `owner-review.md`:
`6d1aa7682786e95bb5e58d415f2e8dbc09cefbeac9708970405adc7cbbe721e1`.
The verified frozen contract hash is
`b6a56c854bb2c23657dd98dae3ed634904789a39a991bd46edf858f456bbec3f`.

The frozen judge made 22 guarded judge calls on existing development answers,
with no generation calls or retries. Plan hash:
`91a251a919026cbcc0886eed5a0b2d84e4a3133ed509f9fbd995f8ba41e16b9d`.
The archived baseline and frozen judge are compared against the same 30 grades
in `validation-results.json`. There was one validation evaluation. The prompt,
rubric, model, schema and deterministic scoring checks will not be revised.

| Type | Archived accuracy | Archived kappa | Frozen accuracy | Frozen kappa | Meets bar |
| --- | --- | --- | --- | --- | --- |
| Required claim | 5/6, 83.3% | 0.5714 | 6/6, 100% | 1.0 | Yes |
| Qualification | 2/6, 33.3% | 0.0 | 3/6, 50% | 0.0 | No |
| Forbidden claim | 6/6, 100% | Undefined | 6/6, 100% | Undefined | No |
| Abstention | 6/6, 100% | 1.0 | 6/6, 100% | 1.0 | Yes |
| Citation | 4/6, 66.7% | 0.0 | 6/6, 100% | Undefined | No |

The acceptance bar is kappa >= 0.6 AND all-item agreement >= 80% for each type.
The single UNCERTAIN owner verdict belongs to qualifications. It receives no
agreement credit in the six-item accuracy and is excluded from binary kappa.
Qualification agreement on decidable pairs is 3/5, 60%, with kappa 0.0. There
are no unknown frozen predictions. The unknown policy was registered before
validation and is unchanged.

Citation and forbidden-claim grades contain only PASS, and the frozen judge
also predicts only PASS. Their perfect observed agreement cannot establish
sensitivity to errors, and kappa is undefined. They therefore do not pass.
Qualifications still disagree and are unreliable. Exclude all three types
from decision metrics and the composite. Required claims and deterministic
abstention may be used for the new development comparison, with the limit that
six validation items per type do not establish reliability on future inputs.

The owner and Codex reported 58/60, 96.7%, pre-adjudication agreement as a realistic
automated-agreement ceiling. The owner adopted Codex's two disputed verdicts.
Their original grades and IDs are unavailable, so same-family bias cannot be
quantified or removed. This is human-approved grading with that limitation,
not an independent human-only reference or held-out answer study.

Current-corpus answers will still be generated for the five requested
configurations because two judgment types pass. The unavailable unsupported
and forbidden-claim endpoints cannot satisfy the pre-registered AND rule's
safety guards. They may be reported as uncertified diagnostics, but no absence
of violations can be claimed as calibrated evidence for promotion.
