# Frozen judge and context decision rule

Step 3 freezes the calibrated judge before validation is opened. The manifest
contains its complete prompt, rubric, model ID, structured schema, deterministic
checks, uncertainty policy and implementation hashes. The generation prompt is
unchanged. The six-item calibration results are not used as validation acceptance.

The primary context comparison is Qwen3-4B 12k versus Qwen3-4B four passages.
Holding retrieval fixed tests the existing full tier's 12k budget. Promotion
requires more complete required claims over the same 36 answerable questions,
a two-sided paired exact McNemar p < 0.05, no increase in unsupported or forbidden
claims over all 50 cases, and no worse correct generated abstention over the
14 negatives. Other configuration comparisons are descriptive diagnostics;
they do not replace a failed primary test after results are known.

Only judgment types meeting both validation thresholds, kappa >= 0.6 and all-item
agreement >= 80%, enter decision metrics. Unknowns remain visible. Undefined
kappa does not qualify. Excluded types do not silently satisfy a safety guard.
If unsupported or forbidden claims cannot be measured reliably, the AND rule
cannot establish promotion and current defaults remain. Qualifications are
reported separately and cannot distort the required-claim endpoint through
an uncertified composite.

If the rule passes, the existing full/standard/light/minimal character budgets
become the per-tier application policy. The explicit no-tier fallback remains
TF-IDF four, because this experiment does not generate a TF-IDF 16k comparison.
If the rule fails or cannot be assessed, defaults remain unchanged.

All Phase 2 paid calls share a persistent $3 ledger. Development only; no new
retrieval or generation on held-out questions. Inputs and sample membership stay
unchanged. After this freeze commit, verify the sealed validation CSV hash against
`owner-review.md`, judge the validation half once, and publish agreement and
unreliable-type exclusions. Do not revise the judge after seeing those grades.
