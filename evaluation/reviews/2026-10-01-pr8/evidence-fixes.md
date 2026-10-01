# Development evidence fixes

Implemented on 2026-10-01 by Codex / GPT-6.1-Sol, medium reasoning, as an AI implementer.
This is not human approval. Evidence labels remain `unreviewed`, with null reviewer/date.

The preserved [evidence audit](evidence-review.md) and [JSON audit](evidence-review.json)
reviewed 36 cases, 83 groups, 111 alternatives and 114 existing span occurrences.
Their input label hash was
`fc04f09f169c35d5d22173ef67246759ba9495a7a0e707635a0765391268a59e`.
The revised file has 92 groups, 140 alternatives and 165 exact span occurrences across
the same 36 answerable cases. Twenty-five cases changed. All 14 negatives remain
unlabeled and unscored. The three dataset/corpus/passage pins are unchanged.

[evidence-fixes.json](evidence-fixes.json) records input/output hashes, audit-file
hashes, all 41 recommendation decisions, changed groups and new requirement types.
The output label file hash is
`f2fab94e1af336af0ee8e65ff7aadb1c0d7e129ba7a0117c34adc42fda4e4019`.

## Substantive fixes

| Finding | Correction |
| --- | --- |
| F01 | Stage two requires normal and artificially defective sample types. p8/p46 and the split abstract supply explicit alternatives. Removed artificial-only/clean-target options from this requirement. Clean targets remain required in the separate question that actually asks for them. |
| F02 | Red/green evidence now includes the forward/backward ordered antecedent in p38[168:479]. Blue uses only the averaging clause. |
| F03 | All dynamic-sigma options now include Gaussian parameter identity. Added weighting-spread and fixed 11-by-11 footprint groups. XML confirms sigma changes and distinguishes patch dimensions. No numeric k or changing-footprint claim was invented. |
| F04 | Complete coverage requires both p41 and the inconsistent p46 statement. p46 remains a valid P5/FSPPF alternative, but cannot replace P3/P4 AMFF evidence. No figure passage ID was created. |
| F05 | Added the excluded-data-transmission efficiency argument and the fixed-line-frequency experimental boundary as complementary required evidence. |
| F06 | Expanded CFPN evidence to include stripe identity and added the explicit incomplete-CDS qualification. |
| F07 | ImageNet and transferred-classifier input evidence include ResNet-50/Inception V3 identity. Removed the self-built p25 input alternative. Repaired p29 with named-model context instead of keeping it as a standalone architecture claim. |
| F08 | AW-SSIM comparison includes standard multiplication, AW addition, explicit constant component weights and unchanged component calculations. Weighting-priority background is not accepted as constant-weight evidence. |
| F09 | Charge-transfer evidence includes the moving object/image antecedent, with a valid p8 stage-accumulation alternative. Ideal square-root scaling evidence remains unchanged. |
| F10 | Added one-view outline visibility, experimental-versus-proposed containment and residual-localization purpose as factual qualifications. |
| F11 | Restored backward-lighting, theta-phase, structured-image processing and bright-field referents. Preprocessing uses explicit p29 modality scope with p22 operations. |
| F12 | Both detector feature-extraction alternatives now include fusion and detection purpose. p41 uses complementary spans that omit optional FSPPF architecture detail. |
| F13 | Shortened crop/augmentation, RGB and ADGA edge spans; narrowed manual-adjustment and oblique-illumination descriptions to match their facts. All three original AND structures remain intact. |
| F14 | Added checked introduction, abstract, architecture and conclusion alternatives where each option supplies the full group. Conservatively excluded generic residual-method text as a standalone implementation claim. |

## Decisions that differ from the proposals

- The new painted-classifier introduction alternative stops after the model names,
  without requiring optional promised performance benefits.
- p16 alone names structured illumination but not deflectometry. For the group that
  explicitly requires deflectometry, the new p44 option is sufficient; p16 was not
  added as an independent option or a redundant AND with existing p35 evidence.
- The p5 decision-level-fusion list fragment now includes the study/task antecedent.
- Structured preprocessing uses p29 scope plus p22 operations. The generic
  `Afterwards` fragment alone does not name the processed modality.
- The p29 image-size alternative retains explicit p26 model identity. p25's self-built
  model size is not evidence for the transferred classifier pair.
- Gaussian increment evidence in p32 also includes p30 Gaussian identity. Fixed
  footprint and weighting spread are required factual context, not invented formulas.
- The optional metrics dataset-scope proposal remains background for a reasoning
  limitation, not a required metric-definition group. No literal passage proves the
  absence of a direct performance ranking.
- The complementary weighting-priority proposal is background only. It cannot replace
  p26's constant-weight statement, and adding it as a redundant AND would impose an
  unnecessary requirement.
- The generic p6 residual-method introduction was not added as a standalone alternative
  for this implementation's localization result. The method-specific p40 statement
  remains sufficient; a p6-plus-p40 alternative would add no necessary fact. The p6
  residual-purpose and partial-reconstruction statements do supply complementary
  qualification evidence for the skip-connection question.

## Source checks and preservation

Checked full canonical source passages around the proposed fragments, development
question claims/qualifications, and original XML where symbol identity or source
inconsistency matters. All four original XML checksums match the pinned manifest and
attribution. The autoencoder XML identifies sigma, a fixed 11-by-11 window, PH/PW
patch dimensions and symbolic k without a numeric value. The canopy XML independently
confirms the p41/p46 conflict. The Figure 8 Chrome check remains the preserved reviewer's
visual audit; this implementation does not claim a new image inspection.

Approved datasets, held-out freeze, corpus/extraction, original question-review files,
human approval archive and both input evidence-review files were preserved byte-for-byte.
The supplied audit files use CRLF. Specific Git attributes disable newline conversion
for those two files so their recorded byte hashes remain valid on Windows and Linux.
Relabeling used source evidence only. No held-out retrieval, model failure inspection,
settings tuning, model download, answer generation or paid call informed these fixes.

The repository validator checks every revised quote, half-open Unicode offset, source
identity and pin. Focused regressions check that partial evidence fails for scoped
efficiency, AMFF disagreement, Gaussian footprint, classifier identity and constant
weights. Fresh-process TF-IDF diagnostics may exercise the revised contract on
development only; they are unapproved-label tooling checks, not model-quality evidence.
Old-label runs must not be compared with revised-label runs because their contracts differ.

Genuine human review of the revised evidence groups remains required before approval
and model/settings selection. The owner-approved questions do not approve new evidence
annotations. Keep held-out questions and their freeze untouched.
