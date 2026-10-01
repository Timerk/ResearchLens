# PR 8 evidence-group review

Reviewed 2026-10-01 by Codex / GPT-6.1-Sol, AI evidence reviewer, against commit `1e98076dd4ebd0c6fc57836961849879b3044ed2`.

The labels need revisions before approval or model selection. All 36 answerable development cases, 83 groups and 111 alternatives were reviewed. All 114 span occurrences, representing 98 distinct spans, match the canonical text exactly. Dataset, corpus and shared-passage pins also match. These structural successes do not resolve missing support, context or qualifications.

This review records findings and proposed exact spans. It does not modify or approve the labels, approved question datasets, held-out freeze or historical question reviews. The 14 development negatives remain unlabeled. No retrieval results, model failures, model selection or held-out rankings informed the review.

| Requested check | Result |
| --- | --- |
| Requirements | Claim indices are all present, but several factual qualifications and parts of composite claims are not required by the groups. Some descriptions also impose extra or mismatched facts. |
| Support | Most alternatives are sound. One stage-two option does not support its group, one classifier-size option has the wrong model scope, and several fragments need explicit context. All three existing multi-span AND options are sufficient for their described facts. |
| Alternatives | The list is incomplete. Verified additions and replacements are recorded below and in the JSON companion. |
| Text locations | All 114 existing span occurrences match exact half-open Unicode character offsets. No stale quote, out-of-bounds location, unexpected source or pin mismatch was found. Proposed locations are also verified. |

The existing AND options are the ADGA resize/paste and blur/edge combinations, and the two-skip/all-layer-reconstruction combination. Their component spans supply complementary facts. Incomplete tails in ADGA and clean-reference passages are real 180-word-window boundaries, not quote or offset errors.

Factual qualifications such as fixed line frequency, incomplete CDS, unchanged SSIM components and the conflicting AMFF paragraph need supporting text if complete evidence is meant to include them. Generic limits on generalization, unreported measurements and forbidden claims remain answer-review rules. A passage-retention score cannot establish that an answer obeys them. The no-direct-ranking conclusion in the metrics comparison is a reasoned inference from different metrics and studies, not a literal statement in either paper.

## Findings

### F01. Stage-two alternatives do not match their own requirement

Severity: high. [`tech-autoencoder-exact`](../../labels/technical-development.json#L251).

part-2 alternative 2 never states clean references. Reframe the group around the actual normal/synthetic sample-type requirement, using p8 or p46. Keep clean targets as explanatory context rather than silently imposing an extra answer requirement.

### F02. RGB ordering is outside every labeled span

Severity: high. [`tech-rgb-channel-assignment`](../../labels/technical-development.json#L547).

Both groups quote p38[294:479]. Forward and backward are named only in p38[168:293]. The existing quotes cannot determine which grayscale image is red versus green. Expand part-1 to p38[168:479].

### F03. Gaussian identity and fixed footprint are missing

Severity: high. [`tech-changing-neighborhood`](../../labels/technical-development.json#L1260).

The selected p31 spans erase sigma and leave it undefined. Add p30 parameter identity and p29 fixed 11-by-11 footprint. The original XML confirms changing sigma, not changing window dimensions, and symbolic k without a numeric value.

### F04. Architecture conflict is not required by coverage

Severity: high. [`tech-amff-layers`](../../labels/technical-development.json#L582).

p41 alone covers all current groups, even though the expected answer must acknowledge p46's inconsistent P3/P5 AMFF statement. Add an AND group contrasting p41 with p46. Figure 8 agrees with p41 and is original-only visual evidence.

### F05. Efficiency result lacks its operational boundary

Severity: high. [`tech-wafer-exact`](../../labels/technical-development.json#L188).

Abstract and conclusion both support the joint result but not the required fixed-line-frequency/excluded-transmission qualification. Add p14:w180 plus the fixed 23,400-Hz experiment clause in p16.

### F06. Stripe identity and incomplete CDS qualification are omitted

Severity: medium. [`tech-wafer-paraphrase`](../../labels/technical-development.json#L216).

The readout-mismatch quote omits the stripe-like CFPN identification. No group requires the qualification that correlated dual sampling does not completely eliminate CFPN. Both are explicit in p15.

### F07. Some input-size alternatives refer to the wrong population

Severity: medium. [`tech-imagenet-initialization`](../../labels/technical-development.json#L718), [`tech-compare-network-inputs`](../../labels/technical-development.json#L1570).

p25 belongs to the self-built CNN subsection, so it cannot be a standalone alternative for both transferred classifiers. p29 gives the common image-processing workflow without naming those architectures. Preserve p26's model identity with its size and ImageNet assertions.

### F08. AW-SSIM comparison loses standard-SSIM facts

Severity: medium. [`tech-aw-ssim-combination`](../../labels/technical-development.json#L796).

part-1 alternative 2 establishes AW-SSIM addition only, not what it replaces. Combine it with the standard multiplication sentence in p25. Add the required unchanged component-calculations sentence in p26.

### F09. Charge transfer is quoted without the moving image

Severity: medium. [`tech-moving-signal-addition`](../../labels/technical-development.json#L1199).

The i1/i2 charge-transfer sentence alone does not explain how the charge follows object/image motion across stages. Expand p7 or add p8[0:complete second sentence]. The ideal square-root scaling quote is correct and already includes Ideally.

### F10. Additional scientific qualifications have no groups

Severity: medium. [`tech-manual-outline-union`](../../labels/technical-development.json#L986), [`tech-daylight-interference`](../../labels/technical-development.json#L1114), [`tech-too-many-shortcuts`](../../labels/technical-development.json#L1234).

Add one-view outline visibility, tested-versus-proposed containment, and why partial defect reconstruction undermines residual localization. These are available in p33, p34 and autoencoder p6 respectively.

### F11. Several short alternatives omit their referents

Severity: medium. [`tech-glass-paraphrase`](../../labels/technical-development.json#L63), [`tech-stripe-frequencies`](../../labels/technical-development.json#L640), [`tech-adaptive-binarization`](../../labels/technical-development.json#L675).

Retain backward-lighting context for it, define theta as phase, and explicitly connect grayscale/binarization to structured images. The full cases sometimes supply the context across other groups, but the individual alternatives do not.

### F12. Detector feature-extraction groups omit downstream purpose

Severity: medium. [`tech-compare-network-roles`](../../labels/technical-development.json#L1621).

Extend p41 or p59 to include fusion and detection. The autoencoder compression/reconstruction groups are sufficient together.

### F13. Oversized or mismatched groups distort partial coverage

Severity: low. [`tech-small-photo-supply`](../../labels/technical-development.json#L1036), [`tech-rgb-channel-assignment`](../../labels/technical-development.json#L547), [`tech-manual-outline-union`](../../labels/technical-development.json#L986), [`tech-bright-specks-dark-background`](../../labels/technical-development.json#L1149).

The two small-photo groups both require optional augmentation hyperparameters. The blue-average group requires unrelated red/green text. Two descriptions promise facts covered separately by neighboring groups. Shorten the spans or narrow the descriptions.

### F14. Valid alternatives were omitted

Severity: medium. [`tech-painted-exact`](../../labels/technical-development.json#L113), [`tech-autoencoder-exact`](../../labels/technical-development.json#L251), [`tech-compare-fusion`](../../labels/technical-development.json#L333), [`tech-amff-layers`](../../labels/technical-development.json#L582), [`tech-aw-ssim-combination`](../../labels/technical-development.json#L796), [`tech-both-checks-clean`](../../labels/technical-development.json#L1071), [`tech-damaged-clean-pairs`](../../labels/technical-development.json#L1310), [`tech-compare-localization-outputs`](../../labels/technical-development.json#L1345), [`tech-moving-signal-addition`](../../labels/technical-development.json#L1199).

The proposed changes include exact, verified alternatives in introduction, abstract, architecture and conclusion passages. These can change MRR and complete-evidence coverage without any retrieval change. No original-only figure or formula has been assigned a fabricated passage ID.

## Every case and group

Each row lists all groups in that case. Supported means the positive fact is established in its source context. Group-level support does not override a missing case-level qualification. Alternative-level exceptions and original locations are recorded individually in [evidence-review.json](evidence-review.json).

| Case | Groups | Review |
| --- | --- | --- |
| [`tech-glass-exact`](../../labels/technical-development.json#L12) | part-1: supported; part-2: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-glass-paraphrase`](../../labels/technical-development.json#L63) | part-1: supported; part-2: supported; part-3: needs context | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-painted-exact`](../../labels/technical-development.json#L113) | part-1: supported; part-2: supported | The names and scratch-built comparator are supported. The introduction and conclusion contain additional exact alternatives. Preserve the OK/NOK heater-task scope. |
| [`tech-wafer-exact`](../../labels/technical-development.json#L188) | part-1: supported | Both alternatives support the reported joint SNR result. They omit the explicit fixed-line-frequency and excluded-data-transmission qualification required by the dataset. |
| [`tech-wafer-paraphrase`](../../labels/technical-development.json#L216) | part-1: needs context; part-2: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-autoencoder-exact`](../../labels/technical-development.json#L251) | part-1: supported; part-2: revise requirement and support; part-3: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-compare-fusion`](../../labels/technical-development.json#L333) | part-1: supported; part-2: supported; part-3: supported; part-4: supported; part-5: supported | All five requirements are represented. The current alternatives support the relevant facts in their article context. The first RGB alternative contains unrelated dataset-novelty prose. Additional alternatives exist for illumination, heater fusion, and named ADMF-Net feature-level fusion. |
| [`tech-obb`](../../labels/technical-development.json#L477) | part-1: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-annotation-tools`](../../labels/technical-development.json#L497) | part-1: supported; part-2: supported; part-3: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-rgb-channel-assignment`](../../labels/technical-development.json#L547) | part-1: insufficient without antecedent; part-2: supported but overlong | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-amff-layers`](../../labels/technical-development.json#L582) | part-1: supported; part-2: supported; part-3: supported | The P3/P4, P5 FSPPF and OBB-head groups are correct under the question's explicit paragraph-41/Figure-8 scope. The required acknowledgment of contradictory P3/P5 prose in paragraph 46 has no group. Figure 8 was inspected in Chrome and agrees with paragraph 41. Do not admit paragraph 46 as an alternative for the P3/P4 group. |
| [`tech-stripe-frequencies`](../../labels/technical-development.json#L640) | part-1: supported; part-2: needs symbol definition | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-adaptive-binarization`](../../labels/technical-development.json#L675) | part-1: needs modality context; part-2: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-imagenet-initialization`](../../labels/technical-development.json#L718) | part-1: needs model identity; part-2: revise alternative scope | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-tdi-motion-sync`](../../labels/technical-development.json#L761) | part-1: supported; part-2: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-aw-ssim-combination`](../../labels/technical-development.json#L796) | part-1: revise comparator context; part-2: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-adga-shapes`](../../labels/technical-development.json#L839) | part-1: supported; part-2: supported; part-3: supported; part-4: supported | All four groups are supported. The resize/paste AND option supplies complementary operations. The blur/edge AND option supplies application plus edge effect, despite its final incomplete sentence. That incomplete tail is exact stored text, not an offset mismatch. The edge span can end before ensuring a without losing the required fact. |
| [`tech-stable-camera`](../../labels/technical-development.json#L916) | part-1: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-turn-and-flip-labels`](../../labels/technical-development.json#L936) | part-1: supported; part-2: supported; part-3: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-manual-outline-union`](../../labels/technical-development.json#L986) | part-1: description mismatch; part-2: supported; part-3: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-small-photo-supply`](../../labels/technical-development.json#L1036) | part-1: supported but overlong; part-2: supported but overlong | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-both-checks-clean`](../../labels/technical-development.json#L1071) | part-1: supported; part-2: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-daylight-interference`](../../labels/technical-development.json#L1114) | part-1: supported; part-2: supported | The contrast effect and successful processing are supported. The required tested-versus-proposed containment qualification is missing, though available in the same paragraph. |
| [`tech-bright-specks-dark-background`](../../labels/technical-development.json#L1149) | part-1: description mismatch; part-2: supported; part-3: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-moving-signal-addition`](../../labels/technical-development.json#L1199) | part-1: insufficient motion context; part-2: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-too-many-shortcuts`](../../labels/technical-development.json#L1234) | part-1: supported | The two-span AND alternative establishes the experimental two-skip preference and unwanted all-layer partial reconstruction. Add the residual-localization reason if the required qualification is scored, instead of interpreting reconstruction quality as detection quality. |
| [`tech-changing-neighborhood`](../../labels/technical-development.json#L1260) | part-1: needs parameter identity; part-2: needs parameter identity; part-3: needs parameter identity | The pinned XML identifies sigma as standard deviation, the patch dimensions as PH/PW, and k as a symbolic small increment. No numeric k is given. Do not label the misleading p31 phrase different window sizes as evidence for changing the 11-by-11 dimensions. Attach parameter context to the tradeoff and reset alternatives too, or make parameter identity a mandatory group. |
| [`tech-damaged-clean-pairs`](../../labels/technical-development.json#L1310) | part-1: supported; part-2: supported | Both facts are supported. The end of the reconstruction-reference quote is an exact word-window cutoff, not stale text. A clean-target alternative is available in p36; a single p17 range also connects artificial/clean pairing and reconstruction reference. |
| [`tech-compare-localization-outputs`](../../labels/technical-development.json#L1345) | part-1: supported; part-2: supported | Both representations are supported. The p6 residual sentence is a methodological statement introduced before this method; accept it together with the existing p40 method-specific result if stricter implementation attribution is required. Canopy annotation alone is not an alternative for an OBB detection head, but p41 and p59 explicitly report the head. |
| [`tech-compare-training-splits`](../../labels/technical-development.json#L1380) | part-1: supported; part-2: supported | Both partition claims are supported with correct counting units. The canopy ratio is reported as 9:1, not an exact identity of the integer counts. These excerpts do not establish sample independence after augmentation; retain that as an answer-review limit, not an invented positive claim. |
| [`tech-compare-training-computers`](../../labels/technical-development.json#L1415) | part-1: supported; part-2: supported; part-3: supported | All frameworks, versions, GPU and system/VRAM quantities are supported. Do not turn the different machines into a comparative speed claim. |
| [`tech-compare-data-expansion`](../../labels/technical-development.json#L1465) | part-1: supported; part-2: supported | Both pipelines are supported. The heater span can be split at the crop and transformation clauses to improve partial-coverage diagnostics. The augmentation count is not an independent acquisition count. |
| [`tech-compare-evaluation-metrics`](../../labels/technical-development.json#L1500) | part-1: supported; part-2: supported | The two groups support different metric definitions. The no-direct-ranking answer is a comparison inference grounded in different metrics and studies, not a quotation in either source. Text-span coverage cannot verify that the answer actually makes this inference. If dataset difference is to be independently scored, add the complementary source scope below. |
| [`tech-compare-optical-cues`](../../labels/technical-development.json#L1535) | part-1: supported; part-2: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-compare-network-inputs`](../../labels/technical-development.json#L1570) | part-1: supported; part-2: revise alternative scope | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |
| [`tech-compare-network-roles`](../../labels/technical-development.json#L1621) | part-1: incomplete purpose; part-2: supported; part-3: supported | The groups cover the required positive facts. Keep the stated paper/task scope and the limits on unsupported generalization. |

## Exact proposed evidence

These are review recommendations, not an applied label patch. OR separates alternatives; AND joins spans needed together. New group IDs are suggestions. The optional metrics scope group and complementary weighting background are explicitly distinguished from required additions. Existing valid alternatives should remain unless replaced to correct scope or excess text.

### Proposal 1. tech-glass-paraphrase / part-3

expand context. Backward lighting loses surface and boundary detail.

Alternative 1:

- `pmc11510794:p22:w0[192:405]`

  > Backward lighting effectively reveals the depth information of defects, aiding in the analysis of defect severity and classification. However, it tends to lose surface detail and some boundary contour information.

### Proposal 2. tech-painted-exact / part-1

add alternative. Transferred classifier names.

Alternative 1:

- `pmc11768589:p5:w180[0:305]`

  > (2) TL of two pre-trained CNN architectures—ResNet-50 and Inception V3. At this point, the proposed system will not only provide a more enriched dataset in terms of variety given the wider detectable defect categories, but also an improved prediction accuracy regarding the status of the painted surfaces.

### Proposal 3. tech-painted-exact / part-2

add alternative. Scratch-built comparator.

Alternative 1:

- `pmc11768589:p25:w0[0:104]`

  > The first approach consisted in the construction and training of a new and lightweight CNN from scratch.

### Proposal 4. tech-wafer-exact / efficiency-scope

add required group. Efficiency argument excludes transmission time and holds line frequency fixed.

Alternative 1:

- `pmc10934137:p14:w180[82:334]`

  > Without considering the data transmission time, the imaging time is only related to line frequency. Therefore, the increase in the number of TDI stages does not affect the line frequency, thus improving the SNR without sacrificing detection efficiency.

- `pmc10934137:p16:w0[0:60]`

  > In the experiment, the line frequency is fixed at 23,400 Hz,

All spans in this alternative are required together.

### Proposal 5. tech-wafer-paraphrase / part-1

expand context. Background stripes are CFPN caused by column-readout mismatch.

Alternative 1:

- `pmc10934137:p15:w0[0:299]`

  > It should be noted that in Figure 9e, when the signal intensity of particles is weak at low TDI stages, the presence of stripe-like column fixed pattern noise (CFPN) in the background can impact particle detection. This CFPN is caused by a mismatch between the readout circuits of different columns.

### Proposal 6. tech-wafer-paraphrase / cds-incomplete

add required group. Correlated dual sampling does not completely eliminate CFPN.

Alternative 1:

- `pmc10934137:p15:w0[300:429]`

  > Although the correlated dual sampling circuit structure is an effective method to eliminate CFPN, this elimination is incomplete.

### Proposal 7. tech-autoencoder-exact / part-2

replace requirement and alternatives. Stage two uses normal and artificially defective training samples.

Alternative 1:

- `pmc11121878:p8:w0[83:282]`

  > The first stage of training is exclusively conducted only on normal samples, and the second stage is training on normal and artificially defective samples using the model weight from the first stage.

Alternative 2:

- `pmc11121878:p46:w0[519:674]`

  > In the second stage of training, artificially defective samples and normal samples are used to train the model and enhance its ability to localize defects.

Alternative 3:

- `pmc11121878:p1:w0[1152:1296]`

  > In the second stage of training, the weights obtained from the first stage are used to train the model on both normal and artificially defective

- `pmc11121878:p1:w180[0:17]`

  > training samples.

All spans in this alternative are required together.

### Proposal 8. tech-autoencoder-exact / part-1

add alternative. Normal-only first stage.

Alternative 1:

- `pmc11121878:p1:w0[1008:1151]`

  > In the first stage, the model trains only on normal samples using AW-SSIM loss, allowing it to learn robust representations of normal features.

Alternative 2:

- `pmc11121878:p46:w0[59:160]`

  > The first stage of training is performed only on normal samples, utilizing the AW-SSIM loss function.

### Proposal 9. tech-autoencoder-exact / part-3

add alternative. Transfer first-stage weights.

Alternative 1:

- `pmc11121878:p8:w0[83:282]`

  > The first stage of training is exclusively conducted only on normal samples, and the second stage is training on normal and artificially defective samples using the model weight from the first stage.

### Proposal 10. tech-compare-fusion / part-1

add alternative. Canopy forward/backward illumination.

Alternative 1:

- `pmc11510794:p1:w0[420:565]`

  > To address this issue, we developed a dual-modal illumination system that integrates both forward and backward lighting to capture defect images.

Alternative 2:

- `pmc11510794:p57:w0[264:427]`

  > This system utilizes both forward lighting and backward lighting to capture defect images, facilitating a more comprehensive and accurate defect detection process.

### Proposal 11. tech-compare-fusion / part-3

add alternative. Named ADMF-Net performs feature-level fusion.

Alternative 1:

- `pmc11510794:p40:w0[0:194]`

  > To fully utilize the multimodal information obtained under different lighting conditions, this paper proposes an attention-based dual-branch modal fusion network (ADMF-Net) for defect detection.

- `pmc11510794:p5:w0[515:766]`

  > A dual-modal baseline is designed and proved to be competitive, in which we designed two fusion detection methods: a data-level fusion method named RGB Channel Fusion, and an attention-based dual-branch modal fusion network using feature-level fusion.

All spans in this alternative are required together.

### Proposal 12. tech-compare-fusion / part-4

add alternative. Heater structured and bright-field modes.

Alternative 1:

- `pmc11768589:p16:w0[109:319]`

  > The liquid crystal display (LCD) monitor (21’’) provided two illumination modes: (1) structured illumination, by projecting a sinusoidal pattern; and (2) bright field illumination, by projecting a white screen.

Alternative 2:

- `pmc11768589:p44:w0[256:520]`

  > This system comprised deflectometry and bright light-based image acquisition for dataset generation, DL algorithms for defect detection and classification, surface’s information shipping to a MES server, and a final visual interface for defect information display.

### Proposal 13. tech-compare-fusion / part-5

add alternative. Heater decision-level fusion.

Alternative 1:

- `pmc11768589:p35:w0[1000:1122]`

  > However, unlike Guan et al. that employed a feature-level fusion, a decision-level fusion method was applied in this work.

Alternative 2:

- `pmc11768589:p5:w0[928:1009]`

  > (2) DL models for defect detection and classification with decision-level fusion,

### Proposal 14. tech-rgb-channel-assignment / part-1

expand context. Forward grayscale is red and backward grayscale is green.

Alternative 1:

- `pmc11510794:p38:w0[168:479]`

  > In the RGB Channel Fusion method, the forward lighting image and the backward lighting image are each converted to grayscale. These grayscale images are then assigned to the red channel and green channel of the fused image, respectively, while the blue channel is obtained by averaging the two grayscale images.

### Proposal 15. tech-rgb-channel-assignment / part-2

shorten span. Blue averages the grayscale images.

Alternative 1:

- `pmc11510794:p38:w0[412:479]`

  > the blue channel is obtained by averaging the two grayscale images.

### Proposal 16. tech-amff-layers / architecture-conflict

add required group. Paragraph 46 conflicts with paragraph 41 on AMFF scales.

Alternative 1:

- `pmc11510794:p41:w0[200:353]`

  > Next, two AMFF modules are inserted between the two backbones, applied to the P3 and P4 layers, to obtain fused features with different receptive fields.

- `pmc11510794:p46:w0[277:400]`

  > The output of FSPPF, along with the outputs from the P3 and P5 layers’ AMFF modules, serves as the input to the neck layer.

All spans in this alternative are required together.

### Proposal 17. tech-amff-layers / part-2

add alternative. P5 outputs feed FSPPF.

Alternative 1:

- `pmc11510794:p46:w0[0:179]`

  > The FSPPF module first concatenates the outputs of the P5 layers from the two feature extraction backbones, and then passes it into the SPPF (Spatial Pyramid Pooling-Fast) module.

### Proposal 18. tech-stripe-frequencies / part-2

add context span. Zero phase in both tested patterns.

Alternative 1:

- `pmc11768589:p17:w0[270:285]`

  > θ to its phase.

- `pmc11768589:p18:w0[247:287]`

  > The θ was 0 for both frequencies tested.

All spans in this alternative are required together.

### Proposal 19. tech-adaptive-binarization / part-1

add context span. Structured images receive grayscale and adaptive binarization.

Alternative 1:

- `pmc11768589:p22:w0[0:310]`

  > Afterwards, the images were subjected to processing through the conversion RGB to grey scale and the application of adaptive binarization to reduce the effect of the environmental lighting (Figure 2b). It should be emphasized that images obtained via bright field illumination were not subjected to processing.

### Proposal 20. tech-imagenet-initialization / part-1

expand context. ResNet-50 and Inception V3 were pretrained on ImageNet.

Alternative 1:

- `pmc11768589:p26:w0[0:246]`

  > The second approach entailed the TL and fine-tunning of two common pre-trained CNNs: ResNet-50 and Inception V3. These networks have been trained on at least one million images from the ImageNet and have over 23 million trainable parameters [43].

### Proposal 21. tech-imagenet-initialization / part-2

add context span. The transferred classifier pair uses 450 by 450 inputs.

Alternative 1:

- `pmc11768589:p26:w0[0:112]`

  > The second approach entailed the TL and fine-tunning of two common pre-trained CNNs: ResNet-50 and Inception V3.

- `pmc11768589:p26:w0[247:313]`

  > The input image size of these pre-trained CNNs was also 450 × 450.

All spans in this alternative are required together.

### Proposal 22. tech-compare-network-inputs / part-2

add context span. The transferred classifier pair uses 450 by 450 inputs.

Alternative 1:

- `pmc11768589:p26:w0[0:112]`

  > The second approach entailed the TL and fine-tunning of two common pre-trained CNNs: ResNet-50 and Inception V3.

- `pmc11768589:p26:w0[247:313]`

  > The input image size of these pre-trained CNNs was also 450 × 450.

All spans in this alternative are required together.

### Proposal 23. tech-aw-ssim-combination / part-1

add context span. AW-SSIM adds sub-functions where standard SSIM multiplies.

Alternative 1:

- `pmc11121878:p25:w0[0:148]`

  > The SSIM loss calculation uses multiplication between the three sub-functions to bring independence between these factors, as shown in Equation (6).

- `pmc11121878:p26:w0[0:89]`

  > For AW-SSIM, we apply addition between the three sub-functions, as shown in Equation (6).

All spans in this alternative are required together.

Alternative 2:

- `pmc11121878:p8:w0[723:921]`

  > Inspired by this, we propose an adaptive weighted structural similarity (AW-SSIM) loss by introducing addition instead of multiplication between the luminance, contrast, and structure sub-functions.

### Proposal 24. tech-aw-ssim-combination / component-calculations

add required group. Component calculations remain those of standard SSIM.

Alternative 1:

- `pmc11121878:p26:w0[778:892]`

  > The calculations of the luminance, contrast, and structure values in AW-SSIM are the same as in the standard SSIM.

### Proposal 25. tech-aw-ssim-combination / part-2

record complementary background. Weighting rationale; p26 is still needed to establish constant weights.

Alternative 1:

- `pmc11121878:p46:w0[161:325]`

  > AW-SSIM loss prioritizes the most important features during training by assigning different weights to the three sub-functions (luminance, contrast, and structure).

- `pmc11121878:p27:w0[0:173]`

  > The weighting factors in the AW-SSIM equation ( [formula omitted] , [formula omitted] , and [formula omitted] ) allow us to prioritize different aspects of image similarity.

All spans in this alternative are required together.

### Proposal 26. tech-adga-shapes / part-4

shorten incomplete tail. Gaussian blur softens patch edges.

Alternative 1:

- `pmc11121878:p18:w0[940:1064]`

  > To smoothly integrate this irregularly shaped portion into the target image ( [formula omitted] ), we apply a Gaussian blur.

- `pmc11121878:p18:w0[1065:1115]`

  > This blurring softens the transition at the edges,

All spans in this alternative are required together.

### Proposal 27. tech-manual-outline-union / visibility-scope

add required group. Some outlines are clear under only one lighting condition.

Alternative 1:

- `pmc11510794:p33:w0[39:130]`

  > This is because some defects are only clearly outlined under a specific lighting condition.

### Proposal 28. tech-small-photo-supply / part-1

shorten span. Four crops and raw/crop dimensions.

Alternative 1:

- `pmc11768589:p21:w0[173:282]`

  > (1) four sub-images with 450 × 450 were extracted from the original 808 × 608 images using the GIMP software;

### Proposal 29. tech-small-photo-supply / part-2

shorten span. Augment to 500 images per category.

Alternative 1:

- `pmc11768589:p21:w0[0:172]`

  > Given the low availability of painted samples (with and without defects), two strategies were employed to augment the dataset to 500 images per defect category (Figure 2a):

- `pmc11768589:p21:w0[287:376]`

  > (2) several data augmentation techniques were then performed on the extracted sub-images,

All spans in this alternative are required together.

### Proposal 30. tech-both-checks-clean / part-2

add alternative. Final OK requires both modes.

Alternative 1:

- `pmc11768589:p48:w0[127:261]`

  > by imposing OK classification on models trained with images derived from both illumination modes: sinusoidal pattern and bright field.

### Proposal 31. tech-daylight-interference / containment-scope

add required group. Environmental light was uncontrolled; containment was proposed for implementation.

Alternative 1:

- `pmc11768589:p34:w0[0:151]`

  > Environmental lighting was not controlled, in this experimental setup, to better approximate the lighting conditions observed in an industrial setting.

- `pmc11768589:p34:w0[770:945]`

  > Still, if containment is required for industrial implementation, tunnels such as those reported by Armesto et al., Molina et al., and Chang et al. could be considered [2,3,6].

All spans in this alternative are required together.

### Proposal 32. tech-moving-signal-addition / part-1

replace or expand alternative. Charge follows moving image and accumulates across stages.

Alternative 1:

- `pmc10934137:p7:w0[357:627]`

  > At a certain moment, object position p1 is imaged at image position i1. When the object moves after ∆t time, position p1 moves to p2, and the corresponding image position i1 moves to i2. Meanwhile, the charge at position i1 is transferred to position i2 and accumulated.

Alternative 2:

- `pmc10934137:p8:w0[0:240]`

  > In general, TDI image sensors consist of N TDI stages. As the object under test moves, the TDI image sensor sequentially captures light from the first stage to the Nth stage, and the charge accumulates from the first stage to the Nth stage.

### Proposal 33. tech-too-many-shortcuts / residual-purpose

add required group. Partial defect reconstruction reduces residual-based discrimination.

Alternative 1:

- `pmc11121878:p6:w0[247:354]`

  > Using the residual (difference) between the input and the reconstructed image, we can localize the defects.

- `pmc11121878:p6:w0[404:600]`

  > Partial defect reconstruction: Sometimes, the trained model might also reconstruct the defective region, thereby diminishing its ability to distinguish between defective and non-defective regions.

All spans in this alternative are required together.

### Proposal 34. tech-changing-neighborhood / gaussian-spread

add required group. Gaussian standard deviation changes weighting spread.

Alternative 1:

- `pmc11121878:p30:w0[0:440]`

  > The standard deviation [formula omitted] of the Gaussian window determines how weights are assigned to pixels within the sliding window. A smaller [formula omitted] creates a narrower window, concentrating weight near the center and reducing the influence of distant pixels, as shown in Figure 5. Conversely, a larger [formula omitted] results in a wider window, spreading weights more evenly and increasing the influence of distant pixels.

### Proposal 35. tech-changing-neighborhood / fixed-footprint

add required group. The window footprint remains 11 by 11.

Alternative 1:

- `pmc11121878:p29:w0[1035:1080]`

  > We used a window size of 11 × 11 in our work.

- `pmc11121878:p30:w0[0:136]`

  > The standard deviation [formula omitted] of the Gaussian window determines how weights are assigned to pixels within the sliding window.

All spans in this alternative are required together.

### Proposal 36. tech-changing-neighborhood / part-2

add context span. Increase Gaussian standard deviation by a small constant.

Alternative 1:

- `pmc11121878:p30:w0[0:136]`

  > The standard deviation [formula omitted] of the Gaussian window determines how weights are assigned to pixels within the sliding window.

- `pmc11121878:p31:w0[292:427]`

  > During training, it is gradually incremented by a small constant after processing every [formula omitted] patch of the training images.

All spans in this alternative are required together.

Alternative 2:

- `pmc11121878:p32:w0[0:374]`

  > Here, [formula omitted] is the standard deviation after each epoch, which depends on the number of training samples and the sizes of the patches ( [formula omitted] ) in patch-based training. H and W are the height and width of the input image, respectively, and k is a small constant added to [formula omitted] after each patch of size [formula omitted] in the input image.

### Proposal 37. tech-damaged-clean-pairs / part-2

add alternative. The reconstruction target is the clean image.

Alternative 1:

- `pmc11121878:p36:w0[0:238]`

  > Here, [formula omitted] is the combined structural and perceptual loss, [formula omitted] is the original image without defects, and [formula omitted] is the reconstructed image from the artificially defective image ( [formula omitted] ).

Alternative 2:

- `pmc11121878:p17:w0[664:1140]`

  > Here, images with artificially introduced defects ( [formula omitted] ) created by the ADGA are paired with their non-defect counterparts ( [formula omitted] ). During training, these pairs are fed into the model. The normal samples ( [formula omitted] ) are used as references to improve the reconstruction performance of the model by comparing a normal sample with the reconstructed image ( [formula omitted] ) from its artificially defective counterpart ( [formula omitted]

### Proposal 38. tech-compare-localization-outputs / part-1

add alternative. Canopy rotated-box localization.

Alternative 1:

- `pmc11510794:p41:w0[452:604]`

  > Finally, the three scales of features are fed into the detection layers, using an OBB detection head to predict the defects with rotated bounding boxes.

Alternative 2:

- `pmc11510794:p59:w0[506:648]`

  > Finally, the features are fed into the detection layers, where an OBB detection head is used to provide the rotated bounding boxes of defects.

### Proposal 39. tech-compare-localization-outputs / part-2

add alternative. Residual-based localization.

Alternative 1:

- `pmc11121878:p6:w0[247:354]`

  > Using the residual (difference) between the input and the reconstructed image, we can localize the defects.

### Proposal 40. tech-compare-evaluation-metrics / dataset-scope

optional required group. The scores concern different datasets and tasks.

Alternative 1:

- `pmc11510794:p36:w0[0:155]`

  > The final dataset of aircraft glass canopy defects, named ag_dual_obb, includes four types of defects, totaling 1752 defect points and 4784 defect objects.

- `pmc11121878:p38:w0[0:170]`

  > For our experiments, we used diverse anomaly detection samples sourced from the MVTec AD dataset [47], including leather, carpet, hazelnut, pill, wood, and tile textures.

All spans in this alternative are required together.

### Proposal 41. tech-compare-network-roles / part-1

expand context. Canopy backbones extract modality features for fusion and detection.

Alternative 1:

- `pmc11510794:p41:w0[0:604]`

  > In this network, we use two CSPDarknet-like feature extraction backbones, as proposed in YOLOv8, to extract multi-scale features from the forward lighting and backward lighting modalities separately. Next, two AMFF modules are inserted between the two backbones, applied to the P3 and P4 layers, to obtain fused features with different receptive fields. Then, the P5 layers from both modalities are connected to a spatial pyramid pooling layer, FSPPF. Finally, the three scales of features are fed into the detection layers, using an OBB detection head to predict the defects with rotated bounding boxes.

Alternative 2:

- `pmc11510794:p59:w0[0:648]`

  > Furthermore, we proposed a data-level fusion method named RGB Channel Fusion, and a feature-level fusion model, the attention-based dual-branch modal fusion network (ADMF-Net). The model uses two feature extraction backbones to independently extract multi-scale features from the forward and backward lighting modalities. Next, through the attention-based multi-modal feature fusion block (AMFF) and improved SPPF module, the network adaptively integrates the multi-scale features from the two modalities. Finally, the features are fed into the detection layers, where an OBB detection head is used to provide the rotated bounding boxes of defects.

## Provenance and checks

- Input label file SHA-256: `fc04f09f169c35d5d22173ef67246759ba9495a7a0e707635a0765391268a59e`.
- Canonical serialized dataset SHA-256: `0bd3499a71d908b7482d55e87110115b428b0ede5a7803b0c9e86ba0d8feb5df`.
- Raw corpus SHA-256: `cda1b161618373b9c7b9701d3326fda4707f9501bbc3bf29c802d9a000908bce`.
- Shared passage identity: `c7bf2f1f6b9c866573669f946866b5b0635ae4afcee1d06511e3109ab47c1157`.

Inspected the listed alternatives against development questions, required claims and qualifications; searched the four stored documents for alternatives; checked pinned XML for the Gaussian interpretation and source provenance. Inspected PR 8 and canopy Figure 8 and conflicting prose in Chrome. This review did not repeat the prior inspection of all 38 figure images or claim an exhaustive new figure/table audit.

Canonical passages were reconstructed in memory with the repository's `chunk_documents`, using the pinned 180-word windows. The repository's `validate_labels` passed. All original XML checksums match document attribution. Every proposed span was located by exact text, checked against its stored substring and checked against the case's expected source IDs. No offsets were assigned to unextracted figures, tables or equations.

After label corrections are reviewed and approved with truthful reviewer provenance, rerun every compared development mode because label hashes and coverage/MRR can change. Preserve the existing held-out freeze and question-approval archive.
