# Wafer and autoencoder development-case audit

This AI-assisted audit covers 11 development positives. It is not independent human review. All 11 visible questions are answerable from the indexed passages. No question requires omitted original-only material. There is a resolvable window-terminology ambiguity and an equation-number typo in the autoencoder paper, but neither makes the requested fact unsupported.

The requested facts appear before the annotation comparison for each case below. Existing annotations were visible during source review, so this is not a blinded annotation study. Cached retrieval rankings and case performance were not inspected. No held-out questions, paid API calls or generated answers were used. Approved artifacts remain unchanged.

The audit read all canonical prose for both papers, checked it against original XML, and inspected relevant MathML, table XML and figure captions. Figure pixels were not newly inspected. The existing `chunk_documents` and `prose_text` functions verified all 59 approved spans, both original-file hashes, and all 65 paragraph locations. Character intervals below are half-open offsets in canonical passage text. The JSON companion contains every original span, source identity, locator and requirement classification.

The strongest mismatch is `tech-wafer-exact`: its visible SNR question does not request an efficiency claim. If an answer adds that claim, the fixed-frequency and transmission-time conditions remain necessary. Separate original-package and proposed question-scoped results; do not rewrite historical scores.

Several current requirements are reasonable. The shortcut question needs the reason partial defect reconstruction harms localization. The Gaussian schedule needs enough context to identify standard deviation after formula removal. The AW-SSIM comparison must distinguish multiplication from weighted addition, not merely retrieve a passage mentioning SSIM.

| Source | Original SHA-256 | Canonical paragraphs checked |
| --- | --- | --- |
| [pmc10934137](https://pmc.ncbi.nlm.nih.gov/articles/PMC10934137/) | `a22c7ee300e05855e878b94f8700b4c4487487a37f7e145d56ae43be61f6d482` | 18 |
| [pmc11121878](https://pmc.ncbi.nlm.nih.gov/articles/PMC11121878/) | `f9f3b4eed5d04f9a8597b33fb21c76f944f659614e6b931f0913e352d1fa60a1` | 47 |

## Case-level judgments

### tech-wafer-exact

Question: What changes to TDI stages and column fixed pattern noise improve particle-defect SNR in the non-patterned wafer study?

Requested facts: Which direction to change the number of TDI stages. Which direction to change column fixed pattern noise. That these changes improve particle-defect SNR in the reported wafer experiment.

Sufficient scoped answer: Increase TDI stages and reduce column fixed pattern noise to improve particle-defect SNR in the reported experiment.

Confirmed question-to-expectation mismatch and an omitted sufficient alternative. The source is answerable and does not need an extraction change.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| Increasing stages and reducing CFPN improve SNR | explicitly requested | These are the two changes named in the question. |
| Without sacrificing detection efficiency | conditional on additional claim | The question does not ask about efficiency. Once this extra claim is made, its conditions must accompany it. |
| Reported result, not arbitrary-scanner guarantee | necessary for accuracy | The visible question already scopes the result to this study; preserving that scope is necessary but does not require a separate disclaimer sentence. |
| Fixed line frequency, excluded transmission time, no measured end-to-end throughput guarantee | conditional on additional claim | Necessary for the additional efficiency claim, not for the requested direction of SNR changes. |
| No invented numerical SNR gain | conditional on additional claim | If a numerical gain is volunteered, its evidence must support the number. The qualitative answer needs no number. |

Evidence judgments:

- `part-1`: Both abstract and conclusion support the full original combined claim. Their efficiency wording does not force an answer to repeat that extra claim when answering the narrower visible question. Verified locations: `pmc10934137:p18:w0[318:561]`, `pmc10934137:p1:w0[600:828]`.
- `efficiency-scope`: The approved p14 AND p16 combination is sufficient. It is overconstrained because p14 already says line frequency does not change. The entire efficiency group is conditional under the visible question. Verified locations: `pmc10934137:p14:w180[82:334]`, `pmc10934137:p16:w0[0:60]`.

Unresolved judgments:

- Owner judgment remains necessary before any new scoring contract is approved. The original package metric is valid for its documented broader package.

### tech-wafer-paraphrase

Question: In the wafer study, what caused the background stripes in the particle images, and how did the researchers reduce them?

Requested facts: What causes the stripe-like background. How the researchers reduce those stripes.

Sufficient scoped answer: The stripes are CFPN from mismatched column readout circuits. The researchers subtract particle-free background images from particle images.

Answerable from one indexed passage. A reasonable scope refinement has no passage-budget effect.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| Readout mismatch causes stripes/CFPN | explicitly requested | Answers the cause. |
| Particle-free background subtraction at different stages | explicitly requested | Answers the remedy; the stage detail locates the experiment. |
| Correlated dual sampling is incomplete | conditional on additional claim | Required if describing the circuit approach; useful background for the subtraction-only answer. |
| Do not claim subtraction removes every noise source | conditional on additional claim | A reduction claim does not license complete elimination. |

Evidence judgments:

- `part-1`: The expanded span identifies stripe-like CFPN and readout mismatch, not merely readout hardware. Verified locations: `pmc10934137:p15:w0[0:299]`.
- `part-2`: The exact subtraction sentence is sufficient. Verified locations: `pmc10934137:p15:w0[875:985]`.
- `cds-incomplete`: The sentence supports the claim, but this claim exceeds what a minimal correct answer needs. Verified locations: `pmc10934137:p15:w0[300:429]`.

### tech-autoencoder-exact

Question: What training examples are used in each stage of the two-stage autoencoder method, and how are stage-one weights used?

Requested facts: Training sample types in stage one. Training sample types in stage two. How the first-stage weights are used.

Sufficient scoped answer: Stage one uses only normal samples. Stage two uses normal and artificially defective samples and starts from stage-one weights.

Answerable; a confirmed omitted abstract alternative can correct evidence scoring without changing requirements.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| Normal-only stage one, normal/artificial stage two, first-stage weights | explicitly requested | All three components are directly requested. |
| Artificial examples do not imply real defects in stage one | necessary for accuracy | This guards the requested training-set distinction and is already conveyed by normal-only stage one. |
| No labeled real defects required for stage one | conditional on additional claim | The source explicitly says only normal samples. |

Evidence judgments:

- `part-1`: All five alternatives explicitly establish normal-only first-stage training. Verified locations: `pmc11121878:p17:w0[41:216]`, `pmc11121878:p1:w0[1008:1151]`, `pmc11121878:p44:w0[485:630]`, `pmc11121878:p46:w0[59:160]`, `pmc11121878:p8:w0[83:282]`.
- `part-2`: p8 and p46 explicitly name both sample types. The abstract alternative correctly joins p1:w0 and p1:w180 because the final noun crosses the boundary. p17 describes pairs and clean targets; it does not unambiguously say normal samples are separate stage-two inputs, so do not substitute it without deciding that interpretation. Verified locations: `pmc11121878:p1:w0[1152:1296]`, `pmc11121878:p1:w180[0:17]`, `pmc11121878:p46:w0[519:674]`, `pmc11121878:p8:w0[83:282]`.
- `part-3`: All current alternatives support transfer. The abstract contains a complete omitted transfer clause before its cutoff. Verified locations: `pmc11121878:p17:w0[534:663]`, `pmc11121878:p44:w0[631:807]`, `pmc11121878:p8:w0[83:282]`.

Unresolved judgments:

- The wording uses normal samples broadly; do not strengthen it to an unsupported claim about the exact batching of normal standalone inputs versus clean target images.

### tech-tdi-motion-sync

Question: How must TDI line frequency and charge-accumulation direction relate to wafer motion to avoid blur?

Requested facts: Relationship between line frequency and wafer speed. Relationship between charge accumulation direction and wafer motion.

Sufficient scoped answer: Match line frequency to wafer motion speed and make charge accumulation oppose wafer motion in the described optical system.

Answerable in prose despite omitted Equation 4. No equation is needed for the visible question.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| Frequency matches speed and charge accumulation opposes wafer motion | explicitly requested | Both relationships are in the question and p10. |
| Equation omitted; do not invent constants | conditional on additional claim | An equation is not requested. Its omission is an extraction fact rather than mandatory answer content. |
| Increasing frequency alone does not guarantee sharp images at arbitrary speeds | conditional on additional claim | The required relationship is matching, not a monotonic setting recommendation. |

Evidence judgments:

- `part-1`: p10 explicitly establishes the matching relationship. Verified locations: `pmc10934137:p10:w0[123:396]`.
- `part-2`: The same span is sufficient; p7 supplies another direction example. The p7 example alone does not establish the line-frequency relationship. Verified locations: `pmc10934137:p10:w0[123:396]`.

### tech-aw-ssim-combination

Question: How does AW-SSIM combine the luminance, contrast and structure sub-functions differently from standard SSIM?

Requested facts: How the three components are combined in AW-SSIM versus standard SSIM. How AW-SSIM weights those components.

Sufficient scoped answer: AW-SSIM uses a weighted sum of the same luminance, contrast and structure values instead of multiplying the components. Each component has a constant coefficient selected for the training sample type.

Answerable from indexed prose. The source p26 mistakenly cites Equation 6 for AW-SSIM addition; original MathML puts the product in Equation 6 and sum in Equation 7. The annotation captures the correct operation and does not reproduce this citation typo.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| Addition rather than multiplication; component coefficients | explicitly requested | This is the combination difference the question asks about. |
| Same component calculations | necessary for accuracy | A useful comparison distinguishes changed combination from unchanged component definitions; it shares required p26. |
| Equations omitted in extraction | optional background | A textual comparison fully answers the question. An answer need not announce a pipeline limitation. |
| No invented weights; Figure 4 values optional | conditional on additional claim | Exact coefficients are not requested and depend on sample type. The corpus does not contain the figure pixels. |

Evidence judgments:

- `part-1`: p25 gives the product and replacement by addition; p25+p26 supplies both sides separately; p8 explicitly contrasts addition and multiplication. p26 alone supplies only the AW-SSIM side, so it is not an adequate contrast alternative. Verified locations: `pmc11121878:p25:w0[0:148]`, `pmc11121878:p25:w0[420:618]`, `pmc11121878:p26:w0[0:89]`, `pmc11121878:p8:w0[723:921]`.
- `part-2`: p26 explicitly says constant coefficients for each named component. The constants are not necessarily identical across sample types; p28 describes empirical selection. Verified locations: `pmc11121878:p26:w0[0:261]`.
- `component-calculations`: p26 explicitly states unchanged calculations and incurs no additional passage beyond the weighting requirement. Verified locations: `pmc11121878:p26:w0[778:892]`.

Unresolved judgments:

- Figure 4 numerical values were not visually reinspected in this audit and remain optional.

### tech-adga-shapes

Question: How does ADGA choose and blend irregular defect patches into target images?

Requested facts: How source appearances and irregular shapes are chosen. How patches are resized/placed and blended.

Sufficient scoped answer: Choose source images suited to the target background, cut irregular polygons with 3 to 7 vertices, resize and paste them randomly, and apply Gaussian blur to soften their edges.

Answerable in one indexed passage. The earlier question-review note that p18:w180 is needed for the edge explanation is stronger than the actual text supports; current evidence labels already correctly accept p18:w0 alone.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| Appearance selection, 3-to-7 vertices, random resize/paste, Gaussian edges | explicitly requested | These details explain choosing and blending the irregular patches. |
| Simulated defects for training | necessary for accuracy | ADGA generates training examples; do not describe acquired real damaged samples. |
| Not all arbitrary rectangular patches | conditional on additional claim | p18 contrasts previous rectangular-crop methods with the proposed irregular, appearance-aware method. |

Evidence judgments:

- `part-1`: p18 names the target color/appearance criterion. Verified locations: `pmc11121878:p18:w0[575:734]`.
- `part-2`: The 3-to-7 vertex range survives formula removal. Verified locations: `pmc11121878:p18:w0[735:878]`.
- `part-3`: Both selected spans are needed for random location and random dimensions but are in the same passage. Verified locations: `pmc11121878:p18:w0[412:574]`, `pmc11121878:p18:w0[879:939]`.
- `part-4`: p18:w0 contains both Gaussian blur and the complete edge-softening proposition before its cutoff. The tail adds a natural-blend description but no missing required fact. Verified locations: `pmc11121878:p18:w0[1065:1115]`, `pmc11121878:p18:w0[940:1064]`.

Unresolved judgments:

- Do not rewrite the preserved historical review archive; record the outdated note in a new review.

### tech-bright-specks-dark-background

Question: Why do tiny flaws look bright against a dark wafer image when the beam arrives from the side?

Requested facts: How oblique illumination and defect scattering produce bright flaws on a dark background.

Sufficient scoped answer: The smooth wafer reflects the oblique illumination away, while the optics collect light scattered by defects, producing bright spots against a dark background.

Answerable from p6. No missing table, figure or formula is necessary.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| Oblique light, clean-surface reflection, defect-scattered collection | explicitly requested | Together these explain the observed contrast. |
| No universal minimum defect size follows | conditional on additional claim | Necessary if discussing detectability limits, not mandatory content for a contrast explanation. |
| Do not say the image collects direct reflection everywhere | conditional on additional claim | That would reverse the dark-field mechanism. |

Evidence judgments:

- `part-1`: p6 supports oblique illumination. Verified locations: `pmc10934137:p6:w0[417:478]`.
- `part-2`: p6 states reflection from defect-free areas. Treat complete reflection as the paper's schematic description, not an independent universal optical claim. Verified locations: `pmc10934137:p6:w0[479:566]`.
- `part-3`: p6 explicitly links defect scatter collection to bright defects/dark background. p9 explains the beam trap and rejection of reflected light but does not alone state every labeled appearance claim, so no wholesale p9 alternative is proposed. Verified locations: `pmc10934137:p6:w0[567:715]`.

### tech-moving-signal-addition

Question: In the wafer study, how does following a moving spot across more sensor rows help a dim feature, and what ideal signal-to-noise improvement is expected when the number of rows is multiplied by m?

Requested facts: How charge accumulation follows the moving image across stages. The paper's ideal SNR multiplier for m times as many rows.

Sufficient scoped answer: Charge moves with the image and accumulates across stages, strengthening weak signals. The paper states an ideal square-root-of-m SNR gain.

Answerable from two indexed passages; ordinary symbol text survives extraction.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| Moving-charge accumulation and square-root-of-m gain | explicitly requested | Both mechanism and multiplier are directly requested. |
| Ideal, not an unconditional measured guarantee | necessary for accuracy | The question and source both say ideal. |
| Do not claim necessarily linear SNR scaling | conditional on additional claim | The paper's stated ideal multiplier is square-root-of-m; its general SNR equation also includes noise that may vary. |

Evidence judgments:

- `part-1`: p7 includes object/image movement and charge transfer. p8:w0 independently describes sequential stage accumulation. Verified locations: `pmc10934137:p7:w0[357:627]`, `pmc10934137:p8:w0[0:240]`.
- `part-2`: p8:w180 contains the only explicit ideal square-root statement found in canonical prose. It is not a corrupted formula placeholder. Equation 3 alone should not be used to infer a fixed-noise scaling guarantee. Verified locations: `pmc10934137:p8:w180[206:305]`.

### tech-too-many-shortcuts

Question: In the two-stage surface-reconstruction study, why did the network avoid shortcuts between every matching layer of its encoder and decoder?

Requested facts: Why all-layer shortcuts harmed the method's defect-detection purpose.

Sufficient scoped answer: Connecting all layers partly reconstructed defects. That weakens a method that localizes defects from the residual between input and reconstruction; the authors preferred two connections.

Answerable. Keep the causal-purpose requirement; do not count p16 alone as complete merely because it names unwanted reconstruction.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| All-layer shortcuts partly reconstruct defects | explicitly requested | This is the concrete reason for avoiding them. |
| Two strategic connections were best | optional background | Useful replacement configuration; the question asks why all-layer connections were avoided, not how many were retained. |
| Defect reconstruction is bad for residual localization | necessary for accuracy | The why question needs the detection consequence, otherwise better reconstruction sounds desirable. |
| More skips do not always improve detection | conditional on additional claim | The reported all-layer outcome contradicts such a universal claim. |

Evidence judgments:

- `part-1`: The two spans establish both observations in one p16 passage. Keeping the optional two-connection fact adds no passage requirement. Verified locations: `pmc11121878:p16:w0[1124:1274]`, `pmc11121878:p16:w0[1275:1366]`.
- `residual-purpose`: p6 supplies an explicit residual and discrimination explanation. p7 supplies a legitimate alternative requirement for clear residuals: non-reconstruction of defects. Its combination with retained p16 is required; p7 alone does not answer the architecture question. Verified locations: `pmc11121878:p6:w0[247:354]`, `pmc11121878:p6:w0[404:600]`.

Unresolved judgments:

- The alternative p7 expresses harm through a necessary condition for a clear residual, rather than the literal phrase diminishes ability. Human review should confirm acceptance of this direct inference; never drop the purpose group for convenience.

### tech-changing-neighborhood

Question: In the two-stage surface-reconstruction study, how did the researchers change which nearby pixels influence learning to balance noise suppression and preservation of small details?

Requested facts: Which Gaussian parameter changes nearby-pixel weights. How the schedule addresses noise versus fine detail. How incrementing/resetting and shuffling distribute those weightings through training.

Sufficient scoped answer: Vary Gaussian standard deviation, starting small and increasing it during patch processing, resetting it each epoch and shuffling samples. Small spread emphasizes nearby pixels and can amplify noise; large spread includes more distant pixels and can blur detail. The change concerns weighting spread.

Answerable with an internally loose terminology issue that prose plus original MathML resolve. Formula stripping increases required contextual passages. The existing three-passage support set is defensible; do not score-drop the footprint as a confirmed defect.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| Small/large spread tradeoff; increase, reset and shuffle | explicitly requested | These facts explain the changing neighborhood and how it is applied during learning. |
| Change standard deviation rather than grid dimensions | necessary for accuracy | p31 uses loose window-size language, so identify the actual changing parameter. |
| Exact fixed 11-by-11 dimensions | optional background | The numerical footprint is not requested; including it is scientifically useful but a short correct explanation can omit it. |
| Symbolic k has no supplied numeric value | conditional on additional claim | Required if specifying a numerical increment, not required in an explanation of gradual change. |
| No fixed neighborhood width throughout training | conditional on additional claim | Interpret width as Gaussian weighting spread. A fixed pixel-grid size is in fact reported; the guard should distinguish these meanings explicitly. |

Evidence judgments:

- `part-1`: p31 loses sigma to formula placeholders; p30 supplies the parameter identity. The joint requirement is justified. Verified locations: `pmc11121878:p30:w0[0:136]`, `pmc11121878:p31:w0[95:189]`.
- `part-2`: p31 describes the schedule; p32 describes k. Both approved alternatives include p30 to identify Gaussian standard deviation. Repeating p30 across groups costs no extra passage. Verified locations: `pmc11121878:p30:w0[0:136]`, `pmc11121878:p31:w0[292:427]`, `pmc11121878:p32:w0[0:374]`.
- `part-3`: p31 gives reset and shuffle; p30 again identifies the missing parameter. Verified locations: `pmc11121878:p30:w0[0:136]`, `pmc11121878:p31:w0[428:576]`.
- `gaussian-spread`: p30 explains central versus distant pixel weights. This is factual sufficiency, not a topic-only match. Verified locations: `pmc11121878:p30:w0[0:440]`.
- `fixed-footprint`: p29+p30 distinguishes the fixed 11x11 grid from changing spread. Exact dimension is optional for the visible question, but retaining this guard is defensible because the paper itself uses ambiguous window-size language. Verified locations: `pmc11121878:p29:w0[1035:1080]`, `pmc11121878:p30:w0[0:136]`.

Unresolved judgments:

- The future question-scoped contract must decide whether a correct explanation of standard deviation and weighting spread requires an explicit numerical footprint. This audit does not treat that policy choice as an annotation error.
- The forbidden-claim wording one fixed neighborhood width can be read as contradicting the correct fixed-grid claim; propose an explicit Gaussian-standard-deviation guard in review.

### tech-damaged-clean-pairs

Question: In the two-stage surface-reconstruction study, when the input has made-up damage, which picture is used as the target for the repaired output?

Requested facts: Which image is the reconstruction target when input contains synthetic damage.

Sufficient scoped answer: Use the corresponding original clean image as the target for the reconstructed output.

Answerable from p17:w0. Two groups divide a single target relationship but do not require extra passages.

| Existing requirement aspect | Classification | Reason |
| --- | --- | --- |
| Artificial inputs paired with clean counterparts; reconstructed output compared with normal reference | explicitly requested | Both phrasings describe the requested target relationship. |
| Synthetic damage belongs on the input, not target | necessary for accuracy | This preserves the direction of the requested mapping. |
| Do not train the output to reproduce synthetic damage | conditional on additional claim | That reverses the described target. |

Evidence judgments:

- `part-1`: p17 explicitly states artificial/clean pairing. Verified locations: `pmc11121878:p17:w0[664:824]`.
- `part-2`: All current alternatives identify clean reconstruction references. The p17 ending is a real word-window cutoff; enough of the counterpart statement survives for the target fact. The longer p17 alternative repeats support, not extra required material. p36 names original clean and reconstructed/artificial images, but the loss-argument symbols were removed. Verified locations: `pmc11121878:p17:w0[664:1140]`, `pmc11121878:p17:w0[878:1140]`, `pmc11121878:p36:w0[0:238]`.

Unresolved judgments:

- p36 may support the full clean-target relationship when read in the loss section; its stripped symbols weaken an exact pairing inference. Do not add p36 to part-1 merely because it contains the right topic. Keep this as a review question, not a confirmed score correction.

## Proposed revisions for review

These proposals are separate from the approved labels. Alternative corrections retain the requested facts. Scope proposals require an explicitly versioned contract and owner approval before they are used as the new evaluation standard. The parent audit can replay their effects through the existing evaluator using cached development rankings.

### wafer-question-scope

`tech-wafer-exact` / `efficiency-scope`. Category: question-scope. Action: remove_group. Confidence: high.

The visible question requests changes that improve SNR. Efficiency is an extra claim introduced by the required answer. In a separately approved question-scoped contract, make the no-efficiency-sacrifice clause and its transmission/fixed-frequency qualification conditional on making that extra claim. Preserve both in the original package metric.

Also split required_claims[0] into requested SNR changes and conditional efficiency. Removing only the group while continuing to require unqualified efficiency would be unsound.

### wafer-efficiency-self-contained

`tech-wafer-exact` / `efficiency-scope`. Category: alternatives. Action: add_alternative. Confidence: high.

This passage states both excluded transmission time and unchanged line frequency as stages increase. The requirement does not request the numerical 23,400 Hz setting, so p16 is corroboration rather than a necessary second passage.

`pmc10934137:p14:w180[82:334]`, `./body/sec[4]/sec[3]/p[2]`:

> Without considering the data transmission time, the imaging time is only related to line frequency. Therefore, the increase in the number of TDI stages does not affect the line frequency, thus improving the SNR without sacrificing detection efficiency.

### autoencoder-abstract-weight-transfer

`tech-autoencoder-exact` / `part-3`. Category: alternatives. Action: add_alternative. Confidence: high.

The complete weight-transfer clause is present before the 180-word boundary. It does not need the next passage to establish where the weights came from or their use in stage two. Keep the two-passage stage-two sample alternative unchanged.

`pmc11121878:p1:w0[1152:1254]`, `./front/article-meta/abstract[1]/p[1]`:

> In the second stage of training, the weights obtained from the first stage are used to train the model

### tdi-opposite-motion-example

`tech-tdi-motion-sync` / `part-2`. Category: alternatives. Action: add_alternative. Confidence: high.

The paper directly describes opposite object and integration directions. This alternative supports direction only; matching line frequency remains required by part-1.

`pmc10934137:p7:w0[246:356]`, `./body/sec[2]/sec[2]/p[1]`:

> In Figure 4a, the object moves to the left and the integral direction of the TDI image sensor is to the right.

### shortcut-residual-purpose

`tech-too-many-shortcuts` / `residual-purpose`. Category: alternatives. Action: add_alternative. Confidence: high.

This is the causal requirement for a useful residual, not a generic mention of autoencoders. Retained part-1 still requires p16 to establish that all-layer skip connections reconstruct defects in this architecture. Jointly p16 and p7 establish the same reason as p16 and the approved generic-method p6 explanation.

`pmc11121878:p7:w0[0:154]`, `./body/sec[1]/p[6]`:

> Therefore, achieving a clear and informative residual image requires a high-quality normal background reconstruction and non-reconstruction of the defect.

## Source limits and repeated observations

The wafer positives reuse a small collection of linked passages: the SNR changes, CFPN remedy and charge-accumulation mechanism are related observations from one apparatus. Autoencoder training, clean targets, skip-connection rationale and Gaussian weighting likewise reuse the same method. These are valid paper-reading needs, but they are not 11 independent experiments or evidence of broad deployment performance.

The wafer experiments concern particle surrogates on polished wafers, not malignant-cell sensitivity or specificity. Its tables cover sensor specifications, background noise and instrument/application parameters. The autoencoder experiments use six MVTec AD surface categories, with 1660 training and 714 test samples, not hospital CT patients. Its tables compare anomaly-detection methods and ablations by AuROC. Neither paper reports a shared four-paper CPU benchmark or randomized factory warranty trial. These observations assist the separate negative-case review without turning negatives into positive completeness successes.

No corpus rebuild is proposed for these 11 visible questions. Preserving mathematical symbol identities could reduce fragmented evidence needs in a future extraction revision, especially for the Gaussian schedule, but would require a separate corpus artifact, rebuilding all indexes, validating citations/IDs and remapping every affected exact span. Keep that migration separate from annotation corrections.

Generated-answer correctness remains unmeasured. Even a revised complete-evidence flag means that cached selected passages support an approved evidence contract, not that an answer provider produced the right answer.
