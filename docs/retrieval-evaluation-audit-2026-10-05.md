# Retrieval evaluation and visible-question alignment

The plateau combines real retrieval failures with a smaller evaluation-contract mismatch. The existing evaluator correctly reproduces the approved evidence-package score of **26/36, 72.2%**. It does not measure whether a generated answer answers the visible question correctly. Source-backed proposals recorded before inspecting cached outcomes would raise the incumbent to **28/36, 77.8%**, if approved. Seven unambiguous alternative additions alone leave it at 26/36. The two gains require judgments about question scope or contextual sufficiency.

The historical result remains 26/36. A separate, unresolved decision about how much causal explanation the shortcut question requires would yield 29/36 under a narrower contract. It was raised after replay and is recorded separately. None of these changes improves retrieval. The 29/36 target is not demonstrated under the approved contract, and no development percentage establishes generalization or answer accuracy.

This is an AI-assisted audit by Codex / GPT-6-Astra, with parallel source review and a separate scoring review. It is not independent human scientific review. The initial semantic reviews identified requested facts before classifying expectations; they were not blind to the existing annotations or the user's diagnostic summary. Reviewers did not read cached per-case rankings before recording the initial judgments. A later follow-up about shortcut explanations is explicitly separated below.

## Scope and reproducibility

On 2026-10-05, GitHub reported PR #9 open at `0542fb8aa1ac87b96d0e6b91320a48e2f4328889`, based on the open PR #8 branch at `f079ed1ad4c76c280d090c0b905fc23b0af3074a`. A separate worktree and branch, `audit/question-evidence-alignment-2026-10-05`, were created from that exact PR #9 commit. Existing worktrees and unrelated changes were preserved. Neither PR was merged or updated.

The audit preserves all 21 tracked files under the protected corpus, dataset, label and review paths. Their byte hashes are recorded in [input-audit.json](evaluation-audit-2026-10-05/input-audit.json). The application still uses TF-IDF by default. Canonical text, 204 passage IDs, citations, four-passage output and existing question/context limits are unchanged. No paid API, answer generation, model inference or model download was used.

Frozen held-out questions were not inspected or executed. Byte-hash validation was used. There was one boundary incident: an early schema probe called `list()` on the mixed rejection archive, which is a list rather than a mapping, and accidentally emitted rejected held-out draft records. The probe was stopped and the exposure was disclosed. Those records were not used for corrections. This session must not be described as having zero exposure to held-out-related text. Subsequent archive reads filtered to development entries before output; some historical development notes also refer to reserved topics. No claim about held-out performance or semantic split independence is made.

The new review checked indexed prose against pinned original XML, including relevant tables, mathematical text and figure captions. External figure image pixels were not re-inspected. Prior development review entries record broader figure inspection; this audit does not claim to have repeated it. In particular, the p41/p46 architecture contradiction is directly verifiable in prose, while fresh visual verification of Figure 8 remains outstanding. The absent `docs/retrieval-evaluation-audit-2026-10-02.md` supplied no prior findings.

## Case-level answerability

Every development case has a question-first requested-fact analysis, requirement classification and source judgment in these review artifacts:

| Cases | Count | Review and exact-source record |
| --- | ---: | --- |
| Canopy and heater single-paper positives | 16 | [Review](evaluation-audit-2026-10-05/canopy-heater.md), [JSON](evaluation-audit-2026-10-05/canopy-heater.json) |
| Wafer and autoencoder single-paper positives | 11 | [Review](evaluation-audit-2026-10-05/wafer-autoencoder.md), [JSON](evaluation-audit-2026-10-05/wafer-autoencoder.json) |
| Cross-paper comparisons | 9 | [Review](evaluation-audit-2026-10-05/comparisons-negatives.md), [JSON](evaluation-audit-2026-10-05/comparisons-negatives.json) |
| Unrelated and missing-evidence negatives | 14 | Same comparison/negative artifacts, separately classified and unscored |

All 36 positive questions have support in the indexed passages for their visible, source-attributed requests. None was found to require only omitted original material, and none was found unsupported as phrased. This does not independently prove the paper's scientific claims. One case, `tech-amff-layers`, has a definite internal source conflict. Its explicitly scoped p41 account is answerable, but the paper's actual architecture cannot be unambiguously resolved from its conflicting statements. The changing-neighborhood prose also has imprecise window terminology; the detailed case review retains the distinction between Gaussian spread and fixed footprint rather than inventing a resolution.

The 14 negatives remain unsupported document-only requests. Seven are unrelated to these papers. Seven request absent quantities, validation settings or comparisons. Hardware specifications do not supply joules per heater or a matched CPU benchmark; PSL wafer particles do not establish malignant-cell sensitivity; MVTec results do not establish CT patient accuracy; mAP50-95 is not a confidence interval. Contextual reference passages are not positive relevance labels or proofs of absence. These negatives contribute neither successes nor failures to the 36-case positive completeness denominator. Their generated-answer abstention behavior remains unmeasured.

## Confirmed findings and review judgments

The historical score is an accurate measure of whether all approved groups were retrieved. Treating it as generated-answer accuracy, or as the unique minimal evidence needed for every visible question, would be inaccurate.

The following facts are directly supported by the sources and implementation:

- All 165 approved span occurrences, representing 138 distinct ranges, match the canonical text, source identity and offsets. No stale span, wrong-source reference or arithmetic defect was found in this replay.
- The glass-paraphrase dataset entry contains a duplicated qualification. Deduplicating it does not change retrieval scores.
- Seven sufficient alternatives are absent from the approved group set. They cover the painted-model comparator/name passages, wafer efficiency conditions, autoencoder abstract weight transfer, the TDI direction example, shortcut residual purpose and canopy feature-fusion identity. Their exact ranges and rationale are in [proposed-revisions.json](evaluation-audit-2026-10-05/proposed-revisions.json). Missing alternatives are an incompleteness of the annotations, which already describe themselves as conservative and non-exhaustive.
- Some complementary sets demand redundant context. Wafer p14:w180 itself states both excluded transmission time and unchanged line frequency, so p16 is not necessary for that specific qualification. Canopy p5:w0 names the expanded ADMF-Net model and feature-level fusion, so requiring p40 alongside it is unnecessary.
- One evaluation README sentence says MRR uses original reference IDs, while the current implementation uses approved evidence IDs when labels are supplied. The earlier alternatives section documents the implemented behavior correctly. Historical original-reference recall remains a separate metric.

The two user examples require a contract decision, rather than a claim that their scientific qualifications are false:

| Case | Requested answer | Proposed treatment |
| --- | --- | --- |
| `tech-wafer-exact` | Which TDI-stage and CFPN changes improve SNR | Keep increased stages and reduced CFPN mandatory. Efficiency is an additional claim. If made, require fixed line frequency and excluded transmission time. Remove that mandatory evidence group only together with the corresponding unconditional expected-answer clause. |
| `tech-amff-layers` | What p41 and Figure 8 report about AMFF/FSPPF/head | p41 says AMFF at P3/P4, FSPPF at P5, then OBB detection. p46 instead refers to P3/P5 AMFF outputs. An answer explicitly attributed to p41 can report that account; an unqualified architecture assertion should disclose the conflict. Alternatively ask explicitly about the conflict and retain the whole package. |

The incumbent already retrieves both AMFF passages, so changing that qualification does not increase its complete-case count. Other cached configurations can change; the replay preserves those differences.

`tech-adaptive-binarization` is a contextual-sufficiency judgment. Heater p22 contains RGB-to-grayscale conversion, adaptive binarization and an explicit bright-field exclusion. In the visible structured-illumination question, the complete paragraph can support the requested contrast. The current labels also demand p29 to name the structured mode. Accepting p22 alone is a reasonable proposed alternative, but the owner may retain the stricter antecedent requirement. It is reported separately from unambiguous additions.

Other optional detail includes the eightfold augmentation example and manual annotation-file checks. Moving these out of mandatory answer content does not change whole-passage completeness because the requested facts occupy the same passages. The proposed-versus-tested daylight tunnel distinction remains necessary if an enclosure is mentioned. Its mixed group also contains the required uncontrolled-light fact, so it is retained in executable replay; a future rubric should narrow it rather than delete both facts.

Reasonable conservative choices remain. A heater crop size from the scratch-built-network section cannot stand in for the transferred classifiers' size. Stripe phase retains its symbol-definition context. A general residual-method introduction is not automatically proof of the proposed model's output. Multiple spans in one canonical passage consume one output slot, not multiple slots. Source-specific attribution and necessary scientific qualifications must not be removed just because they are difficult to retrieve.

## Scoring reproduction and sensitivity

[The scoring audit](evaluation-audit-2026-10-05/scoring.md) explains the implementation and [replay-results.json](evaluation-audit-2026-10-05/replay-results.json) retains old/new per-case results, changed cases, remaining failures and input hashes. The replay calls the existing `ranking_metrics`, `evidence_coverage`, `cutoff_summary`, `minimal_supports` and context preparation code. It introduces no replacement scoring formula.

All 31 cached configurations from the retrieval-improvement and Vulkan archives reproduced at four passages: 1,550 case rankings. The available original raw runs also reproduced 6,150 saved case/cutoff comparisons with zero mismatches. These are repeated configurations on the same development questions, not independent observations. Saved latency is historical; replay latency is not a new model benchmark.

For the incumbent BGE-M3 to BGE-reranker-v2-m3 over 20 candidates:

| Measure at four passages | Approved result | Interpretation |
| --- | ---: | --- |
| Original reference-passage recall | 71.660% | Mean recall of original reference IDs, including interchangeable references |
| Any approved evidence hit | 33/36, 91.7% | At least one support fragment, not necessarily one whole fact |
| MRR | 0.8333 | Rank of the first approved support fragment |
| Approved group coverage | 80.278% | Mean per-question proportion of groups covered |
| Complete approved evidence | 26/36, 72.2% | Every group has one fully present alternative |
| Generated-answer accuracy | Unmeasured | No answers generated or judged |

Original reference recall has a corpus-wide four-slot ceiling of 96.040%, even with perfect selection. Four cases list more than four reference IDs. For example, the fusion comparison lists 13. Adding interchangeable references can lower this metric without making answering harder. Its denominator is preserved in every scenario; alternative-aware group coverage is not silently substituted for historical recall.

The corpus minimum-support distribution remains 18 questions needing one passage, 16 needing two and two needing three. That establishes feasibility under the labels, not semantic validity. True four-slot oracles remain 31/36 for BGE20 and 34/36 for Qwen40, including under the initial proposal set. `retrieval_analysis.analyze_run` treats the run's returned IDs as its candidate universe; on a k=4 output alone, its missing-candidate label cannot distinguish an upstream top-20 failure. This audit uses the separately archived candidate pools for that distinction.

The initial 13-action proposal set is separate from approved files. Each action has an individual replay, plus grouped scenarios:

| Scenario on the identical incumbent ranking | Complete cases | Change |
| --- | ---: | --- |
| Original approved package | 26/36 | Historical baseline |
| Seven unambiguous alternative additions only | 26/36 | No incumbent case becomes complete |
| Question-scope proposals only | 27/36 | `tech-wafer-exact` |
| Contextual p22 alternative only | 27/36 | `tech-adaptive-binarization` |
| Combined initial proposals | 28/36 | Both cases; no complete case is lost |

The combined scenario has 83.056% mean group coverage. Original reference recall, any-hit and MRR remain unchanged for this incumbent. TF-IDF changes from 15 to 16 complete cases, Qwen3-4B dense from 24 to 27, and Qwen3-4B plus BGE40 from 25 to 27 under the same proposals. These counterfactual labels do not establish a newly selected deployable configuration.

The gained contexts can support accurate answers to their visible questions under the proposed interpretations. They are not observed correct generated answers. The wafer context supports a qualitative SNR answer, not an unqualified throughput claim. The adaptive-binarization context supports the operations and bright-field exclusion only if the contextual antecedent is accepted.

The initial combined proposal still leaves these eight cases incomplete:

| Case | Missing requested support under retained requirements | Location of the problem |
| --- | --- | --- |
| `tech-glass-paraphrase` | Lighting-specific strengths and omissions | Support exists in BGE20; selection misses it |
| `tech-compare-fusion` | Canopy illumination and data/feature fusion | Output contains only heater passages; BGE20 has both sources' support |
| `tech-stripe-frequencies` | Phase-definition context | Support exists in BGE20; selection misses it |
| `tech-both-checks-clean` | Both-OK acceptance and subsequent inspection workflow | Complete support absent from BGE20 |
| `tech-moving-signal-addition` | The moving-signal accumulation explanation | Complete support absent from BGE20 |
| `tech-too-many-shortcuts` | Explicit residual-purpose explanation | Complete support absent from BGE20 under the retained fuller rubric; see adjudication below |
| `tech-changing-neighborhood` | Gaussian schedule, spread and footprint explanation | Complete support absent from BGE20 |
| `tech-compare-localization-outputs` | OBB output and method-specific residual localization | Complete support absent from BGE20 |

## Remaining judgment about explanatory depth

After reviewing the failure list, the primary auditor asked two source reviewers, still without cached outcomes, to reconsider `tech-too-many-shortcuts`. Both distinguished a concise empirical reason from a fuller mechanism explanation. The narrow answer, "All-layer shortcuts partly reconstructed defective regions; two selected connections gave the best results in the authors' experiments," is supported by p16. Explaining how copied defects disappear from a residual requires additional evidence.

This qualifies the initial review's claim that explicit residual explanation is necessary for every accurate answer to the visible why-question. It is an unresolved rubric-depth decision. p16 plus p17 must not be relabeled as support for the unchanged residual-discrimination statement, which they do not state. The initial proposal snapshot remains unchanged. [The post-replay adjudication](evaluation-audit-2026-10-05/post-replay-adjudication.md) and [separate sensitivity record](evaluation-audit-2026-10-05/shortcut-sensitivity.json) expose the consequences of accepting the narrower scope.

The separate exploratory calculation yields 29/36, 80.6%, when that narrow empirical answer is accepted together with the initial proposals. Only the shortcut case changes; seven cases remain incomplete. The corresponding hypothetical BGE20 ceiling rises to 32/36, while Qwen40 stays at 34/36. This later, outcome-informed question must not be silently counted as another confirmed annotation defect or used to announce that the original retrieval target has been met. Its main lesson is that the apparent crossing of 80% depends on a disputed evaluation choice.

## Dataset realism and uncertainty

The development set has 14 exact-terminology questions, 13 paraphrases, nine cross-paper comparisons, seven unrelated negatives and seven missing-evidence negatives. The questions plausibly exercise source lookup, methods comparison and document-only abstention. They are curated paper-reading tasks rather than a measured sample of user traffic. Exact annotation-tool versions and a question naming paragraph 41 are useful navigation diagnostics, but their frequency among intended user needs is unknown. Recipes and exchange rates are easy out-of-domain controls; biological and CT questions are strong domain shifts. Energy, remaining service life and uncertainty questions are more plausible nearby evidence-gap requests. None supplies a production prevalence estimate.

Positive question incidence is 16 for canopy, 13 for heaters, six for wafers and ten for autoencoders; cross-paper questions count toward both papers. Twenty-eight of 630 positive-case pairs share at least one approved support passage. Shared passages do not necessarily mean identical factual targets, and non-overlapping passages can still concern the same mechanism. Repeated training, illumination and augmentation facts and four shared papers make the observations dependent. Treating 36 questions as independent samples from a broad scientific-QA population would understate uncertainty.

One question changes completeness by 2.778 percentage points. Moving from 26 to the target 29 is three cases. The reviewable scope choices are large enough to affect that conclusion without any retrieval change. Extensive tuning on this small development set also makes its best observed result optimistic as an estimate of new-user performance. An 80% development threshold is a local acceptance rule, not a demonstrated generalization guarantee.

## Proposed decision and future contract

Keep the approved dataset, labels, archives, freeze and historical results unchanged. Review [the separate proposal artifact](evaluation-audit-2026-10-05/proposed-revisions.json) for factual sufficiency and visible-question scope before adopting any effect on scores. Resolve the contextual binarization and explanatory-depth choices explicitly. Record which facts are mandatory, which qualify additional claims, and which are supplementary. Where the richer package is the intended task, rewrite the visible question to request it instead of leaving an implicit demand.

If adopted, publish a newly versioned development question/label contract and preserve metrics-version-2 runs with their original label hash. Apply paired corrections to expected claims and evidence groups, obtain owner approval with truthful provenance, and replay all cached configurations using the same evaluator. Keep original-reference recall unchanged. Keep requested-evidence completeness distinct from full approved-package completeness and from future generated-answer correctness, citation support and abstention review. Do not pass different label versions to the ordinary controlled-comparison report as if they were the same experiment.

No corpus or extraction change is required to answer the current visible development questions. Figures, numerical tables and formulas are still important limitations for broader user questions and resolving original-source ambiguity. Any future expansion should be a separate extraction proposal: version the corpus, preserve or explicitly remap stable IDs, rebuild all passage/embedding artifacts, re-anchor exact evidence offsets and citations, regenerate identity hashes, and retain the old artifacts/results. A held-out remapping or refreeze would need a separately controlled process, without using its contents to tune this investigation.

Before making a general performance claim, obtain an independent review of the question contract and evaluate representative user needs across additional papers. The frozen held-out set remains reserved. The present audit establishes that annotations and scoring interpretation contribute to the apparent plateau, while substantial evidence-retrieval failures remain.

## Verification

The [verification record](evaluation-audit-2026-10-05/verification.json) checks all 50 case IDs, every original claim/qualification/prohibition index, 174 audit quote occurrences and all 21 protected byte hashes. Existing evidence tests passed, 42 tests, with the CLI test deselected because it would parse the frozen other split. The selected hash-only held-out check was allowed and passed. Ruff lint and format checks pass for the audit scripts, local report links resolve, and generated files have no trailing whitespace. No credential patterns were found in the new artifacts.

Run from this worktree with the existing project environment. These scripts do not read `.env` or invoke models:

```powershell
rtk python docs/evaluation-audit-2026-10-05/verify-audit.py
rtk python docs/evaluation-audit-2026-10-05/inspect-inputs.py
rtk python docs/evaluation-audit-2026-10-05/assemble-proposals.py
rtk python docs/evaluation-audit-2026-10-05/replay.py --help
```

The replay's full commands, archive pins, raw-run verification option and limitations are documented in [scoring.md](evaluation-audit-2026-10-05/scoring.md). Use a Python environment with the repository dependencies. RTK was unavailable during this audit, so shell commands used a local pass-through wrapper as permitted by the README.
