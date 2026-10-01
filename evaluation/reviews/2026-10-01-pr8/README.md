# PR 8 question and expectation review

Reviewed 2026-10-01 by **Codex / GPT-6.1-Sol, AI source reviewer** against
PR [8](https://github.com/Timerk/ResearchLens/pull/8), input commit `7c096fc`.
Approval is the named AI reviewer's decision, requested by the user. It is **not
human scientific sign-off**. No retrieval rankings, model failures, evaluation
run reports or model/settings selection informed these decisions.

All 100 input cases received a decision: 30 approved, 56 revised and approved,
14 rejected. The active datasets contain 50 development and 36 held-out cases.
The accepted held-out subset is frozen before model selection. Development
remains editable. Category balance was allowed to change rather than adding
replacement questions solely to restore counts.

| Record | Contents |
| --- | --- |
| [review.json](review.json) | Every decision, identity/date, support and absence notes, alternative/complementary passages, original-only evidence, source versions, figure URLs/checksums and exact input/output dataset hashes |
| [rejected-cases.json](rejected-cases.json) | All 14 original rejected cases, marked rejected with identity/date and reasons; excluded from runnable datasets |
| [technical development](../../datasets/technical-development.json) | 50 accepted cases with revised wording, expectations, relevance references and review provenance |
| [held-out](../../datasets/held-out.json) | 36 accepted, approved, frozen cases; its exact SHA-256 is in review.json |

## Material findings

| Case(s) | Finding and disposition |
| --- | --- |
| `hold-compare-ablation-results` | Rejected. Canopy Tables 3/5 give mAP50-95 0.669 versus 0.639: a 3.0-percentage-point decline, inconsistent with paragraph 55's 5.2%. Autoencoder Table 2 gives 86.7, 90.86, 95.60 and 98.89 under different loss/training configurations. Its paragraph 42's 4.16% is not an isolated AW-SSIM improvement; 4.16 points instead matches the first two table columns. The original expectation would turn conflicting prose into unqualified gold results. |
| `tech-amff-layers` | Revised and approved with scope: paragraph 41 and Figure 8 agree on P3/P4 AMFF and P5 FSPPF; paragraph 46 incorrectly says P3/P5 AMFF. The question now identifies the agreeing locations, and its qualifications acknowledge the conflict. |
| `hold-classification-versus-cycle` | Revised. Paragraph 41 gives classification below one second after model input; paragraph 29 schedules acquisition/display at five-second intervals. An interval is not a cycle duration. Paragraph 48 broadly calls the sequence below one second without an independent timing breakdown. The question now asks the two explicit quantities instead of requiring an unsupported whole-cycle interpretation. |
| `hold-production-scan-projection` | Revised. Table 5 separates experimental 23,400 Hz and 5 mm/s, with a calculated 1.12-hour eight-inch scan, from potential production settings of 608 kHz and 129 mm/s with three-minute scanning and a higher-power, shorter-wavelength source. Three minutes is not demonstrated prototype throughput. |
| `hold-subtracted-channel` | Revised. Prose reports a slight mAP decrease; original Tables 3/5 also support mAP50 0.979 to 0.977 and mAP50-95 0.691 to 0.684. Optional exact declines of 0.2/0.7 percentage points are acceptable, although omitted from the extraction. |
| `hold-compare-scratch-weakness` | Revised. Canopy prose rounds backward scratch AP to 23%; Table 4 gives AP50 23.3% and AP50-95 11.8%. Either source-grounded precision for AP50 is acceptable. Heater classification accuracy is a different metric. |
| `tech-changing-neighborhood` | Revised. Sigma changes the Gaussian's spread; the 11-by-11 footprint stays fixed. Describing changing window dimensions would alter the technical meaning. |
| `tech-stripe-frequencies` | Qualified. Retain the heater authors' reported Hz labels for the generated spatial patterns; do not silently infer temporal refresh rates or calibrated cycles/mm. |
| `hold-compare-task-specific-limits` | Qualified. The canopy transformer comparison also changes to rectangular boxes; it does not isolate attention complexity as the sole cause. Wafer defocus/depth-of-field limitations remain a separate optical result. |
| Missing-evidence cases | Checked full originals, including tables, mathematical markup and all figures. Replaced the wafer every-coating/million-scan and autoencoder universal-false-alarm guarantee traps with concrete missing measurements. Context references remain excluded from positive relevance scoring. |

## Overlap decisions

The rejected development cases are `tech-painted-paraphrase`,
`tech-autoencoder-paraphrase`, `tech-cfpn-subtraction`, `tech-compare-learning`,
`tech-compare-labels-versus-simulation`, `tech-compare-relative-motion`,
`tech-compare-noise-preprocessing`, `tech-compare-image-degradation`,
`tech-compare-light-control` and `tech-missing-riscv-runtime`.

Several simply recombined complete factual answers already tested elsewhere.
`tech-compare-image-degradation` also exposed the held-out moving-chart blur target.
`tech-compare-light-control` asked about canopy backlight properties while its
expectation instead named forward LEDs and switching; repairing the original target
would overlap the held-out panel-settings question.

The rejected held-out cases are `hold-paired-image-alignment`,
`hold-compare-ablation-results`, `hold-compare-pretrained-network-purpose` and
`hold-compare-optics-scale`. Their individual reasons are preserved in the archive.

Remaining comparisons require factual information from both papers and explicitly
avoid a shared-benchmark ranking. Some retain partial contextual overlap:
optical scattering, classifier input size, crop expansion, and PSL size occur in
more than one question, but the retained questions add different required targets
(optical cue, patch/crop distinction, transformation pipeline, or units/threshold
interpretation). These are correlated observations. Approval does not establish
statistical independence or eliminate all shared-paper familiarity across splits.

## Source and evidence scope

The four pinned originals are PMC11510794 (canopy), PMC11768589 (painted heaters),
PMC10934137 (TDI wafer microscopy), and PMC11121878 (two-stage autoencoder).
Review covered their full article prose, all 12 tables, mathematical markup,
figure captions, relevant back matter and all **38 publisher figure images**:
10 canopy, 10 heater, 11 wafer and 7 autoencoder figures. Downloaded figure assets
were inspected locally; their URLs and SHA-256 values are recorded without
rebundling the images. PDF downloads returned HTTP 403; original XML and matching
publisher figure assets provided the full review material. No supplementary-material
elements are declared in the pinned XML; this is not a claim that every external
repository or linked dataset was exhaustively inspected.

Missing-evidence findings concern the requested result in these papers, not its
absence throughout the literature. Nearby context and cited related work do not
prove absence. The review records the specific experiment/material scope checked
for every missing-evidence case and all four papers for unrelated questions.

Positive passage references include acceptable alternative and complementary
prose evidence. Some locations support only part of a multi-claim expectation;
the per-case notes state those limits. Context that does not support a required
answer claim is not added as a positive retrieval label. Tables/formulas/figures
omitted from the extraction are recorded under `original_evidence` or in notes,
without inventing retrievable passage IDs or PDF page numbers.

The existing passage-recall statistic is the fraction of listed relevant passages
retrieved; adding alternatives changes its denominator. It is not claim coverage,
answer correctness or a requirement to retrieve every alternative. First-relevant
rank/MRR recognize any listed positive passage, but neither verifies that all
required claims are supported. No scoring algorithm or retrieval setting was
changed during this review.

## Validation and freeze

All 75 backend tests passed, with the existing Starlette/httpx deprecation warning.
Metadata-only checks validate both splits against the unchanged corpus, original
versions and passage/XML locations. Tests verify the dataset hashes and the review
partition and retain draft/frozen approval guards without executing held-out
questions. Ruff lint, formatting and Git whitespace checks passed.
These checks establish structure and provenance, not scientific truth.

Use the recorded held-out output hash to identify this freeze. Changing questions,
expectations, references or dispositions requires a new version, source review and
freeze before model/settings selection. If held-out failures influence tuning,
retire this set and prepare fresh targets for subsequent quality claims.
