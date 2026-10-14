# Owner review of answer-judge results

Review status: human reviewed. Reviewer: project owner. Confirmed 2026-10-15.

The owner reviewed and graded all 60 items and confirmed the final verdicts.
The draft was prepared with Codex assistance; the owner approved the final
judgments and authorized this review record.

## Committed calibration results

[calibration-grades.csv](calibration-grades.csv) contains the 30 approved
calibration verdicts and notes, using the frozen membership in
[scoring-key.json](scoring-key.json). Each of the five judgment types has six
items. Item IDs, answer text, source passages, and split membership are unchanged.
The pristine [owner-grading.md](owner-grading.md) remains unchanged.

For G005, the final calibration verdict is PASS. The cited fragment supports the
smoother-blending outcome under the single-citation rule, which requires support
for at least one substantive part of the section.

## Sealed validation results

The 30 validation verdicts and notes, the complete 60-item CSV, and the completed
packet are archived locally under owner-review-sealed/2026-10-14-answer-judge
in the repository's common Git directory. Resolve that directory with
git rev-parse --git-common-dir. The archive files are owner-grades.csv,
validation-grades.csv, and owner-grading-completed.md.

The archive is local to this repository installation and is not transferred
by a Git push or clone. Obtain the sealed files from the owner when needed.
Keep validation verdicts, notes, and comparisons closed during judge revision.
Open them only after recording the frozen prompt, rubric, model, schema, and
deterministic checks, then perform the single validation evaluation described in
[README.md](README.md).

## Integrity record

These hashes identify the approved files without exposing validation judgments:

- Pristine packet SHA-256: b1594cf0cb6b2ca5a12335343cbafa4e98e4a94a503f3163f621b22b3d51007b
- Complete reviewed CSV SHA-256: a3f8a064c43ec724b17302ed3f04b30a73842493ab64cd6ee725310072cd626a
- Sealed validation CSV SHA-256: 6d1aa7682786e95bb5e58d415f2e8dbc09cefbeac9708970405adc7cbbe721e1

The scoring-key split was consulted only after grading and human confirmation,
to separate the approved results. Neither diagnosis.md nor the original papers
were consulted for this handoff.
