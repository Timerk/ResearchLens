# Canopy and heater development-case audit

AI-assisted source review, 2026-10-05. These are proposals for owner review, not a replacement for approved labels or independent human scientific review. No cached retrieval scores or rankings were consulted before these judgments were written.

All 16 visible questions have prose answers in the canonical index. The AMFF case asks for a particular account in a paper with conflicting prose; that scoped account is answerable, while independent verification of Figure 8's pixels remains outside this local text audit.

Checked 60 approved span occurrences against canonical text, including source identity and half-open character offsets. Original XML checksums match corpus attribution, and all reviewed source paragraphs match the originals. The JSON companion contains every approved span and individual requirement classification. The original XML tables and captions were also checked for omitted relevant context. No approved input files were changed.

## Findings that need separate treatment

- Confirmed annotation defects: the repeated glass depth qualification, plus omitted scratch-comparator and model-name alternatives for `tech-painted-exact`.
- Question-contract choices: paragraph 46's conflict note is conditional for the explicitly paragraph-41-scoped AMFF question. Eightfold augmentation, annotation-file checks and enclosure proposals are also extra answer detail. Most of these occupy the same already-needed passage and cannot explain a passage-selection plateau.
- Contextual sufficiency judgment: paragraph 22 alone is a candidate alternative for adaptive binarization when its explicit bright-field exclusion resolves the images' scope. Keep the stricter p29+p22 result visible and submit this inference policy for owner review.
- Reasonable conservative design: retain the stripe phase definition in paragraph 17, and the explicit two-mode final decision rule for heater acceptance. Their joint support has a factual purpose.

Development-only archive comparison followed the first written judgments. It confirms that AMFF's question was narrowed from an unqualified architecture question to the paragraph-41/Figure-8 account before the evidence fixes added the contradiction group. For adaptive binarization, the earlier audit explicitly allowed the bright-field exclusion as complementary context; the applied fix chose a separate structured-mode passage. These are reviewable scope and context-policy choices, not newly discovered source text.

## Case-level review

### tech-glass-exact

Question: Which forward and backward light sources are used in the aircraft glass canopy acquisition platform?

Requested facts: Identify the forward light source and the backward light source in the named platform.

Sufficient scoped answer: Forward lighting uses a ring light, and backward lighting uses a planar backlight.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. Both directions and source types are directly requested.
- `required_qualifications[0]`: necessary for accuracy. Attribute the answer to this platform. The visible question already supplies that scope; no separate disclaimer is needed.
- `forbidden_claims[0]`: conditional on additional claim. Calibration values or universal optimality would be new, unsupported claims.

Evidence judgment: Both alternatives for each group are sufficient. Paragraph 28's backlight panel is the concrete planar source; paragraph 25 lists hardware but does not map lights to directions, so is topical rather than a sufficient replacement.

Canonical sources: `pmc11510794:p24:w0`, `pmc11510794:p28:w0`.

Confidence: high. Existing labels remain unchanged.

### tech-glass-paraphrase

Question: In the aircraft glass canopy study, why take pictures of the same transparent cover with light arriving from opposite sides, and what information can each view miss?

Requested facts: Explain the complementary purpose of opposite illumination directions. State what each view reveals and what it can miss.

Sufficient scoped answer: Forward bright-field lighting shows surface scratches but suffers reflections and uneven illumination; backward lighting shows depth-related information but can lose surface details and boundary contours.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. The forward view's benefit and limitation answer the question.
- `required_claims[1]`: explicitly requested. The backward view's benefit and limitation answer the question.
- `required_qualifications[0]`: necessary for accuracy. Report these as observations from the named study.
- `required_qualifications[1]`: conditional on additional claim. A depth-calibration disclaimer is needed if an answer implies quantitative depth measurement. Plainly attributed qualitative depth information does not require a separate numerical disclaimer.
- `required_qualifications[2]`: unsupported or mismatched. Exact duplicate of qualification 1. Remove the duplicate without changing the scientific constraint.
- `forbidden_claims[0]`: necessary for accuracy. Universal sufficiency of one view contradicts the requested complementary explanation.
- `forbidden_claims[1]`: conditional on additional claim. Numerical thresholds would be an added claim.

Evidence judgment: Paragraph 22 directly supports all three groups. The third span correctly includes the backward-lighting antecedent. Abstract paragraph 1 supports the general value of dual lighting but not each specific limitation; paragraph 33's scratches/spots examples cannot replace the required depth/boundary account.

Canonical sources: `pmc11510794:p22:w0`.

Proposed correction: Exact duplicated guard, not an extra fact. No evidence-group change and no retrieval-score effect.

Confidence: high. Existing labels remain unchanged.

### tech-painted-exact

Question: Which pre-trained CNNs were compared with a model trained from scratch for painted heating-device surface classification?

Requested facts: Name the pretrained CNNs compared against the scratch-built model for painted heater classification.

Sufficient scoped answer: The study compares transferred ResNet-50 and Inception V3 against a self-built CNN trained from scratch.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. Model names and the comparison are requested.
- `required_qualifications[0]` / painted heating-device surfaces: necessary for accuracy. Keep the painted heating-device scope supplied by the question.
- `required_qualifications[0]` / OK/NOK classification: optional background. Spelling out the OK/NOK labels is useful background but unnecessary to identify the model pair.
- `forbidden_claims[0]`: necessary for accuracy. Attributing these classifiers to the canopy dataset would misidentify the source.

Evidence judgment: All existing alternatives support their own subfact. Paragraph 26 names the models without the comparator; paragraph 25 identifies the comparator without naming both models. Keeping separate groups is defensible. Missing factual alternatives exist in paragraph 5's first window and paragraph 37's second window. Related-work paragraph 14 lists other studies and is not a substitute.

Canonical sources: `pmc11768589:p1:w0`, `pmc11768589:p15:w180`, `pmc11768589:p26:w0`, `pmc11768589:p44:w0`, `pmc11768589:p5:w0`, `pmc11768589:p37:w180`.

Proposed correction: This is the study's own comparison, not a related-work claim; the next canonical window is already accepted for the model names.

- `pmc11768589:p5:w0[1109:1261]`: Regarding the feature extraction and decision-making performed by the DL models, two approaches were compared: (1) a CNN built and trained from scratch;

Proposed correction: The paper's own results explicitly identify both fine-tuned pretrained models. The numerical accuracies are not required by this question.

- `pmc11768589:p37:w180[24:203]`: Indeed, the fine-tuning of pre-trained CNNs considerably improved the outputs, with ResNet-50 and Inception V3 reaching around 95% and 90% of accuracy, respectively (Figure 7b,c).

Confidence: high. Existing labels remain unchanged.

### tech-obb

Question: Why are oriented bounding boxes (OBB) selected for aircraft canopy defect annotation?

Requested facts: Explain the dataset-specific reason to use oriented bounding boxes.

Sufficient scoped answer: Many defects are slender, span much of an image and can interlace, which motivates oriented boxes.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. The target geometry is the stated rationale.
- `required_qualifications[0]`: necessary for accuracy. The motivation applies to this dataset, which is already named in the question.
- `forbidden_claims[0]`: conditional on additional claim. A universal OBB-superiority claim would go beyond the question and evidence.

Evidence judgment: Paragraph 31 gives the full rationale in one sentence. The later OBB-head passages establish rotated predictions but do not explain the annotation choice.

Canonical sources: `pmc11510794:p31:w0`.

Confidence: high. Existing labels remain unchanged.

### tech-annotation-tools

Question: What X-AnyLabeling version and Segment Anything variant are used for canopy pre-labeling, and how are OBBs derived?

Requested facts: Give the X-AnyLabeling version, the Segment Anything variant and how pre-labeling polygons become OBBs.

Sufficient scoped answer: X-AnyLabeling 2.3.5 uses Segment Anything ViT-Large for preparatory polygons; a script calculates each minimum enclosing rectangle.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. All three named details are requested.
- `required_qualifications[0]`: necessary for accuracy. The question already calls this pre-labeling. Describe preparatory labels accurately without requiring a second passage about human checks.
- `forbidden_claims[0]`: conditional on additional claim. Human checks being unnecessary would be a new claim contradicted by paragraph 33.

Evidence judgment: All three exact spans in paragraph 32 are sufficient and stay within one passage. Paragraph 33's manual review is useful extra context, not a missing required alternative for the named software or rectangle procedure.

Canonical sources: `pmc11510794:p32:w0`.

Confidence: high. Existing labels remain unchanged.

### tech-rgb-channel-assignment

Question: How does RGB Channel Fusion assign forward and backward grayscale canopy images to red, green and blue?

Requested facts: Map the forward image, backward image and their combination onto RGB channels.

Sufficient scoped answer: Forward grayscale goes to red, backward grayscale to green, and their average to blue.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. The three channel assignments are exactly requested.
- `required_qualifications[0]`: optional background. Calling the construction data-level fusion is correct background; the mapping already answers the question.
- `forbidden_claims[0]`: necessary for accuracy. Subtraction would be incorrect for the reported primary method. Table 5's differential-image ablation is a separate variant.

Evidence judgment: Paragraph 38 supports both groups. Group part-1 includes the blue rule as context and overlaps part-2, but it imposes no extra passage. Paragraph 39 motivates averaging without stating both red/green assignments, so it is not a full substitute. Original Table 5 confirms the differential third-channel variant must not overwrite the primary method.

Canonical sources: `pmc11510794:p38:w0`.

Confidence: high. Existing labels remain unchanged.

### tech-amff-layers

Question: According to paragraph 41 and Figure 8 of the canopy paper, at which feature scales does ADMF-Net use AMFF and FSPPF, and what detection head follows?

Requested facts: Report the AMFF scales, the FSPPF scales and detection head according to the explicitly named paragraph 41 and Figure 8 account.

Sufficient scoped answer: Paragraph 41 reports AMFF at P3/P4, both P5 outputs feeding FSPPF, and an OBB detection head for rotated boxes.

Answerability: The requested paragraph-41 account is answerable from the index. The paper is internally contradictory because paragraph 46 says P3/P5 AMFF. The current audit verified both XML prose locations. Figure 8's caption and graphic reference are present in the original XML, but the graphic is not bundled and was not visually rechecked; its claimed agreement rests on the earlier review, not new visual verification.

Requirement classification:

- `required_claims[0]`: explicitly requested. The scoped feature scales and head are directly requested.
- `required_qualifications[0]`: conditional on additional claim. The paragraph-46 conflict is mandatory if an answer claims a single unambiguous architecture across the paper. It is optional supplementary context when the answer explicitly reports the paragraph-41 account requested. Figure agreement must not be claimed as newly verified by this audit.
- `forbidden_claims[0]`: conditional on additional claim. Feature dimensions and angle conventions would be extra unsupported detail.
- `forbidden_claims[1]`: necessary for accuracy. Do not affirm internal consistency. Omitting an unrequested conflict note is not itself a claim of consistency.

Evidence judgment: All existing spans accurately quote the source. The architecture-conflict joint alternative genuinely proves a contradiction and therefore correctly needs both paragraphs. Making that extra fact mandatory for this visibly scoped question is the mismatch. Paragraph 46 remains a legitimate alternative for P5 FSPPF alone, despite its separate AMFF error; paragraph 59 supports the OBB head alone.

Canonical sources: `pmc11510794:p41:w0`, `pmc11510794:p46:w0`, `pmc11510794:p59:w0`.

Proposed correction: Retain the contradiction as an answer-review guard and optional evidence. Require it if an answer generalizes beyond the named account, or rewrite the question to ask about the conflict before keeping it mandatory. Preserve the historical approved-package score.

- `pmc11510794:p41:w0[200:353]`: Next, two AMFF modules are inserted between the two backbones, applied to the P3 and P4 layers, to obtain fused features with different receptive fields.
- `pmc11510794:p46:w0[277:400]`: The output of FSPPF, along with the outputs from the P3 and P5 layers’ AMFF modules, serves as the input to the neck layer.

Confidence: high. Existing labels remain unchanged.

### tech-stripe-frequencies

Question: Which sinusoidal frequencies, stripe counts and phase are tested for painted heating-device illumination?

Requested facts: Give both tested sinusoidal frequencies, their corresponding stripe counts and the phase.

Sufficient scoped answer: The paper reports 0.8 Hz for 20 stripes, 1.6 Hz for 40 stripes, and zero phase for both.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. Every numerical value is directly requested.
- `required_qualifications[0]`: necessary for accuracy. Keep the source's units and distinguish tested settings from universal optimum.
- `required_qualifications[1]` / reported label: necessary for accuracy. Attribution matters because Hz is the paper's label for generated spatial patterns.
- `required_qualifications[1]` / temporal or spatial conversion warning: conditional on additional claim. A monitor-refresh or cycles/mm interpretation would be an added claim requiring unavailable calibration.
- `forbidden_claims[0]`: conditional on additional claim. Optimality for all painted surfaces would be a new claim.

Evidence judgment: Paragraph 18 supplies both pairs and theta=0. Paragraph 17 explicitly identifies theta as phase, so their joint requirement is defensible for strict factual grounding. Paragraph 18 mentions phase in its opening sentence and an ordinary reader can infer the symbol, but deleting the definition is an unresolved sufficiency choice, not a confirmed correction. Do not count the two-passage requirement as a defect merely because theta is familiar.

Canonical sources: `pmc11768589:p17:w0`, `pmc11768589:p18:w0`.

Unresolved: Whether paragraph 18 alone is an acceptable zero-phase alternative depends on the agreed allowance for local symbol inference. Retain the existing joint support pending review.

Confidence: high. Existing labels remain unchanged.

### tech-adaptive-binarization

Question: What grayscale and adaptive-binarization preprocessing is applied to structured-illumination heater images, and is it applied to bright-field images?

Requested facts: Describe grayscale conversion and adaptive binarization for structured illumination, including whether bright-field images receive it.

Sufficient scoped answer: The structured-image pipeline converts RGB to grayscale and applies adaptive binarization to reduce environmental-light effects. The paper explicitly excludes bright-field images from this processing.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. Both transformations and the bright-field exception are requested; the purpose explains the processing.
- `required_qualifications[0]`: conditional on additional claim. Threshold or window size would be an additional implementation claim.
- `forbidden_claims[0]`: necessary for accuracy. Applying the same processing to both modes contradicts the explicit exception.

Evidence judgment: The current p29+p22 joint alternative is sufficient. Paragraph 29 names structured illumination but does not name grayscale or adaptive binarization. Paragraph 22 names both transformations and explicitly excludes bright-field in the same passage, which supports the visible two-mode question without requiring another passage to restate structured-mode identity. A p22-only alternative is a justified candidate under ordinary contextual reading, with its anaphoric opening disclosed. It is not an exact source contradiction in the existing labels.

Canonical sources: `pmc11768589:p22:w0`, `pmc11768589:p29:w0`.

Proposed correction: Use the complete paragraph including its explicit bright-field exclusion, not only the first sentence. An owner may still prefer a literal named-mode link; report that stricter interpretation separately rather than treating this correction as already approved.

- `pmc11768589:p22:w0[0:310]`: Afterwards, the images were subjected to processing through the conversion RGB to grey scale and the application of adaptive binarization to reduce the effect of the environmental lighting (Figure 2b). It should be emphasized that images obtained via bright field illumination were not subjected to processing.

Unresolved: Paragraph 22 begins 'Afterwards, the images'. The proposed alternative permits resolving its scope using the same paragraph's bright-field exclusion and the visible question's two named modes.

Confidence: high. Existing labels remain unchanged.

### tech-imagenet-initialization

Question: Which pretraining dataset and input image size are reported for the transferred ResNet-50 and Inception V3 classifiers?

Requested facts: Identify the pretraining dataset and study input size for both transferred classifiers.

Sufficient scoped answer: Both ResNet-50 and Inception V3 were pretrained on ImageNet and use 450 by 450 inputs in this study.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. The dataset and study dimensions are requested.
- `required_qualifications[0]`: necessary for accuracy. Distinguish prior pretraining from the study's fine-tuning.
- `forbidden_claims[0]`: conditional on additional claim. A million new heater photographs would be an added false claim.

Evidence judgment: Paragraph 26 alone directly supports all facts. Its two-span input-size alternative keeps the antecedent for 'these pre-trained CNNs' within the same passage. The p26+p29 alternative is redundant at whole-passage scoring because p26 already states the dimensions, but it does not make extra retrieval mandatory. Paragraph 25's 450 dimensions refer to the scratch-built CNN and cannot alone establish the transferred pair's inputs.

Canonical sources: `pmc11768589:p26:w0`.

Confidence: high. Existing labels remain unchanged.

### tech-stable-camera

Question: When the transparent cover is photographed twice, what stops it from shifting relative to the lens?

Requested facts: Identify what physically preserves the camera/sample geometry between captures.

Sufficient scoped answer: A flexible arm holder keeps the lens and sample in a fixed relative position.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. The support device and its role answer the question.
- `required_qualifications[0]`: conditional on additional claim. A measured registration-error guarantee would be an additional claim.
- `forbidden_claims[0]`: conditional on additional claim. An active stabilization algorithm would be an added unsupported mechanism.

Evidence judgment: Paragraph 27 explicitly gives the holder's purpose. Paragraph 25 merely inventories the holder and does not state why it prevents shifting; no omitted sufficient alternative was found.

Canonical sources: `pmc11510794:p27:w0`.

Confidence: high. Existing labels remain unchanged.

### tech-turn-and-flip-labels

Question: How can the aircraft-cover training pictures be turned and reflected without drawing their defect outlines again?

Requested facts: Explain how image rotations and reflections preserve usable defect annotations without redrawing.

Sufficient scoped answer: Apply each rotation and mirror transformation to the image and its labels together, correcting or deleting labels that move outside the image.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]` / rotate and mirror together: explicitly requested. Simultaneous image/label transformations answer how redrawing is avoided.
- `required_claims[0]` / 90-degree eightfold example: optional background. The eightfold count is an illustrative example, not required to explain transformed labels.
- `required_claims[0]` / out-of-frame labels: necessary for accuracy. For the question's unrestricted turning operation, labels that leave the frame need correction or removal.
- `required_qualifications[0]`: conditional on additional claim. Specify 90-degree rotations and mirroring if adding the eightfold example.
- `forbidden_claims[0]`: necessary for accuracy. Do not imply arbitrary rotations preserve all content and boxes.

Evidence judgment: All existing groups are accurately supported by paragraph 34's first window. The eightfold group is optional detail but imposes no separate passage. The numerical example is not grounds to accept paragraph 34's second window alone, which lacks the core image/label transformation instruction.

Canonical sources: `pmc11510794:p34:w0`.

Proposed correction: The visible how-question does not ask the augmentation factor. Preserve overflow safeguards; expected complete-evidence passage requirement is unchanged because all facts are in p34:w0.

Confidence: high. Existing labels remain unchanged.

### tech-manual-outline-union

Question: If damage has a different outline in the two pictures of the aircraft cover, how do the annotators reconcile the boundary?

Requested facts: Explain how annotators reconcile a defect's differing outlines across two illumination views.

Sufficient scoped answer: They manually adjust the boundaries and select the union outer contour when the views differ.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]` / manual adjustment and union outer contour: explicitly requested. Manual reconciliation and the union rule directly answer the boundary question.
- `required_claims[0]` / annotation files checked: optional background. Checking every annotation file is related quality control, not necessary to identify how the boundary is reconciled.
- `required_qualifications[0]`: optional background. Visibility under one illumination explains why manual work is useful but is supplementary to the explicitly stated differing-outline condition.
- `forbidden_claims[0]`: necessary for accuracy. Accepting model output without review would contradict the manual reconciliation.

Evidence judgment: Paragraph 33 supports all groups and supplies their local context. The visibility qualification and annotation-file checks add requested-answer scope but do not consume extra passage slots. Paragraph 32's automated rectangle generation does not establish the union boundary.

Canonical sources: `pmc11510794:p33:w0`.

Proposed correction: Keep union and manual adjustment mandatory. Both optional facts live in the same necessary passage, so the whole-passage completeness result should not change.

Confidence: high. Existing labels remain unchanged.

### tech-small-photo-supply

Question: How did the heater researchers enlarge a limited supply of surface photographs before fitting their classifiers?

Requested facts: Explain how the heater study expanded a limited photo dataset before classifier training.

Sufficient scoped answer: They extracted four 450 by 450 crops from each 808 by 608 image, then augmented the crops to 500 images per defect category.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]` / crop then augment: explicitly requested. Cropping followed by augmentation is the requested enlargement method.
- `required_claims[0]` / numerical recipe details: optional background. Exact raw/crop dimensions and the 500-image target are useful concrete study details but the how-question does not explicitly demand every number.
- `required_qualifications[0]`: conditional on additional claim. Clarify derived versus independent samples if stating the 500 count or interpreting sample independence.
- `forbidden_claims[0]`: necessary for accuracy. Do not reinterpret augmentation as acquisition of 500 independent heaters.

Evidence judgment: Paragraph 21 directly supports both stages and all numbers. The two spans for augmentation stay in one passage and connect the 500-image goal with the augmentation operation. Its omitted rotation/flip examples could improve an answer but do not justify adding a new mandatory detail list. Keeping current factual groups is a reasonable specific-answer design choice; scope should be explicit in any answer rubric.

Canonical sources: `pmc11768589:p21:w0`.

Unresolved: The desired granularity of a how-question is a rubric choice. The current numerical recipe is correct and costs no extra passage; no score-changing simplification is proposed.

Confidence: high. Existing labels remain unchanged.

### tech-both-checks-clean

Question: Can a heater pass inspection after looking undamaged under the striped screen alone, and what happens next?

Requested facts: Decide whether a structured-only clean result is enough and describe the next test and final pass rule.

Sufficient scoped answer: No. An OK under the sinusoidal pattern triggers a bright-field check, and both modes must return OK for a final pass.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. The sequence and two-mode final acceptance rule answer both parts.
- `required_qualifications[0]`: conditional on additional claim. A zero-miss guarantee would be an extra claim. Calling this the reported decision rule is sufficient.
- `forbidden_claims[0]`: necessary for accuracy. A one-mode pass contradicts the requested decision rule.

Evidence judgment: Paragraph 29 proves sequence; paragraphs 30, 1 and 48 each explicitly state the two-mode OK requirement. The final-rule alternatives do not establish sequence, so a second passage for that fact is warranted. Paragraph 29 strongly implies the final rule but does not explicitly state the final classification; retaining the second group is defensible and avoids substituting topical overlap for complete decision logic.

Canonical sources: `pmc11768589:p29:w0`, `pmc11768589:p30:w0`, `pmc11768589:p1:w0`, `pmc11768589:p48:w0`.

Confidence: high. Existing labels remain unchanged.

### tech-daylight-interference

Question: Why could changing daylight hide a mark in the heater photographs, and how did the researchers make the mark easier to see?

Requested facts: Explain the contrast problem from daylight changes and the tested way to make defects easier to see.

Sufficient scoped answer: Uncontrolled ambient light reduces contrast and can hide a scratch. Processing the sinusoidal-pattern images produces high-contrast defect regions.

Answerability: The requested facts have sufficient prose support in the indexed passages. No omitted table, figure or equation is required to report them.

Requirement classification:

- `required_claims[0]`: explicitly requested. The contrast mechanism and processing mitigation directly answer the question.
- `required_qualifications[0]`: conditional on additional claim. The proposed-tunnel distinction matters only if an answer introduces containment. It need not discuss an enclosure at all to answer the visible question.
- `forbidden_claims[0]`: necessary for accuracy. Calling a tunnel the tested fix would be inaccurate.

Evidence judgment: Paragraph 34 proves all approved groups. The containment-scope group partly contains necessary experimental context, uncontrolled light, but also forces the optional tunnel proposal. Separate those subfacts in a revised rubric. No extra passage is caused because all quoted text is already in the core support passage.

Canonical sources: `pmc11768589:p34:w0`.

Proposed correction: Keep uncontrolled ambient illumination in the requested explanation; make proposed containment conditional on discussing an enclosure. Passage-level completeness should stay unchanged.

Confidence: high. Existing labels remain unchanged.

## Realism and dependence

These cases mostly ask for named hardware, architecture details or a source-specific procedure. The paraphrases provide useful vocabulary variation, but their facts remain clustered within the same two studies. Glass illumination, glass boundary labeling and hardware stability all reuse one acquisition setting. Heater binarization and daylight interference reuse the same image-processing pipeline. Successes on these questions are therefore correlated, not independent evidence across many research domains.

The AMFF question's canonical paragraph number is evaluation-specific, and explicitly cites a figure excluded from retrieval. That makes it useful for testing a carefully scoped paper lookup but weak evidence of broad user realism. Source scope and legitimate inference rules should be decided before a revised score is interpreted. No score effect, model advantage or generated-answer accuracy is claimed in this reviewer artifact.
