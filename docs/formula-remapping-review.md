# Formula span and reference remapping, approved and adopted

The project owner approved all proposed development span mappings and the 11
changed held-out references on 2026-10-14. Reason: source text change from formula
rendering. [Approval and adoption record](../evaluation/reviews/2026-10-14-pr15/approval.json).
The tables below preserve the reviewed old/new locations and quotes. Current labels
contain 167 fragments, including two required AND splits. Held-out is now version
`4-readable-formulas-frozen`, with 66 references and unchanged question/answer/claim
content. No held-out retrieval or answer inspection ran.

All offsets are half-open Unicode character offsets. Every occurrence was checked against the canonical quote. Only complete formula placeholders are replaced; all surrounding prose must match exactly. No fuzzy matching or semantic relabeling.

Classification counts: {'unchanged': 132, 'shifted only': 14, 'quote text changed': 19}.

The mapped labels are approved and adopted. Splitting one span across windows requires all fragments together in the same alternative. This preserves the approved text requirement but can change retrieval coverage because passage boundaries change.

## Held-out inventory

Held-out has references only. Every reference was checked offline by source paragraph alignment and candidate window coverage. ID changed takes precedence when the old window's content now requires different or multiple IDs. Text changed means the same ID covers the aligned range but its passage text differs. Questions, answers and claims did not guide rendering. No held-out retrieval ran.

Previous reference counts: seven text changes, 51 unchanged and four ID changes.
The previous frozen corpus pin differed from the candidate, while all original
source versions matched. The owner approved the new frozen version and canonical
pin `f293a02c7afaf38f06ec17d6443f7289fd3a7d3091cf11cf0d4f865ee0e3a675`.
The previous freeze and the original reviewed proposal remain in the approval archive.

| Held-out case / reference | Status | Old ID | Proposed IDs | Same source location |
| --- | --- | --- | --- | --- |
| hold-microscope-settings / 0 | text changed | pmc11510794:p26:w0 | pmc11510794:p26:w0 | True |
| hold-panel-dimensions / 0 | unchanged | pmc11510794:p28:w0 | pmc11510794:p28:w0 | True |
| hold-dataset-variants / 0 | unchanged | pmc11510794:p37:w0 | pmc11510794:p37:w0 | True |
| hold-resnet-head / 0 | unchanged | pmc11768589:p27:w0 | pmc11768589:p27:w0 | True |
| hold-mes-status-codes / 0 | unchanged | pmc11768589:p31:w0 | pmc11768589:p31:w0 | True |
| hold-mes-status-codes / 1 | unchanged | pmc11768589:p31:w180 | pmc11768589:p31:w180 | True |
| hold-tdi-sensor / 0 | unchanged | pmc10934137:p9:w0 | pmc10934137:p9:w0 | True |
| hold-psl-counting / 0 | unchanged | pmc10934137:p13:w0 | pmc10934137:p13:w0 | True |
| hold-ssim-window / 0 | ID changed | pmc11121878:p29:w0 | pmc11121878:p29:w0, pmc11121878:p29:w180 | True |
| hold-ssim-window / 1 | text changed | pmc11121878:p30:w0 | pmc11121878:p30:w0 | True |
| hold-lpips-backbone / 0 | unchanged | pmc11121878:p34:w0 | pmc11121878:p34:w0 | True |
| hold-mvtec-counts / 0 | unchanged | pmc11121878:p38:w0 | pmc11121878:p38:w0 | True |
| hold-raw-photo-counts / 0 | unchanged | pmc11510794:p30:w0 | pmc11510794:p30:w0 | True |
| hold-subtracted-channel / 0 | unchanged | pmc11510794:p54:w0 | pmc11510794:p54:w0 | True |
| hold-subtracted-channel / 1 | unchanged | pmc11510794:p50:w0 | pmc11510794:p50:w0 | True |
| hold-turning-heater / 0 | unchanged | pmc11768589:p36:w0 | pmc11768589:p36:w0 | True |
| hold-turning-heater / 1 | unchanged | pmc11768589:p19:w0 | pmc11768589:p19:w0 | True |
| hold-thinner-stripe-result / 0 | unchanged | pmc11768589:p38:w0 | pmc11768589:p38:w0 | True |
| hold-thinner-stripe-result / 1 | unchanged | pmc11768589:p47:w0 | pmc11768589:p47:w0 | True |
| hold-classification-versus-cycle / 0 | unchanged | pmc11768589:p41:w0 | pmc11768589:p41:w0 | True |
| hold-classification-versus-cycle / 1 | unchanged | pmc11768589:p29:w0 | pmc11768589:p29:w0 | True |
| hold-moving-chart-comparison / 0 | unchanged | pmc10934137:p12:w0 | pmc10934137:p12:w0 | True |
| hold-production-scan-projection / 0 | ID changed | pmc10934137:p16:w0 | pmc10934137:p16:w0, pmc10934137:p16:w180 | True |
| hold-production-scan-projection / 1 | unchanged | pmc10934137:p13:w0 | pmc10934137:p13:w0 | True |
| hold-production-scan-projection / 2 | unchanged | pmc10934137:p18:w0 | pmc10934137:p18:w0 | True |
| hold-material-dependent-loss / 0 | unchanged | pmc11121878:p28:w0 | pmc11121878:p28:w0 | True |
| hold-material-dependent-loss / 1 | text changed | pmc11121878:p27:w0 | pmc11121878:p27:w0 | True |
| hold-two-loss-priorities / 0 | text changed | pmc11121878:p35:w0 | pmc11121878:p35:w0 | True |
| hold-two-loss-priorities / 1 | text changed | pmc11121878:p10:w0 | pmc11121878:p10:w0 | True |
| hold-two-loss-priorities / 2 | unchanged | pmc11121878:p33:w0 | pmc11121878:p33:w0 | True |
| hold-compare-scratch-weakness / 0 | unchanged | pmc11510794:p49:w0 | pmc11510794:p49:w0 | True |
| hold-compare-scratch-weakness / 1 | unchanged | pmc11768589:p40:w0 | pmc11768589:p40:w0 | True |
| hold-compare-scratch-weakness / 2 | unchanged | pmc11510794:p53:w0 | pmc11510794:p53:w0 | True |
| hold-compare-scratch-weakness / 3 | unchanged | pmc11768589:p37:w0 | pmc11768589:p37:w0 | True |
| hold-compare-scratch-weakness / 4 | unchanged | pmc11768589:p37:w180 | pmc11768589:p37:w180 | True |
| hold-compare-size-evidence / 0 | unchanged | pmc11768589:p35:w0 | pmc11768589:p35:w0 | True |
| hold-compare-size-evidence / 1 | unchanged | pmc10934137:p13:w0 | pmc10934137:p13:w0 | True |
| hold-compare-size-evidence / 2 | ID changed | pmc10934137:p10:w0 | pmc10934137:p10:w0, pmc10934137:p10:w180 | True |
| hold-compare-deployment-readiness / 0 | unchanged | pmc11768589:p43:w0 | pmc11768589:p43:w0 | True |
| hold-compare-deployment-readiness / 1 | unchanged | pmc10934137:p17:w0 | pmc10934137:p17:w0 | True |
| hold-compare-defect-vocabularies / 0 | unchanged | pmc11510794:p30:w0 | pmc11510794:p30:w0 | True |
| hold-compare-defect-vocabularies / 1 | unchanged | pmc11768589:p20:w0 | pmc11768589:p20:w0 | True |
| hold-compare-performance-caveats / 0 | unchanged | pmc11510794:p52:w0 | pmc11510794:p52:w0 | True |
| hold-compare-performance-caveats / 1 | unchanged | pmc11121878:p39:w0 | pmc11121878:p39:w0 | True |
| hold-compare-performance-caveats / 2 | unchanged | pmc11510794:p50:w0 | pmc11510794:p50:w0 | True |
| hold-compare-performance-caveats / 3 | unchanged | pmc11510794:p60:w0 | pmc11510794:p60:w0 | True |
| hold-compare-intensity-assumptions / 0 | unchanged | pmc11510794:p39:w0 | pmc11510794:p39:w0 | True |
| hold-compare-intensity-assumptions / 1 | text changed | pmc10934137:p11:w0 | pmc10934137:p11:w0 | True |
| hold-compare-task-specific-limits / 0 | unchanged | pmc11510794:p56:w0 | pmc11510794:p56:w0 | True |
| hold-compare-task-specific-limits / 1 | unchanged | pmc10934137:p17:w0 | pmc10934137:p17:w0 | True |
| hold-compare-task-specific-limits / 2 | unchanged | pmc10934137:p17:w180 | pmc10934137:p17:w180 | True |
| hold-missing-embedding-ranking / 0 | unchanged | pmc11510794:p1:w0 | pmc11510794:p1:w0 | True |
| hold-missing-embedding-ranking / 1 | unchanged | pmc11768589:p1:w0 | pmc11768589:p1:w0 | True |
| hold-missing-embedding-ranking / 2 | unchanged | pmc10934137:p1:w0 | pmc10934137:p1:w0 | True |
| hold-missing-embedding-ranking / 3 | text changed | pmc11121878:p1:w0 | pmc11121878:p1:w0 | True |
| hold-missing-canopy-per-unit-euros / 0 | unchanged | pmc11510794:p25:w0 | pmc11510794:p25:w0 | True |
| hold-missing-canopy-per-unit-euros / 1 | unchanged | pmc11510794:p48:w0 | pmc11510794:p48:w0 | True |
| hold-missing-heater-six-month-drift / 0 | unchanged | pmc11768589:p43:w0 | pmc11768589:p43:w0 | True |
| hold-missing-wafer-damage-threshold / 0 | unchanged | pmc10934137:p9:w0 | pmc10934137:p9:w0 | True |
| hold-missing-wafer-damage-threshold / 1 | ID changed | pmc10934137:p16:w0 | pmc10934137:p16:w0, pmc10934137:p16:w180 | True |
| hold-missing-autoencoder-false-alarm-limit / 0 | unchanged | pmc11121878:p38:w0 | pmc11121878:p38:w0 | True |
| hold-missing-autoencoder-false-alarm-limit / 1 | unchanged | pmc11121878:p39:w0 | pmc11121878:p39:w0 | True |

## Changed or unmappable occurrences

| Case / group / alternative / span | Status and locations | Old quote | New quote |
| --- | --- | --- | --- |
| tech-wafer-exact / efficiency-scope / 0 / 0 | shifted only: pmc10934137:p14:w180[82:334] to pmc10934137:p14:w180[284:536].  | Without considering the data transmission time, the imaging time is only related to line frequency. Therefore, the increase in the number of TDI stages does not affect the line frequency, thus improving the SNR without sacrificing detection efficiency. | Without considering the data transmission time, the imaging time is only related to line frequency. Therefore, the increase in the number of TDI stages does not affect the line frequency, thus improving the SNR without sacrificing detection efficiency. |
| tech-autoencoder-exact / part-1 / 1 / 0 | quote text changed: pmc11121878:p17:w0[41:216] to pmc11121878:p17:w0[41:208].  | In the first stage, the training is performed only on non-defective training samples ( [formula omitted] ), focusing on learning the inherent characteristics of normal images. | In the first stage, the training is performed only on non-defective training samples ( (I)_(N D) ), focusing on learning the inherent characteristics of normal images. |
| tech-autoencoder-exact / part-1 / 3 / 0 | shifted only: pmc11121878:p1:w0[1008:1151] to pmc11121878:p1:w0[992:1135].  | In the first stage, the model trains only on normal samples using AW-SSIM loss, allowing it to learn robust representations of normal features. | In the first stage, the model trains only on normal samples using AW-SSIM loss, allowing it to learn robust representations of normal features. |
| tech-autoencoder-exact / part-2 / 1 / 0 | shifted only: pmc11121878:p46:w0[519:674] to pmc11121878:p46:w0[503:658].  | In the second stage of training, artificially defective samples and normal samples are used to train the model and enhance its ability to localize defects. | In the second stage of training, artificially defective samples and normal samples are used to train the model and enhance its ability to localize defects. |
| tech-autoencoder-exact / part-2 / 2 / 0 | shifted only: pmc11121878:p1:w0[1152:1296] to pmc11121878:p1:w0[1136:1280].  | In the second stage of training, the weights obtained from the first stage are used to train the model on both normal and artificially defective | In the second stage of training, the weights obtained from the first stage are used to train the model on both normal and artificially defective |
| tech-autoencoder-exact / part-2 / 2 / 1 | shifted only: pmc11121878:p1:w180[0:17] to pmc11121878:p1:w0[1281:1289]; pmc11121878:p1:w180[0:8]. Split into AND fragments | training samples. | training samples. |
| tech-autoencoder-exact / part-3 / 0 / 0 | shifted only: pmc11121878:p17:w0[534:663] to pmc11121878:p17:w0[526:655].  | Using the weights learned from the first stage of training, the second stage focuses on equipping the model for defect detection. | Using the weights learned from the first stage of training, the second stage focuses on equipping the model for defect detection. |
| tech-aw-ssim-combination / part-2 / 0 / 0 | quote text changed: pmc11121878:p26:w0[0:261] to pmc11121878:p26:w0[0:213].  | For AW-SSIM, we apply addition between the three sub-functions, as shown in Equation (6). In addition, we multiply each sub-function, luminance, contrast, and structure, by a constant [formula omitted] , [formula omitted] , and [formula omitted] , respectively. | For AW-SSIM, we apply addition between the three sub-functions, as shown in Equation (6). In addition, we multiply each sub-function, luminance, contrast, and structure, by a constant α , β , and γ , respectively. |
| tech-aw-ssim-combination / component-calculations / 0 / 0 | shifted only: pmc11121878:p26:w0[778:892] to pmc11121878:p26:w0[730:844].  | The calculations of the luminance, contrast, and structure values in AW-SSIM are the same as in the standard SSIM. | The calculations of the luminance, contrast, and structure values in AW-SSIM are the same as in the standard SSIM. |
| tech-adga-shapes / part-1 / 0 / 0 | quote text changed: pmc11121878:p18:w0[575:734] to pmc11121878:p18:w0[565:714].  | The source images ( [formula omitted] ) are carefully selected to represent realistic defects based on the background color and appearance of the target image. | The source images ( (I)_(s) ) are carefully selected to represent realistic defects based on the background color and appearance of the target image. |
| tech-adga-shapes / part-2 / 0 / 0 | quote text changed: pmc11121878:p18:w0[735:878] to pmc11121878:p18:w0[715:848].  | We randomly cut a portion of the source image ( [formula omitted] ) by selecting vertices ranging from 3 to 7, resulting in an irregular shape. | We randomly cut a portion of the source image ( (I)_(s) ) by selecting vertices ranging from 3 to 7, resulting in an irregular shape. |
| tech-adga-shapes / part-3 / 0 / 0 | shifted only: pmc11121878:p18:w0[412:574] to pmc11121878:p18:w0[402:564].  | Our approach involves cutting a portion from source images with varying shapes and sizes, and then pasting it randomly onto the target image as shown in Figure 2. | Our approach involves cutting a portion from source images with varying shapes and sizes, and then pasting it randomly onto the target image as shown in Figure 2. |
| tech-adga-shapes / part-3 / 0 / 1 | shifted only: pmc11121878:p18:w0[879:939] to pmc11121878:p18:w0[849:909].  | Then, the section is resized to a randomly chosen dimension. | Then, the section is resized to a randomly chosen dimension. |
| tech-adga-shapes / part-4 / 0 / 0 | quote text changed: pmc11121878:p18:w0[940:1064] to pmc11121878:p18:w0[910:1024].  | To smoothly integrate this irregularly shaped portion into the target image ( [formula omitted] ), we apply a Gaussian blur. | To smoothly integrate this irregularly shaped portion into the target image ( (I)_(T) ), we apply a Gaussian blur. |
| tech-adga-shapes / part-4 / 0 / 1 | shifted only: pmc11121878:p18:w0[1065:1115] to pmc11121878:p18:w0[1025:1075].  | This blurring softens the transition at the edges, | This blurring softens the transition at the edges, |
| tech-moving-signal-addition / part-2 / 0 / 0 | shifted only: pmc10934137:p8:w180[206:305] to pmc10934137:p8:w180[335:434].  | Ideally, increasing the number of TDI stages by a factor of m is expected to improve the SNR by √m. | Ideally, increasing the number of TDI stages by a factor of m is expected to improve the SNR by √m. |
| tech-changing-neighborhood / part-1 / 0 / 0 | quote text changed: pmc11121878:p30:w0[0:136] to pmc11121878:p30:w0[0:120].  | The standard deviation [formula omitted] of the Gaussian window determines how weights are assigned to pixels within the sliding window. | The standard deviation σ of the Gaussian window determines how weights are assigned to pixels within the sliding window. |
| tech-changing-neighborhood / part-1 / 0 / 1 | quote text changed: pmc11121878:p31:w0[95:189] to pmc11121878:p31:w0[79:141].  | A small [formula omitted] amplifies noise, while a large [formula omitted] blurs fine details. | A small σ amplifies noise, while a large σ blurs fine details. |
| tech-changing-neighborhood / part-2 / 0 / 0 | quote text changed: pmc11121878:p30:w0[0:136] to pmc11121878:p30:w0[0:120].  | The standard deviation [formula omitted] of the Gaussian window determines how weights are assigned to pixels within the sliding window. | The standard deviation σ of the Gaussian window determines how weights are assigned to pixels within the sliding window. |
| tech-changing-neighborhood / part-2 / 0 / 1 | quote text changed: pmc11121878:p31:w0[292:427] to pmc11121878:p31:w0[228:363].  | During training, it is gradually incremented by a small constant after processing every [formula omitted] patch of the training images. | During training, it is gradually incremented by a small constant after processing every (P)_(H) × (P)_(W) patch of the training images. |
| tech-changing-neighborhood / part-2 / 1 / 0 | quote text changed: pmc11121878:p30:w0[0:136] to pmc11121878:p30:w0[0:120].  | The standard deviation [formula omitted] of the Gaussian window determines how weights are assigned to pixels within the sliding window. | The standard deviation σ of the Gaussian window determines how weights are assigned to pixels within the sliding window. |
| tech-changing-neighborhood / part-2 / 1 / 1 | quote text changed: pmc11121878:p32:w0[0:374] to pmc11121878:p32:w0[0:342].  | Here, [formula omitted] is the standard deviation after each epoch, which depends on the number of training samples and the sizes of the patches ( [formula omitted] ) in patch-based training. H and W are the height and width of the input image, respectively, and k is a small constant added to [formula omitted] after each patch of size [formula omitted] in the input image. | Here, σ is the standard deviation after each epoch, which depends on the number of training samples and the sizes of the patches ( (P)_(H) × (P)_(W) ) in patch-based training. H and W are the height and width of the input image, respectively, and k is a small constant added to σ after each patch of size (P)_(H) × (P)_(W) in the input image. |
| tech-changing-neighborhood / part-3 / 0 / 0 | quote text changed: pmc11121878:p30:w0[0:136] to pmc11121878:p30:w0[0:120].  | The standard deviation [formula omitted] of the Gaussian window determines how weights are assigned to pixels within the sliding window. | The standard deviation σ of the Gaussian window determines how weights are assigned to pixels within the sliding window. |
| tech-changing-neighborhood / part-3 / 0 / 1 | quote text changed: pmc11121878:p31:w0[428:576] to pmc11121878:p31:w0[364:496].  | Importantly, the training samples are shuffled after each epoch, and [formula omitted] is reset to its initial value before being incremented again. | Importantly, the training samples are shuffled after each epoch, and σ is reset to its initial value before being incremented again. |
| tech-changing-neighborhood / gaussian-spread / 0 / 0 | quote text changed: pmc11121878:p30:w0[0:440] to pmc11121878:p30:w0[0:392].  | The standard deviation [formula omitted] of the Gaussian window determines how weights are assigned to pixels within the sliding window. A smaller [formula omitted] creates a narrower window, concentrating weight near the center and reducing the influence of distant pixels, as shown in Figure 5. Conversely, a larger [formula omitted] results in a wider window, spreading weights more evenly and increasing the influence of distant pixels. | The standard deviation σ of the Gaussian window determines how weights are assigned to pixels within the sliding window. A smaller σ creates a narrower window, concentrating weight near the center and reducing the influence of distant pixels, as shown in Figure 5. Conversely, a larger σ results in a wider window, spreading weights more evenly and increasing the influence of distant pixels. |
| tech-changing-neighborhood / fixed-footprint / 0 / 0 | shifted only: pmc11121878:p29:w0[1035:1080] to pmc11121878:p29:w0[1043:1082]; pmc11121878:p29:w180[0:5]. Split into AND fragments | We used a window size of 11 × 11 in our work. | We used a window size of 11 × 11 in our work. |
| tech-changing-neighborhood / fixed-footprint / 0 / 1 | quote text changed: pmc11121878:p30:w0[0:136] to pmc11121878:p30:w0[0:120].  | The standard deviation [formula omitted] of the Gaussian window determines how weights are assigned to pixels within the sliding window. | The standard deviation σ of the Gaussian window determines how weights are assigned to pixels within the sliding window. |
| tech-damaged-clean-pairs / part-1 / 0 / 0 | quote text changed: pmc11121878:p17:w0[664:824] to pmc11121878:p17:w0[656:800].  | Here, images with artificially introduced defects ( [formula omitted] ) created by the ADGA are paired with their non-defect counterparts ( [formula omitted] ). | Here, images with artificially introduced defects ( (I)_(A D) ) created by the ADGA are paired with their non-defect counterparts ( (I)_(N D) ). |
| tech-damaged-clean-pairs / part-2 / 0 / 0 | quote text changed: pmc11121878:p17:w0[878:1140] to pmc11121878:p17:w0[854:1100].  | The normal samples ( [formula omitted] ) are used as references to improve the reconstruction performance of the model by comparing a normal sample with the reconstructed image ( [formula omitted] ) from its artificially defective counterpart ( [formula omitted] | The normal samples ( (I)_(N D) ) are used as references to improve the reconstruction performance of the model by comparing a normal sample with the reconstructed image ( [formula omitted] ) from its artificially defective counterpart ( (I)_(A D) |
| tech-damaged-clean-pairs / part-2 / 1 / 0 | quote text changed: pmc11121878:p36:w0[0:238] to pmc11121878:p36:w0[0:222].  | Here, [formula omitted] is the combined structural and perceptual loss, [formula omitted] is the original image without defects, and [formula omitted] is the reconstructed image from the artificially defective image ( [formula omitted] ). | Here, [formula omitted] is the combined structural and perceptual loss, (I)_(N D) is the original image without defects, and [formula omitted] is the reconstructed image from the artificially defective image ( (I)_(A D) ). |
| tech-damaged-clean-pairs / part-2 / 2 / 0 | quote text changed: pmc11121878:p17:w0[664:1140] to pmc11121878:p17:w0[656:1100].  | Here, images with artificially introduced defects ( [formula omitted] ) created by the ADGA are paired with their non-defect counterparts ( [formula omitted] ). During training, these pairs are fed into the model. The normal samples ( [formula omitted] ) are used as references to improve the reconstruction performance of the model by comparing a normal sample with the reconstructed image ( [formula omitted] ) from its artificially defective counterpart ( [formula omitted] | Here, images with artificially introduced defects ( (I)_(A D) ) created by the ADGA are paired with their non-defect counterparts ( (I)_(N D) ). During training, these pairs are fed into the model. The normal samples ( (I)_(N D) ) are used as references to improve the reconstruction performance of the model by comparing a normal sample with the reconstructed image ( [formula omitted] ) from its artificially defective counterpart ( (I)_(A D) |
| tech-compare-evaluation-metrics / part-1 / 0 / 0 | shifted only: pmc11510794:p47:w0[669:895] to pmc11510794:p47:w0[659:885].  | In this study, we use both the conventional mAP50, which evaluates at an intersection over union (IoU) threshold of 0.5, and the stricter mAP50-95, which averages over multiple IoU thresholds from 0.5 to 0.95 in steps of 0.05. | In this study, we use both the conventional mAP50, which evaluates at an intersection over union (IoU) threshold of 0.5, and the stricter mAP50-95, which averages over multiple IoU thresholds from 0.5 to 0.95 in steps of 0.05. |
| tech-compare-network-inputs / part-1 / 0 / 0 | shifted only: pmc11121878:p17:w0[217:333] to pmc11121878:p17:w0[209:325].  | First, the input image is divided into 128 × 128 patches, and the latent representation is extracted by the encoder. | First, the input image is divided into 128 × 128 patches, and the latent representation is extracted by the encoder. |
