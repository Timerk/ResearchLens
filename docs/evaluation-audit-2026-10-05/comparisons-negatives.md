# Comparison and negative-case audit

AI-assisted source audit, 2026-10-05. These are proposals, not a replacement human approval. All nine comparisons and fourteen negative cases are included. Judgments were recorded without reading cached retrieval outcomes. Exact source quotes and XML locators are in [the case record](comparisons-negatives.json).

The negative audit checks pinned XML prose, tables, formulas and captions. External figure pixels were not re-inspected. Earlier development-only review entries report a full-figure check; that is historical AI review, not new independent verification.

## tech-compare-fusion

Question: How do the canopy and painted heating-device studies differ in their illumination modalities and fusion levels?

Answerability: Answerable from indexed passages.

Requested facts: Identify both illumination modes in each paper. Distinguish canopy RGB data fusion and ADMF-Net feature fusion from heater decision fusion.

All 5 groups and all current alternatives support their facts in context. Group part-3 unnecessarily pairs canopy p40 with p5: p5 itself names the expanded model and says feature-level fusion. Add the p5 span alone. This does not permit a generic fusion taxonomy as model-specific evidence.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_claims[0]: Canopy inspection combines forward/backward lighting with RGB data-level fusion and an ADMF-Net feature-level method. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_claims[1]: Painted heating-device inspection combines deflectometry/bright illumination with decision-level fusion. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_qualifications[0]: These are different tasks and datasets; no common-benchmark superiority follows. | Conditional on an additional claim | A claim of comparative superiority would need matched tasks/data; a descriptive fusion comparison need not volunteer a performance disclaimer. |
| forbidden_claims[0]: Directly ranking the two approaches' accuracies across different datasets. | Conditional on an additional claim | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |

Proposed action: Add pmc11510794:p5:w0 [515,766) alone for part-3; retain existing alternatives and all five facts.

Source anchors: pmc11510794:p5:w0, pmc11510794:p59:w0, pmc11768589:p1:w0, pmc11768589:p30:w0

## tech-unrelated

Question: Who composed the music for the opera The Magic Flute?

Answerability: Unsupported by the source.

Requested facts: Who composed the music for the opera The Magic Flute?

The pinned papers study optical surface inspection, detection networks and reconstruction. Their methods/results, tables and captions do not answer this unrelated question. External general knowledge is outside the document-only contract.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: This technical corpus is not evidence for an unrelated music-history answer. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: An answer supplied from general knowledge rather than these documents. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: All four pinned papers' methods/results; no positive support anchor.

## tech-missing-shared-cpu-cost

Question: Which of the four methods has the lowest total CPU inference cost per detected defect when all four are tested on the identical glass-canopy benchmark?

Answerability: Unsupported by the source.

Requested facts: A matched four-method CPU cost-per-defect ranking on the same canopy data.

The four source methods/results describe different materials, tasks and hardware. Hardware specifications and runtime fragments cannot supply the absent common experiment.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: No full original reports the requested identical-canopy-benchmark CPU cost-per-defect comparison; separate training hardware and task metrics cannot establish such a ranking. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| required_qualifications[1]: No full original reports the requested identical-canopy-benchmark CPU cost-per-defect comparison; separate training hardware and task metrics cannot establish such a ranking. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| required_qualifications[2]: The requested result is absent from the reviewed full original(s), including tables, formulas and figures. Listed passage references are contextual anchors, not positive evidence or proof of absence; abstain from the requested unsupported result. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: An invented cost ranking. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |
| forbidden_claims[1]: Converting unrelated timing or accuracy figures into a shared-benchmark result. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: pmc11510794:p48:w0, pmc11768589:p24:w0, pmc10934137:p17:w0, pmc11121878:p38:w0

## tech-compare-localization-outputs

Question: How do the canopy detector and the two-stage autoencoder represent where a defect is?

Answerability: Answerable from indexed passages.

Requested facts: Name the canopy detector's geometric output. Explain the autoencoder's spatial defect representation.

All 2 groups and 4 alternatives are supported. Canopy p31 explicitly says annotation AND detection, while p41/p59 explicitly name rotated-box prediction. Autoencoder p40 explicitly ties residual localization to this method. Its p6 gives a general methodological statement; p6 alone remains unresolved as model-specific evidence and is not added. A p6+p40 alternative would consume unnecessary passages because p40 already suffices.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_claims[0]: Canopy defects use oriented bounding boxes. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_claims[1]: The autoencoder localizes defects through the residual between input and reconstruction. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_qualifications[0]: The outputs serve different inspection tasks. | Necessary to make the requested answer accurate | Keep detection boxes distinct from reconstruction residuals. |
| required_qualifications[1]: Different tasks and datasets; this is not a common-benchmark performance ranking. | Conditional on an additional claim | Matched-benchmark performance is only relevant if an answer adds a ranking. |
| forbidden_claims[0]: The autoencoder reports the same rotated-box labels as the canopy detector. | Necessary to make the requested answer accurate | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |
| forbidden_claims[1]: Claiming a head-to-head evaluation on identical data. | Conditional on an additional claim | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |

Proposed action: No scoring change. Keep p6 as supplementary conceptual context, pending attribution review.

Source anchors: pmc11510794:p31:w0, pmc11510794:p41:w0, pmc11510794:p59:w0, pmc11121878:p40:w0

## tech-compare-training-splits

Question: Compare the reported training/test partition in the canopy dataset with the painted heater dataset.

Answerability: Answerable from indexed passages.

Requested facts: Report each training/test split with the correct units and attribution.

Both groups each have a sufficient single-passage alternative. Canopy p36 reports 1576/176 pairs and describes this approximately as 9:1. Heater p23 reports 80/20 images. Neither the split prose nor canopy Table 1, which counts defect objects, proves sample independence. Exact counts plus ratio are a reasonable reference-answer choice, not a new reason to require other passages.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_claims[0]: Canopy uses 1576/176 image pairs, described as 9:1. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_claims[1]: Painted surfaces use 80% training and 20% testing. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_qualifications[0]: Pairs and individual images are different counting units; neither passage establishes independence after augmentation. | Necessary to make the requested answer accurate | Pairs versus images are necessary units. The additional statement about post-augmentation independence is conditional on a leakage or independence claim. |
| required_qualifications[1]: Different tasks and datasets; this is not a common-benchmark performance ranking. | Conditional on an additional claim | The question does not request a performance ranking. |
| forbidden_claims[0]: These percentages prove that both splits are leakage-free. | Necessary to make the requested answer accurate | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |
| forbidden_claims[1]: Claiming a head-to-head evaluation on identical data. | Conditional on an additional claim | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |

Proposed action: Keep evidence. Split the compound first qualification into a mandatory unit distinction and a conditional independence guard in a future answer rubric.

Source anchors: pmc11510794:p36:w0, pmc11768589:p23:w0

## tech-compare-training-computers

Question: What software frameworks and GPU/memory configurations are reported for canopy training and painted-surface training?

Answerability: Answerable from indexed passages.

Requested facts: Report software frameworks, GPU identities, GPU memory where reported, and system RAM for each study.

All 3 groups are supported by two passages. Canopy p48 separates 16GB VRAM from 48GB system memory and states PyTorch/CUDA versions. Heater p24 states Keras/TensorFlow, 930MX and 8GB RAM. Requiring another hardware or timing passage is unnecessary. Versions are a reasonable interpretation of reported framework configurations.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_claims[0]: Canopy uses PyTorch 2.2.2 with CUDA 11.8, an RTX 4080 with 16GB VRAM and 48GB system memory. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_claims[1]: Painted surfaces use Keras with TensorFlow, a GeForce 930MX and 8GB RAM. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_qualifications[0]: Reported setups are not matched computational-cost experiments. | Conditional on an additional claim | Hardware descriptions need a matched-cost caveat only when drawing a speed/cost inference. |
| required_qualifications[1]: Different tasks and datasets; this is not a common-benchmark performance ranking. | Conditional on an additional claim | No ranking is requested. |
| forbidden_claims[0]: Either machine is demonstrated faster on the other study's task. | Conditional on an additional claim | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |
| forbidden_claims[1]: Claiming a head-to-head evaluation on identical data. | Conditional on an additional claim | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |

Proposed action: Keep evidence; make benchmarking disclaimers conditional in an answer rubric.

Source anchors: pmc11510794:p48:w0, pmc11768589:p24:w0

## tech-compare-data-expansion

Question: Compare the canopy study's Mosaic-4 transformations with the painted heater study's crop-based data expansion.

Answerability: Answerable from indexed passages.

Requested facts: Describe the Mosaic-4 transformations and the heater crop/augmentation sequence.

The 2 groups are sufficient and each points to the exact pipeline. Canopy p35 lists combinations, scale/translation, contrast/exposure and noise. Heater p21 lists four crops, rotation, shifts, zoom, shear and flips. The latter's detailed numeric augmentation settings are optional for this question; its current expected claim does not demand them. The composite group makes partial coverage coarse but does not inflate passage demand.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_claims[0]: Canopy training uses Mosaic-4 image combinations, scaling/translation, contrast/exposure changes and noise. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_claims[1]: Heater images yield four crops followed by rotations, shifts, zoom, shear and flips. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_qualifications[0]: These procedures increase training variation, not independently acquired samples. | Necessary to make the requested answer accurate | Describe transformations as augmentation, not new acquisitions. A separate sentence about independence is optional when the answer already makes that distinction. |
| required_qualifications[1]: Different tasks and datasets; this is not a common-benchmark performance ranking. | Conditional on an additional claim | No matched performance ranking is requested. |
| forbidden_claims[0]: Both papers used the identical augmentation pipeline. | Necessary to make the requested answer accurate | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |
| forbidden_claims[1]: Claiming a head-to-head evaluation on identical data. | Conditional on an additional claim | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |

Proposed action: No scoring change. Do not import optional transformation parameter values into mandatory answer requirements.

Source anchors: pmc11510794:p35:w0, pmc11768589:p21:w0

## tech-compare-evaluation-metrics

Question: Which metrics quantify canopy object-detection performance and autoencoder anomaly-detection performance, and can their numerical scores be ranked directly?

Answerability: Answerable from indexed passages.

Requested facts: Identify canopy detection and autoencoder anomaly metrics. Answer whether their reported values support a direct ranking.

Both groups are correctly supported: canopy p47 defines mAP50 and mAP50-95/IoU; autoencoder p38 identifies AuROC and its MVTec setting. The no-direct-ranking conclusion is an inference from the metric/task distinction, not a verbatim statement in either source. Complete evidence checks the ingredients, not whether an answer draws that inference. No extra disclaimer passage should be required.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_claims[0]: Canopy reports mAP50 and mAP50-95 over IoU thresholds. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_claims[1]: The autoencoder reports area under the ROC curve (AuROC); the task-specific metrics do not support a direct ranking. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_qualifications[0]: The metrics measure different outputs and are evaluated on different datasets. | Necessary to make the requested answer accurate | Different metric definitions and tasks explain why numeric ranking is invalid. |
| required_qualifications[1]: Different tasks and datasets; this is not a common-benchmark performance ranking. | Explicitly requested | Unlike the other comparison questions, this one explicitly asks about ranking. The second qualification largely duplicates the first. |
| forbidden_claims[0]: 98% mAP means the same error rate as 98% AuROC. | Necessary to make the requested answer accurate | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |
| forbidden_claims[1]: Claiming a head-to-head evaluation on identical data. | Conditional on an additional claim | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |

Proposed action: Keep groups and mandatory non-comparability requirement. Deduplicate the answer qualification without changing retrieval scoring.

Source anchors: pmc11510794:p47:w0, pmc11121878:p38:w0

## tech-compare-optical-cues

Question: What optical cues reveal scratches/dents on painted heaters and particle defects on non-patterned wafers?

Answerability: Answerable from indexed passages.

Requested facts: Explain how reflected stripes reveal heater scratches/dents and scattered light reveals wafer particles.

Both single-passage groups are factually sufficient. Heater p35 names 3D scratches/dents and reflected-pattern distortion; wafer p6 names defect-scattered light on a dark background. Generic references to illumination are not sufficient alternatives. No unsupported interchangeability of sensitivity is licensed.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_claims[0]: Heater structured illumination detects 3D marks through distortion of reflected patterns. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_claims[1]: Wafer dark-field inspection collects defect-scattered light against a dark background. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_qualifications[0]: The two studies do not establish identical material response or sensitivity. | Conditional on an additional claim | A common material response/sensitivity claim would need additional support; merely describing distinct cues does not require this sentence. |
| required_qualifications[1]: Different tasks and datasets; this is not a common-benchmark performance ranking. | Conditional on an additional claim | No performance ranking is requested. |
| forbidden_claims[0]: The wafer method depends on a reflected sinusoidal screen pattern. | Necessary to make the requested answer accurate | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |
| forbidden_claims[1]: Claiming a head-to-head evaluation on identical data. | Conditional on an additional claim | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |

Proposed action: Keep evidence and reject unsupported sensitivity claims; classify unprompted disclaimers as conditional in the answer rubric.

Source anchors: pmc11768589:p35:w0, pmc10934137:p6:w0

## tech-compare-network-inputs

Question: Compare the patch size used for autoencoder training with the input image size of the transferred heater classifiers.

Answerability: Answerable from indexed passages.

Requested facts: Report the autoencoder training patch dimensions and the transferred heater classifiers' input dimensions.

Both groups are supported. Autoencoder p17 states 128 by 128 patches. Heater p26 identifies both transferred CNNs and 450 by 450 inputs in one canonical passage. The p26+p29 joint alternative is redundant but harmless because p26 alone is an accepted complete alternative. Heater p25 describes the scratch-built network; p21/p29 crop sizes alone do not independently identify the transferred pair. Do not loosen those model-scope restrictions.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_claims[0]: Autoencoder training divides images into 128 by 128 patches. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_claims[1]: Transferred heater classifiers use 450 by 450 inputs. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_qualifications[0]: Patch size is distinct from the size of the complete resized image. | Necessary to make the requested answer accurate | 128 by 128 patches must not be described as the full 512 by 512 resized source image. |
| required_qualifications[1]: Different tasks and datasets; this is not a common-benchmark performance ranking. | Conditional on an additional claim | No ranking is requested. |
| forbidden_claims[0]: Both methods consume 128 by 128 whole images. | Necessary to make the requested answer accurate | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |
| forbidden_claims[1]: Claiming a head-to-head evaluation on identical data. | Conditional on an additional claim | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |

Proposed action: No scoring change. Retain the approved contextual antecedent in p26.

Source anchors: pmc11121878:p17:w0, pmc11768589:p26:w0, pmc11768589:p29:w0

## tech-compare-network-roles

Question: How do the two backbones in ADMF-Net differ in purpose from the encoder and decoder in the autoencoder model?

Answerability: Answerable from indexed passages.

Requested facts: Contrast the two modality-specific feature extractors and downstream fusion/detection with the encoder's compression and decoder's reconstruction.

All 3 groups and 4 alternatives are supported. Three spans in the p41 alternative occupy one passage, not three slots. p59 also supplies the whole canopy role. Autoencoder p16 supplies compression and transposed-convolution reconstruction. The particular convolution mechanism is useful optional implementation detail for a purpose question; it occupies the same passage as the requested role, so removing it would not repair a passage-selection failure. No relaxation is proposed.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_claims[0]: ADMF-Net backbones separately extract features from the two lighting modalities for fusion and detection. | Explicitly requested | Supported by the cited passages; preserve scientific scope. |
| required_claims[1]: The autoencoder compresses an image and decodes it with transposed convolutions to reconstruct it. | Explicitly requested | The transposed-convolution subclause is optional background. |
| required_qualifications[0]: Two branches in a detector are not the same as compression/reconstruction stages. | Necessary to make the requested answer accurate | The role distinction is the requested comparison. |
| required_qualifications[1]: Different tasks and datasets; this is not a common-benchmark performance ranking. | Conditional on an additional claim | No performance ranking is requested. |
| forbidden_claims[0]: The ADMF-Net backbones form an encoder-decoder reconstruction pair. | Necessary to make the requested answer accurate | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |
| forbidden_claims[1]: Claiming a head-to-head evaluation on identical data. | Conditional on an additional claim | A prohibition on making this inaccurate assertion, not a mandatory disclaimer sentence or extra retrieval group. |

Proposed action: Keep retrieval groups. Mark 'transposed convolutions' optional in a future answer rubric while preserving compression/reconstruction as required.

Source anchors: pmc11510794:p41:w0, pmc11510794:p59:w0, pmc11121878:p16:w0

## tech-unrelated-recipe

Question: What ingredients and cooking times are needed for a traditional spaghetti carbonara?

Answerability: Unsupported by the source.

Requested facts: What ingredients and cooking times are needed for a traditional spaghetti carbonara?

The pinned papers study optical surface inspection, detection networks and reconstruction. Their methods/results, tables and captions do not answer this unrelated question. External general knowledge is outside the document-only contract.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: The four surface-inspection papers do not support this unrelated question; abstain from a document-only answer. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Answering from general knowledge or inventing a technical-source citation. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: All four pinned papers' methods/results; no positive support anchor.

## tech-unrelated-inheritance-law

Question: How is an intestate estate divided under current German inheritance law?

Answerability: Unsupported by the source.

Requested facts: How is an intestate estate divided under current German inheritance law?

The pinned papers study optical surface inspection, detection networks and reconstruction. Their methods/results, tables and captions do not answer this unrelated question. External general knowledge is outside the document-only contract.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: The four surface-inspection papers do not support this unrelated question; abstain from a document-only answer. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Answering from general knowledge or inventing a technical-source citation. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: All four pinned papers' methods/results; no positive support anchor.

## tech-unrelated-planet-moons

Question: How many confirmed moons does Jupiter have as of September 2026?

Answerability: Unsupported by the source.

Requested facts: How many confirmed moons does Jupiter have as of September 2026?

The pinned papers study optical surface inspection, detection networks and reconstruction. Their methods/results, tables and captions do not answer this unrelated question. External general knowledge is outside the document-only contract.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: The four surface-inspection papers do not support this unrelated question; abstain from a document-only answer. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Answering from general knowledge or inventing a technical-source citation. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: All four pinned papers' methods/results; no positive support anchor.

## tech-unrelated-exchange-rate

Question: What was the euro-to-yen closing exchange rate on 1 September 2026?

Answerability: Unsupported by the source.

Requested facts: What was the euro-to-yen closing exchange rate on 1 September 2026?

The pinned papers study optical surface inspection, detection networks and reconstruction. Their methods/results, tables and captions do not answer this unrelated question. External general knowledge is outside the document-only contract.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: The four surface-inspection papers do not support this unrelated question; abstain from a document-only answer. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Answering from general knowledge or inventing a technical-source citation. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: All four pinned papers' methods/results; no positive support anchor.

## tech-unrelated-database-isolation

Question: Which SQL transaction isolation level prevents phantom reads?

Answerability: Unsupported by the source.

Requested facts: Which SQL transaction isolation level prevents phantom reads?

The pinned papers study optical surface inspection, detection networks and reconstruction. Their methods/results, tables and captions do not answer this unrelated question. External general knowledge is outside the document-only contract.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: The four surface-inspection papers do not support this unrelated question; abstain from a document-only answer. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Answering from general knowledge or inventing a technical-source citation. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: All four pinned papers' methods/results; no positive support anchor.

## tech-unrelated-vaccination

Question: What is the recommended adult hepatitis B vaccination schedule?

Answerability: Unsupported by the source.

Requested facts: What is the recommended adult hepatitis B vaccination schedule?

The pinned papers study optical surface inspection, detection networks and reconstruction. Their methods/results, tables and captions do not answer this unrelated question. External general knowledge is outside the document-only contract.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: The four surface-inspection papers do not support this unrelated question; abstain from a document-only answer. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Answering from general knowledge or inventing a technical-source citation. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: All four pinned papers' methods/results; no positive support anchor.

## tech-missing-canopy-service-life

Question: How many years of flight service remain for a canopy after its largest detected crack is repaired?

Answerability: Unsupported by the source.

Requested facts: Remaining flight years after a crack repair.

Canopy p30 describes defects and p61 limitations; the paper evaluates imaging/detection, not structural fatigue, repair validation or remaining-service-life prediction. Tables 1-5 contain counts, settings and detection metrics.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: Defect imaging and a detection method do not establish a structural-fatigue or remaining-life model. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| required_qualifications[1]: The requested result is absent from the reviewed full original(s), including tables, formulas and figures. Listed passage references are contextual anchors, not positive evidence or proof of absence; abstain from the requested unsupported result. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Inventing the requested result or supplying it from external knowledge. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |
| forbidden_claims[1]: Treating a nearby passage or an omitted table/formula as evidence for the requested result. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: pmc11510794:p30:w0, pmc11510794:p61:w0

## tech-missing-heater-energy

Question: How many joules per inspected heater does the complete camera, monitor and CNN system consume?

Answerability: Unsupported by the source.

Requested facts: End-to-end camera, display and CNN electrical energy per inspected heater.

Heater p16/p24 describe hardware and p29 a 5-second acquisition cycle. No measured watts, duty-cycle accounting or joules-per-heater result is given. A timing interval alone cannot establish energy.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: Hardware descriptions are not measured end-to-end energy consumption. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| required_qualifications[1]: The requested result is absent from the reviewed full original(s), including tables, formulas and figures. Listed passage references are contextual anchors, not positive evidence or proof of absence; abstain from the requested unsupported result. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Inventing the requested result or supplying it from external knowledge. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |
| forbidden_claims[1]: Treating a nearby passage or an omitted table/formula as evidence for the requested result. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: pmc11768589:p16:w0, pmc11768589:p24:w0, pmc11768589:p29:w0

## tech-missing-wafer-live-cells

Question: What sensitivity and specificity does the wafer TDI system achieve for malignant cells in live human blood?

Answerability: Unsupported by the source.

Requested facts: Clinical sensitivity and specificity for malignant cells in live human blood.

Wafer p13 tests sprayed 0.5 micrometre PSL particle surrogates on polished wafers; p17 calls the setup experimental. Introductory references to biological imaging are other work. No relevant patient/cell validation is reported.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: A PSL-particle experiment on a wafer is not a biological diagnostic validation. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| required_qualifications[1]: The requested result is absent from the reviewed full original(s), including tables, formulas and figures. Listed passage references are contextual anchors, not positive evidence or proof of absence; abstain from the requested unsupported result. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Inventing the requested result or supplying it from external knowledge. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |
| forbidden_claims[1]: Treating a nearby passage or an omitted table/formula as evidence for the requested result. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: pmc10934137:p13:w0, pmc10934137:p17:w0

## tech-missing-autoencoder-ct

Question: What patient-level cancer detection accuracy does the two-stage autoencoder achieve on hospital CT scans?

Answerability: Unsupported by the source.

Requested facts: Patient-level CT cancer detection accuracy for the proposed model.

Autoencoder p38 uses MVTec leather, carpet, hazelnut, pill, wood and tile, with AuROC; p39 compares anomaly methods. Related medical work cannot be reassigned to this model or converted into patient accuracy.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: MVTec surface-image evaluation does not supply patient-level CT results. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| required_qualifications[1]: The requested result is absent from the reviewed full original(s), including tables, formulas and figures. Listed passage references are contextual anchors, not positive evidence or proof of absence; abstain from the requested unsupported result. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Inventing the requested result or supplying it from external knowledge. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |
| forbidden_claims[1]: Treating a nearby passage or an omitted table/formula as evidence for the requested result. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: pmc11121878:p38:w0, pmc11121878:p39:w0

## tech-missing-factory-warranty

Question: Which of the four systems reduced warranty returns most in a randomized trial across the same factories?

Answerability: Unsupported by the source.

Requested facts: A common-factory randomized comparison of warranty returns across all four systems.

Separate defect-detection experiments and industrial motivations do not report a randomized warranty-outcome trial. No source offers the common study design or outcome denominators.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: Separate inspection experiments do not supply a shared randomized factory-outcome trial. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| required_qualifications[1]: The requested result is absent from the reviewed full original(s), including tables, formulas and figures. Listed passage references are contextual anchors, not positive evidence or proof of absence; abstain from the requested unsupported result. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Inventing the requested result or supplying it from external knowledge. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |
| forbidden_claims[1]: Treating a nearby passage or an omitted table/formula as evidence for the requested result. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: pmc11510794:p61:w0, pmc11768589:p43:w0, pmc10934137:p17:w0, pmc11121878:p38:w0

## tech-missing-canopy-confidence-bounds

Question: What is the 95% bootstrap confidence interval across independent canopy collections for ADMF-Net's reported mAP50?

Answerability: Unsupported by the source.

Requested facts: A 95% bootstrap interval across independently collected canopy datasets.

Canopy p52/Table 4 and related tables report point metrics. mAP50-95 denotes IoU thresholds, not a 95% confidence interval. No independent-collection bootstrap method or interval is reported; the heater's separate 90% acceptance wording does not answer this question.

| Existing requirement | Classification | Reason |
| --- | --- | --- |
| required_qualifications[0]: A point metric from the canopy experiment is not a bootstrap interval across independent collections. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| required_qualifications[1]: The requested result is absent from the reviewed full original(s), including tables, formulas and figures. Listed passage references are contextual anchors, not positive evidence or proof of absence; abstain from the requested unsupported result. | Necessary to make the requested answer accurate | Document-only abstention is necessary; this explanatory wording is not mandatory. The archival full-figure absence claim is inherited from the prior AI review, not a new visual inspection. |
| forbidden_claims[0]: Inventing the requested result or supplying it from external knowledge. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |
| forbidden_claims[1]: Treating a nearby passage or an omitted table/formula as evidence for the requested result. | Necessary to make the requested answer accurate | Do not invent evidence or answer this document-only request from external knowledge. |

Proposed action: Keep negative and abstain from the requested result. Do not assign a positive evidence-completeness score.

Source anchors: pmc11510794:p47:w0, pmc11510794:p52:w0
