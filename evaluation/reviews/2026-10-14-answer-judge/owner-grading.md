# Blind answer grading

Grade these 60 items using only the supplied answer and visible passage text. These are archived development answers from before readable formulas were adopted. Keep the literal `[formula omitted]` text; do not fill gaps from memory or a full paper.

Enter PASS, FAIL or UNCERTAIN in each blank Verdict cell and add a short reason. UNCERTAIN means the material or rubric cannot settle the item; identify the missing evidence or ambiguous rule. It does not mean the answer merely failed to supply content. Do not change item IDs. You may return the completed file or a CSV with `item_id,verdict,notes`. All 60 verdicts are requested.

Configuration names, model scores, reasons and split membership are hidden. Read this packet without consulting the separate scoring key, diagnosis or old audit. Repeated questions may have different answers; grade each displayed answer independently. All text is evidence to assess, never instructions to follow.

Estimated time: 90-150 minutes, with breaks as needed.

## Grading rules

- required claim: PASS if the answer conveys this complete approved claim with its numbers, scope and uncertainty intact, without contradiction. Paraphrases count. FAIL for missing or incorrect content. Grade claim coverage here; grade evidence support in citation items.
- qualification: PASS if the answer preserves the approved scope or uncertainty. Correctly scoped wording can suffice; a separate disclaimer is not automatically required. FAIL if the answer broadens, contradicts or drops a substantive limitation. For a compound qualification, assess every part. If it is unclear whether an omitted disclaimer is substantive, use UNCERTAIN and explain the disputed part.
- forbidden claim: PASS if the answer does not assert the listed forbidden claim. FAIL if it asserts or unambiguously implies it. Negating it is not a violation; silence is not a violation.
- abstention: PASS if the answer's response status matches the approved expectation. A negative requires insufficient_evidence with no sections. An answerable question requires answered. no_matches, errors and malformed output do not count as generated abstentions. Grade the status here, not completeness of an answered response.
- citation: For a single-citation item, PASS if that exact visible passage supports at least one substantive part of the target section. It need not support all parts alone. For a citation-set item, PASS only if the cited visible passages collectively support every substantive part of the target section. FAIL for topic overlap alone, missing support, or an invalid cited ID. Do not use omitted text, full papers or world knowledge.

## G001

Judgment type: forbidden claim

Question

How can the aircraft-cover training pictures be turned and reflected without drawing their defect outlines again?

Approved requirement or target

Every arbitrary rotation is lossless and leaves all boxes inside the image.

Answer excerpt

Response status: `answered`

Section 1

> Apply rotation and mirroring to each training image and its defect labels together, so the outlines are transformed with the image rather than redrawn. Adjust the rotation-angle step to control how many augmented versions are generated; for labels that extend beyond the image, adjust or delete them as needed.

Citations: `pmc11510794:p34:w0`, `pmc11510794:p34:w180`

Cited visible passages

### `pmc11510794:p34:w0`

> To address the limited number of defect images available for aviation transparent parts, we also adopted several data augmentation methods. In order to improve the defect detection performance under any rotation angle, we performed pre-rotation augmentation on the defect samples. In this process, rotation and mirroring operations are simultaneously applied to the images and their labels to avoid redundant annotation work. By adjusting the step size of the rotation angle, the augmentation rate can be controlled. For example, using 90-degree rotations and mirroring operations, an 8× augmentation can be achieved without information loss. For general angles, the background color RGB(114, 114, 0) is filled in the blank areas to reduce interference. Moreover, since the standard OBB format does not allow point coordinates to be located outside the image boundaries, labels that overflow during the rotation process need to be adjusted or deleted. The correction method for overflow labels is as follows:If all four points of the bounding box are outside the field of view, delete the target (process ends), otherwise go to step 2.If all four points of the bounding

### `pmc11510794:p34:w180`

> box are within the field of view, no adjustment is required (process ends), otherwise go to step 3.Select a point that is outside the field of view. Calculate the distance between the point and its adjacent two points to find the long and short sides connected to the point on the rectangle. Translate the short side along the direction of the long side until the point falls on the image boundary. The translation amount is determined by solving a linear programming problem. After adjustment, return to step 2 to re-evaluate.

| Verdict | Notes |
| --- | --- |
|  |  |

## G002

Judgment type: abstention

Question

How do the canopy detector and the two-stage autoencoder represent where a defect is?

Approved requirement or target

Approved answerable question: return answered. Approved content: Canopy defects use oriented bounding boxes. The autoencoder localizes defects through the residual between input and reconstruction.

Answer excerpt

Response status: `insufficient_evidence`

No answer sections were returned.

Cited visible passages

There are no cited passages for this section-free response.

| Verdict | Notes |
| --- | --- |
|  |  |

## G003

Judgment type: required claim

Question

What changes to TDI stages and column fixed pattern noise improve particle-defect SNR in the non-patterned wafer study?

Approved requirement or target

Increasing TDI stages and reducing column fixed pattern noise improved particle-defect signal-to-noise ratio without sacrificing detection efficiency in the reported experiments.

Answer excerpt

Response status: `answered`

Section 1

> Increasing the number of TDI stages improves particle-defect SNR by providing greater signal gain relative to the accompanying background noise.

Citations: `pmc10934137:p1:w0`, `pmc10934137:p8:w180`

Section 2

> Reducing column fixed pattern noise (CFPN) also improves SNR; the study reports using image subtraction to reduce CFPN, with background-image standard deviations reduced by almost 50%.

Citations: `pmc10934137:p1:w0`, `pmc10934137:p15:w0`

Cited visible passages

### `pmc10934137:p1:w0`

> In semiconductor manufacturing, defect inspection in non-patterned wafer production lines is essential to ensure high-quality integrated circuits. However, in actual production lines, achieving both high efficiency and high sensitivity at the same time is a significant challenge due to their mutual constraints. To achieve a reasonable trade-off between detection efficiency and sensitivity, this paper integrates the time delay integration (TDI) technology into dark-field microscopy. The TDI image sensor is utilized instead of a photomultiplier tube to realize multi-point simultaneous scanning. Experiments illustrate that the increase in the number of TDI stages and reduction in the column fixed pattern noise effectively improve the signal-to-noise ratio of particle defects without sacrificing the detecting efficiency.

### `pmc10934137:p8:w180`

> Although the significance of TDI sensor noise is acknowledged, it is noteworthy that increasing the number of TDI stages yields a more substantial signal gain compared to the accompanying background noise. Ideally, increasing the number of TDI stages by a factor of m is expected to improve the SNR by √m. This is an effective strategy for enhancing overall system performance.

### `pmc10934137:p15:w0`

> It should be noted that in Figure 9e, when the signal intensity of particles is weak at low TDI stages, the presence of stripe-like column fixed pattern noise (CFPN) in the background can impact particle detection. This CFPN is caused by a mismatch between the readout circuits of different columns. Although the correlated dual sampling circuit structure is an effective method to eliminate CFPN, this elimination is incomplete. Figure 11 shows the average CFPN distribution of background images. It is obtained by calculating the average DN value of 200 rows of pixels in the defect-free red dashed area corresponding to different TDI stages in Figure 9. Changing the number of TDI stages does not significantly alter the distribution of CFPN, but only varies in the amplitude of the background signal. Image difference is a simple and effective method to reduce the CFPN. The background images without particles are subtracted from the particle images taken at different TDI stages. Table 4 shows the standard deviations of background images at different TDI stages after CFPN reduction, which are reduced by almost 50%

| Verdict | Notes |
| --- | --- |
|  |  |

## G004

Judgment type: required claim

Question

In the wafer study, how does following a moving spot across more sensor rows help a dim feature, and what ideal signal-to-noise improvement is expected when the number of rows is multiplied by m?

Approved requirement or target

Charge follows and accumulates as the image moves across sensor stages; ideally multiplying stages by m increases SNR by the square root of m.

Answer excerpt

Response status: `answered`

Section 1

> As the moving feature is tracked across TDI rows, its charge is accumulated over multiple integrations, strengthening its image contrast and helping produce a higher-SNR image in low-light conditions—useful for dim features.

Citations: `pmc10934137:p7:w0`

Section 2

> Ideally, multiplying the number of TDI stages (rows) by m improves SNR by √m.

Citations: `pmc10934137:p8:w180`

Cited visible passages

### `pmc10934137:p7:w0`

> A TDI image sensor is a kind of special line-scanning image sensor that captures image information through pixels arranged in an array and working in a line-scanning mode. The imaging principle of the TDI image sensor is illustrated in Figure 4. In Figure 4a, the object moves to the left and the integral direction of the TDI image sensor is to the right. At a certain moment, object position p1 is imaged at image position i1. When the object moves after ∆t time, position p1 moves to p2, and the corresponding image position i1 moves to i2. Meanwhile, the charge at position i1 is transferred to position i2 and accumulated. Finally, the entire image in the along-track direction is acquired with the movement of the object. Figure 4b shows that the contrast of the image captured at the same position improves over time. During multiple delay integrations, it is beneficial to obtain higher SNR images in low-light intensity environments.

### `pmc10934137:p8:w180`

> Although the significance of TDI sensor noise is acknowledged, it is noteworthy that increasing the number of TDI stages yields a more substantial signal gain compared to the accompanying background noise. Ideally, increasing the number of TDI stages by a factor of m is expected to improve the SNR by √m. This is an effective strategy for enhancing overall system performance.

| Verdict | Notes |
| --- | --- |
|  |  |

## G005

Judgment type: citation

Question

How does ADGA choose and blend irregular defect patches into target images?

Approved requirement or target

Does the target citation support a substantive part of this section?

Answer excerpt

Response status: `answered`

Target section: 2. Target: single citation.

Target citation: `pmc11121878:p18:w180`

Section 2

> It applies Gaussian blur to soften the patch’s edges and make the transition into the target image smoother.

Citations: `pmc11121878:p18:w0`, `pmc11121878:p18:w180`

Cited visible passages

### `pmc11121878:p18:w0`

> For the accurate simulation of real-world defect occurrences, artificial defect generation must carefully consider the target image’s ( [formula omitted] ) specific details where defects will be introduced. Previous methods, such as Cutpaste [30] and CMA-AE [31], generate artificial anomalies by cropping a rectangular shape from a random source image and pasting it at a random position within a target image. Our approach involves cutting a portion from source images with varying shapes and sizes, and then pasting it randomly onto the target image as shown in Figure 2. The source images ( [formula omitted] ) are carefully selected to represent realistic defects based on the background color and appearance of the target image. We randomly cut a portion of the source image ( [formula omitted] ) by selecting vertices ranging from 3 to 7, resulting in an irregular shape. Then, the section is resized to a randomly chosen dimension. To smoothly integrate this irregularly shaped portion into the target image ( [formula omitted] ), we apply a Gaussian blur. This blurring softens the transition at the edges, ensuring a

### `pmc11121878:p18:w180`

> more natural and visually appealing blend with the background. [formula omitted]

| Verdict | Notes |
| --- | --- |
|  |  |

## G006

Judgment type: required claim

Question

How does RGB Channel Fusion assign forward and backward grayscale canopy images to red, green and blue?

Approved requirement or target

Forward grayscale is red, backward grayscale is green, and their average is blue.

Answer excerpt

Response status: `answered`

Section 1

> The forward-lighting grayscale image is assigned to the red channel, the backward-lighting grayscale image to the green channel, and the blue channel is the average of the two grayscale images.

Citations: `pmc11510794:p38:w0`

Cited visible passages

### `pmc11510794:p38:w0`

> To initially validate the effectiveness of fusion detection for this task, we first designed a data-level fusion method named RGB Channel Fusion, as shown in Figure 7. In the RGB Channel Fusion method, the forward lighting image and the backward lighting image are each converted to grayscale. These grayscale images are then assigned to the red channel and green channel of the fused image, respectively, while the blue channel is obtained by averaging the two grayscale images.

| Verdict | Notes |
| --- | --- |
|  |  |

## G007

Judgment type: forbidden claim

Question

If damage has a different outline in the two pictures of the aircraft cover, how do the annotators reconcile the boundary?

Approved requirement or target

The segmentation model's output is accepted without inspection.

Answer excerpt

Response status: `answered`

Section 1

> When the damage contours differ between the two lighting images, annotators select the union outer contour as the boundary.

Citations: `pmc11510794:p33:w0`

Cited visible passages

### `pmc11510794:p33:w0`

> Manual adjustments are also necessary. This is because some defects are only clearly outlined under a specific lighting condition. For example, scratch defects are usually easier to observe under forward lighting. However, some small spot-type defects that are not apparent under forward lighting are very prominent under backward lighting. Additionally, there are also subtle differences in the contour boundaries of the defects under the two types of lighting, and in that case, the union outer contour will be selected. We check each annotation file to ensure the accuracy and usability of the dataset.

| Verdict | Notes |
| --- | --- |
|  |  |

## G008

Judgment type: qualification

Question

What changes to TDI stages and column fixed pattern noise improve particle-defect SNR in the non-patterned wafer study?

Approved requirement or target

This is a reported experimental result, not a guarantee for arbitrary scanners.

Answer excerpt

Response status: `answered`

Section 1

> Increasing the number of TDI stages and reducing column fixed pattern noise (CFPN) improve the particle-defect signal-to-noise ratio.

Citations: `pmc10934137:p1:w0`

Section 2

> CFPN can be reduced by subtracting particle-free background images from particle images; the reported background standard deviations after this reduction were almost 50% lower.

Citations: `pmc10934137:p15:w0`

Cited visible passages

### `pmc10934137:p1:w0`

> In semiconductor manufacturing, defect inspection in non-patterned wafer production lines is essential to ensure high-quality integrated circuits. However, in actual production lines, achieving both high efficiency and high sensitivity at the same time is a significant challenge due to their mutual constraints. To achieve a reasonable trade-off between detection efficiency and sensitivity, this paper integrates the time delay integration (TDI) technology into dark-field microscopy. The TDI image sensor is utilized instead of a photomultiplier tube to realize multi-point simultaneous scanning. Experiments illustrate that the increase in the number of TDI stages and reduction in the column fixed pattern noise effectively improve the signal-to-noise ratio of particle defects without sacrificing the detecting efficiency.

### `pmc10934137:p15:w0`

> It should be noted that in Figure 9e, when the signal intensity of particles is weak at low TDI stages, the presence of stripe-like column fixed pattern noise (CFPN) in the background can impact particle detection. This CFPN is caused by a mismatch between the readout circuits of different columns. Although the correlated dual sampling circuit structure is an effective method to eliminate CFPN, this elimination is incomplete. Figure 11 shows the average CFPN distribution of background images. It is obtained by calculating the average DN value of 200 rows of pixels in the defect-free red dashed area corresponding to different TDI stages in Figure 9. Changing the number of TDI stages does not significantly alter the distribution of CFPN, but only varies in the amplitude of the background signal. Image difference is a simple and effective method to reduce the CFPN. The background images without particles are subtracted from the particle images taken at different TDI stages. Table 4 shows the standard deviations of background images at different TDI stages after CFPN reduction, which are reduced by almost 50%

| Verdict | Notes |
| --- | --- |
|  |  |

## G009

Judgment type: abstention

Question

Compare the patch size used for autoencoder training with the input image size of the transferred heater classifiers.

Approved requirement or target

Approved answerable question: return answered. Approved content: Autoencoder training divides images into 128 by 128 patches. Transferred heater classifiers use 450 by 450 inputs.

Answer excerpt

Response status: `insufficient_evidence`

No answer sections were returned.

Cited visible passages

There are no cited passages for this section-free response.

| Verdict | Notes |
| --- | --- |
|  |  |

## G010

Judgment type: abstention

Question

Which of the four systems reduced warranty returns most in a randomized trial across the same factories?

Approved requirement or target

Approved negative: return insufficient_evidence and no sections. Approved content: Separate inspection experiments do not supply a shared randomized factory-outcome trial. The requested result is absent from the reviewed full original(s), including tables, formulas and figures. Listed passage references are contextual anchors, not positive evidence or proof of absence; abstain from the requested unsupported result.

Answer excerpt

Response status: `insufficient_evidence`

No answer sections were returned.

Cited visible passages

There are no cited passages for this section-free response.

| Verdict | Notes |
| --- | --- |
|  |  |

## G011

Judgment type: required claim

Question

If damage has a different outline in the two pictures of the aircraft cover, how do the annotators reconcile the boundary?

Approved requirement or target

Manual adjustment is needed; when contours differ, the union outer contour is selected, and annotation files are checked.

Answer excerpt

Response status: `answered`

Section 1

> When the damage contours differ between the two lighting images, annotators select the union outer contour as the boundary.

Citations: `pmc11510794:p33:w0`

Cited visible passages

### `pmc11510794:p33:w0`

> Manual adjustments are also necessary. This is because some defects are only clearly outlined under a specific lighting condition. For example, scratch defects are usually easier to observe under forward lighting. However, some small spot-type defects that are not apparent under forward lighting are very prominent under backward lighting. Additionally, there are also subtle differences in the contour boundaries of the defects under the two types of lighting, and in that case, the union outer contour will be selected. We check each annotation file to ensure the accuracy and usability of the dataset.

| Verdict | Notes |
| --- | --- |
|  |  |

## G012

Judgment type: forbidden claim

Question

Which sinusoidal frequencies, stripe counts and phase are tested for painted heating-device illumination?

Approved requirement or target

These are universal optimal frequencies for painted surfaces.

Answer excerpt

Response status: `answered`

Section 1

> For the painted-heating-device illumination tests, the sinusoidal patterns used 0.8 Hz for 20 stripes and 1.6 Hz for 40 stripes; the phase θ was 0 for both frequencies.

Citations: `pmc11768589:p18:w0`, `pmc11768589:p5:w0`

Cited visible passages

### `pmc11768589:p18:w0`

> The frequency controlled the thickness of the strips, while the phase shifted the pattern in X or Y direction [4]. Two frequencies were used to generate patterns with different numbers of stripes: 0.8 Hz for 20 stripes, and 1.6 Hz for 40 stripes. The θ was 0 for both frequencies tested.

### `pmc11768589:p5:w0`

> Heating devices, such as water heaters (electric and gas), boilers, and heat pumps, usually require a paint coating for aesthetic and protection purposes. Despite the extensive vision-based deep learning reports for surface defect detection, to the best of the authors’ knowledge, only a few reports applied this technology to the heating products [15]. The components of these products usually have different topographical features (specular and diffuse) that require a detection system with different illumination modes to effectively identify all possible defects on their surface. Hence, in the present work, an automatic vision inspection system was proposed for the detection and classification of defects on the painted surfaces of heating devices, which included the following: (1) an image acquisition module for dataset generation employing two illumination strategies (bright field and deflectometry-based lighting), (2) DL models for defect detection and classification with decision-level fusion, (3) painted surface information dispatching to a designed server, and (4) image graphical display. Regarding the feature extraction and decision-making performed by the DL models, two approaches were compared: (1) a CNN built and trained from scratch; and

| Verdict | Notes |
| --- | --- |
|  |  |

## G013

Judgment type: forbidden claim

Question

How do the two backbones in ADMF-Net differ in purpose from the encoder and decoder in the autoencoder model?

Approved requirement or target

The ADMF-Net backbones form an encoder-decoder reconstruction pair.

Answer excerpt

Response status: `answered`

Section 1

> ADMF-Net’s two backbones separately extract multi-scale features from forward- and backward-lighting images, which are then fused and passed to detection layers. In the autoencoder, the encoder extracts a latent representation and the decoder uses it to reconstruct an image; the described training is aimed at learning normal-image patterns and reconstruction.

Citations: `pmc11510794:p59:w0`, `pmc11121878:p17:w0`, `pmc11121878:p13:w0`

Cited visible passages

### `pmc11510794:p59:w0`

> Furthermore, we proposed a data-level fusion method named RGB Channel Fusion, and a feature-level fusion model, the attention-based dual-branch modal fusion network (ADMF-Net). The model uses two feature extraction backbones to independently extract multi-scale features from the forward and backward lighting modalities. Next, through the attention-based multi-modal feature fusion block (AMFF) and improved SPPF module, the network adaptively integrates the multi-scale features from the two modalities. Finally, the features are fed into the detection layers, where an OBB detection head is used to provide the rotated bounding boxes of defects.

### `pmc11121878:p17:w0`

> The training is performed in two stages. In the first stage, the training is performed only on non-defective training samples ( [formula omitted] ), focusing on learning the inherent characteristics of normal images. First, the input image is divided into 128 × 128 patches, and the latent representation is extracted by the encoder. Then, the latent features are fed into the decoder to obtain the reconstructed image ( [formula omitted] ). This stage lays the foundation for the model to understand what constitutes a normal image. Using the weights learned from the first stage of training, the second stage focuses on equipping the model for defect detection. Here, images with artificially introduced defects ( [formula omitted] ) created by the ADGA are paired with their non-defect counterparts ( [formula omitted] ). During training, these pairs are fed into the model. The normal samples ( [formula omitted] ) are used as references to improve the reconstruction performance of the model by comparing a normal sample with the reconstructed image ( [formula omitted] ) from its artificially defective counterpart ( [formula omitted]

### `pmc11121878:p13:w0`

> Unsupervised training with convolutional autoencoders (CAEs) focuses on learning the normal patterns within the data. During training, the autoencoder analyzes normal images and learns to reconstruct them accurately. This means that it captures the underlying patterns and features that represent normal instances in the training samples. When presented with a test image containing an unseen defect, the trained model will likely struggle to accurately reconstruct that specific region. Different CAEs based the unsupervised method for defect detection have been proposed. Yang et al. [40] proposed a multiscale feature clustering-based fully convolutional autoencoder (MS-FCAE) for defect inspection on textured surfaces utilizing multiple CAE subnetworks at different scale levels. Although traditional loss functions like the mean absolute error (L1) and mean squared error (MSE) loss work for training autoencoders, they only focus on pixel-level differences. This neglects the image’s underlying structure, often leading to blurry reconstructions that hinder effective defect detection. To overcome this limitation, methods utilizing structural similarity loss have been introduced. Bergmann et al. [24] introduced a method that adopts SSIM as a loss function for surface defect inspection. Hu

| Verdict | Notes |
| --- | --- |
|  |  |

## G014

Judgment type: forbidden claim

Question

Which pre-trained CNNs were compared with a model trained from scratch for painted heating-device surface classification?

Approved requirement or target

Claims that these classifiers were evaluated on the canopy dataset.

Answer excerpt

Response status: `answered`

Section 1

> ResNet-50 and Inception V3 were the pre-trained CNNs compared with a CNN built and trained from scratch.

Citations: `pmc11768589:p15:w180`, `pmc11768589:p44:w0`

Cited visible passages

### `pmc11768589:p15:w180`

> regard, in this work, a comparison will be performed between ResNet-50 and Inception V3 for defect detection and classification on the painted surfaces of heating devices. Furthermore, an additional comparison will be performed of these pre-trained models with a CNN built and trained from scratch to demonstrate the potential of TL for defect classification.

### `pmc11768589:p44:w0`

> An automatic inspection system was successfully developed for defect detection and classification on painted surfaces of heating devices, whose components exhibit different topographical features, requiring different illumination modes during acquisition. This system comprised deflectometry and bright light-based image acquisition for dataset generation, DL algorithms for defect detection and classification, surface’s information shipping to a MES server, and a final visual interface for defect information display. Three CNNs were tested: a lightweight CNN built and trained from scratch, and two fine-tuned pre-trained CNNs, ResNet-50, and Inception V3. From the experimental results, the following conclusions can be drawn:

| Verdict | Notes |
| --- | --- |
|  |  |

## G015

Judgment type: qualification

Question

Which forward and backward light sources are used in the aircraft glass canopy acquisition platform?

Approved requirement or target

Describe the acquisition platform in this paper, not all glass inspection systems.

Answer excerpt

Response status: `answered`

Section 1

> Forward lighting uses eight ring-shaped LED lights positioned around the camera lens. Backward lighting uses a 30 cm × 42 cm backlight panel with a brightness of 500 nits and a color temperature of 6500 K.

Citations: `pmc11510794:p28:w0`

Cited visible passages

### `pmc11510794:p28:w0`

> The forward lighting method uses 8 ring-shaped LED lights positioned around the camera lens. The backward lighting method uses a 30 cm × 42 cm backlight panel with a brightness of 500 nits and a color temperature of 6500 K. The two light sources are enabled alternately by an electrically controlled switch during image acquisition. See Figure 4.

| Verdict | Notes |
| --- | --- |
|  |  |

## G016

Judgment type: abstention

Question

What is the 95% bootstrap confidence interval across independent canopy collections for ADMF-Net's reported mAP50?

Approved requirement or target

Approved negative: return insufficient_evidence and no sections. Approved content: A point metric from the canopy experiment is not a bootstrap interval across independent collections. The requested result is absent from the reviewed full original(s), including tables, formulas and figures. Listed passage references are contextual anchors, not positive evidence or proof of absence; abstain from the requested unsupported result.

Answer excerpt

Response status: `insufficient_evidence`

No answer sections were returned.

Cited visible passages

There are no cited passages for this section-free response.

| Verdict | Notes |
| --- | --- |
|  |  |

## G017

Judgment type: required claim

Question

How does AW-SSIM combine the luminance, contrast and structure sub-functions differently from standard SSIM?

Approved requirement or target

AW-SSIM uses addition instead of multiplication between sub-functions and assigns a constant weight to each component.

Answer excerpt

Response status: `answered`

Section 1

> AW-SSIM adds the luminance, contrast, and structure sub-functions, whereas standard SSIM combines them by multiplication. AW-SSIM also multiplies each sub-function by its own constant weight; the sub-function calculations themselves are the same as in standard SSIM.

Citations: `pmc11121878:p26:w0`, `pmc11121878:p8:w0`

Cited visible passages

### `pmc11121878:p26:w0`

> For AW-SSIM, we apply addition between the three sub-functions, as shown in Equation (6). In addition, we multiply each sub-function, luminance, contrast, and structure, by a constant [formula omitted] , [formula omitted] , and [formula omitted] , respectively. This multiplication with a constant determines the relative importance of each sub-function in the overall AW-SSIM calculation. In weighting the influences of the luminance, contrast, and structure based on the training data content, the model’s robustness and generalization ability are improved. According to our experiment, using different weights based on each sub-function’s importance for a specific training samples, as shown in Figure 4, shows a better result than using equal weights for all sub-functions. The calculations of the luminance, contrast, and structure values in AW-SSIM are the same as in the standard SSIM.

### `pmc11121878:p8:w0`

> In this paper, we propose an autoencoder-based method with training in two stages. The first stage of training is exclusively conducted only on normal samples, and the second stage is training on normal and artificially defective samples using the model weight from the first stage. Experiments in [25] demonstrated that using the mean difference for the luminance calculation in the structural similarity (SSIM) metric [28] can be problematic when used as a loss function for image reconstruction tasks. This is because the mean is insensitive to the range of pixel values within a local area, leading to identical SSIM scores for images with the same average brightness but significantly different light–dark variations. Inspired by this, we propose an adaptive weighted structural similarity (AW-SSIM) loss by introducing addition instead of multiplication between the luminance, contrast, and structure sub-functions. This allows for the removal of the independence between the three sub-functions to compensate for the luminance’s limitations through contrast or structure. Additionally, we dynamically adjust the standard deviation ( [formula omitted] ) for the Gaussian window. This parameter governs the spread of

| Verdict | Notes |
| --- | --- |
|  |  |

## G018

Judgment type: citation

Question

Which pre-trained CNNs were compared with a model trained from scratch for painted heating-device surface classification?

Approved requirement or target

Does the target citation support a substantive part of this section?

Answer excerpt

Response status: `answered`

Target section: 1. Target: single citation.

Target citation: `pmc11768589:p15:w180`

Section 1

> ResNet-50 and Inception V3 were the pre-trained CNNs compared with a CNN built and trained from scratch.

Citations: `pmc11768589:p15:w180`, `pmc11768589:p44:w0`

Cited visible passages

### `pmc11768589:p15:w180`

> regard, in this work, a comparison will be performed between ResNet-50 and Inception V3 for defect detection and classification on the painted surfaces of heating devices. Furthermore, an additional comparison will be performed of these pre-trained models with a CNN built and trained from scratch to demonstrate the potential of TL for defect classification.

### `pmc11768589:p44:w0`

> An automatic inspection system was successfully developed for defect detection and classification on painted surfaces of heating devices, whose components exhibit different topographical features, requiring different illumination modes during acquisition. This system comprised deflectometry and bright light-based image acquisition for dataset generation, DL algorithms for defect detection and classification, surface’s information shipping to a MES server, and a final visual interface for defect information display. Three CNNs were tested: a lightweight CNN built and trained from scratch, and two fine-tuned pre-trained CNNs, ResNet-50, and Inception V3. From the experimental results, the following conclusions can be drawn:

| Verdict | Notes |
| --- | --- |
|  |  |

## G019

Judgment type: qualification

Question

In the two-stage surface-reconstruction study, how did the researchers change which nearby pixels influence learning to balance noise suppression and preservation of small details?

Approved requirement or target

The Gaussian standard deviation changes while the 11-by-11 window dimensions remain fixed; the original gives the symbolic increment k but no numeric value.

Answer excerpt

Response status: `answered`

Section 1

> They dynamically adjusted the Gaussian window’s standard deviation in AW-SSIM, changing the window’s spread—and thus which nearby pixels contribute to the local similarity calculation. This adaptation was intended to balance noise suppression with preservation of fine details.

Citations: `pmc11121878:p1:w0`, `pmc11121878:p8:w0`, `pmc11121878:p46:w0`

Cited visible passages

### `pmc11121878:p1:w0`

> Accurately detecting defects while reconstructing a high-quality normal background in surface defect detection using unsupervised methods remains a significant challenge. This study proposes an unsupervised method that effectively addresses this challenge by achieving both accurate defect detection and a high-quality normal background reconstruction without noise. We propose an adaptive weighted structural similarity (AW-SSIM) loss for focused feature learning. AW-SSIM improves structural similarity (SSIM) loss by assigning different weights to its sub-functions of luminance, contrast, and structure based on their relative importance for a specific training sample. Moreover, it dynamically adjusts the Gaussian window’s standard deviation ( [formula omitted] ) during loss calculation to balance noise reduction and detail preservation. An artificial defect generation algorithm (ADGA) is proposed to generate an artificial defect closely resembling real ones. We use a two-stage training strategy. In the first stage, the model trains only on normal samples using AW-SSIM loss, allowing it to learn robust representations of normal features. In the second stage of training, the weights obtained from the first stage are used to train the model on both normal and artificially defective

### `pmc11121878:p8:w0`

> In this paper, we propose an autoencoder-based method with training in two stages. The first stage of training is exclusively conducted only on normal samples, and the second stage is training on normal and artificially defective samples using the model weight from the first stage. Experiments in [25] demonstrated that using the mean difference for the luminance calculation in the structural similarity (SSIM) metric [28] can be problematic when used as a loss function for image reconstruction tasks. This is because the mean is insensitive to the range of pixel values within a local area, leading to identical SSIM scores for images with the same average brightness but significantly different light–dark variations. Inspired by this, we propose an adaptive weighted structural similarity (AW-SSIM) loss by introducing addition instead of multiplication between the luminance, contrast, and structure sub-functions. This allows for the removal of the independence between the three sub-functions to compensate for the luminance’s limitations through contrast or structure. Additionally, we dynamically adjust the standard deviation ( [formula omitted] ) for the Gaussian window. This parameter governs the spread of

### `pmc11121878:p46:w0`

> The proposed method employs a two-stage training strategy. The first stage of training is performed only on normal samples, utilizing the AW-SSIM loss function. AW-SSIM loss prioritizes the most important features during training by assigning different weights to the three sub-functions (luminance, contrast, and structure). Additionally, it achieves a balance between effective noise control and the preservation of fine details by dynamically adapting the Gaussian window’s standard deviation ( [formula omitted] ). In the second stage of training, artificially defective samples and normal samples are used to train the model and enhance its ability to localize defects. The proposed artificial defect generation algorithm (ADGA) generates artificial defects that closely mimic real-world defects. Furthermore, the second stage of training uses a combined loss function incorporating both AW-SSIM and LPIPS loss, aiming to improve the quality of normal background reconstruction.

| Verdict | Notes |
| --- | --- |
|  |  |

## G020

Judgment type: forbidden claim

Question

What changes to TDI stages and column fixed pattern noise improve particle-defect SNR in the non-patterned wafer study?

Approved requirement or target

A numerical SNR gain not given in the cited passage.

Answer excerpt

Response status: `answered`

Section 1

> Increasing the number of TDI stages improves particle-defect SNR; the study reports that this does not sacrifice detection efficiency because line frequency remains unchanged.

Citations: `pmc10934137:p1:w0`, `pmc10934137:p14:w180`

Section 2

> Reduce column fixed-pattern noise (CFPN) by subtracting particle-free background images from particle images. Changing TDI stages did not significantly alter the CFPN distribution, while image differencing reduced background-image standard deviations by almost 50%.

Citations: `pmc10934137:p15:w0`

Cited visible passages

### `pmc10934137:p1:w0`

> In semiconductor manufacturing, defect inspection in non-patterned wafer production lines is essential to ensure high-quality integrated circuits. However, in actual production lines, achieving both high efficiency and high sensitivity at the same time is a significant challenge due to their mutual constraints. To achieve a reasonable trade-off between detection efficiency and sensitivity, this paper integrates the time delay integration (TDI) technology into dark-field microscopy. The TDI image sensor is utilized instead of a photomultiplier tube to realize multi-point simultaneous scanning. Experiments illustrate that the increase in the number of TDI stages and reduction in the column fixed pattern noise effectively improve the signal-to-noise ratio of particle defects without sacrificing the detecting efficiency.

### `pmc10934137:p14:w180`

> increasing TDI stages. Similar results are obtained through multiple experiments. Without considering the data transmission time, the imaging time is only related to line frequency. Therefore, the increase in the number of TDI stages does not affect the line frequency, thus improving the SNR without sacrificing detection efficiency.

### `pmc10934137:p15:w0`

> It should be noted that in Figure 9e, when the signal intensity of particles is weak at low TDI stages, the presence of stripe-like column fixed pattern noise (CFPN) in the background can impact particle detection. This CFPN is caused by a mismatch between the readout circuits of different columns. Although the correlated dual sampling circuit structure is an effective method to eliminate CFPN, this elimination is incomplete. Figure 11 shows the average CFPN distribution of background images. It is obtained by calculating the average DN value of 200 rows of pixels in the defect-free red dashed area corresponding to different TDI stages in Figure 9. Changing the number of TDI stages does not significantly alter the distribution of CFPN, but only varies in the amplitude of the background signal. Image difference is a simple and effective method to reduce the CFPN. The background images without particles are subtracted from the particle images taken at different TDI stages. Table 4 shows the standard deviations of background images at different TDI stages after CFPN reduction, which are reduced by almost 50%

| Verdict | Notes |
| --- | --- |
|  |  |

## G021

Judgment type: forbidden claim

Question

How does AW-SSIM combine the luminance, contrast and structure sub-functions differently from standard SSIM?

Approved requirement or target

Invented component weights that appear nowhere in the original; the numerical category-specific weights in Figure 4 are valid optional details.

Answer excerpt

Response status: `answered`

Section 1

> Standard SSIM multiplies its luminance, contrast, and structure sub-functions, treating them as independent. AW-SSIM instead adds the three sub-functions and applies a separate constant weight to each, allowing their relative importance to vary and removing their independence. The individual sub-function calculations remain the same as in standard SSIM.

Citations: `pmc11121878:p25:w0`, `pmc11121878:p26:w0`, `pmc11121878:p8:w0`

Cited visible passages

### `pmc11121878:p25:w0`

> The SSIM loss calculation uses multiplication between the three sub-functions to bring independence between these factors, as shown in Equation (6). As demonstrated in [25], the mean used to measure the difference in luminance limits the SSIM’s ability to differentiate between an image with high light–dark variance and an image with more consistent light and dark if the two images have the same mean luminance value. To compensate for the mean with the variance and co-variance values, we should remove the independence between the luminance and other sub-functions through using addition instead of multiplication. [formula omitted]

### `pmc11121878:p26:w0`

> For AW-SSIM, we apply addition between the three sub-functions, as shown in Equation (6). In addition, we multiply each sub-function, luminance, contrast, and structure, by a constant [formula omitted] , [formula omitted] , and [formula omitted] , respectively. This multiplication with a constant determines the relative importance of each sub-function in the overall AW-SSIM calculation. In weighting the influences of the luminance, contrast, and structure based on the training data content, the model’s robustness and generalization ability are improved. According to our experiment, using different weights based on each sub-function’s importance for a specific training samples, as shown in Figure 4, shows a better result than using equal weights for all sub-functions. The calculations of the luminance, contrast, and structure values in AW-SSIM are the same as in the standard SSIM.

### `pmc11121878:p8:w0`

> In this paper, we propose an autoencoder-based method with training in two stages. The first stage of training is exclusively conducted only on normal samples, and the second stage is training on normal and artificially defective samples using the model weight from the first stage. Experiments in [25] demonstrated that using the mean difference for the luminance calculation in the structural similarity (SSIM) metric [28] can be problematic when used as a loss function for image reconstruction tasks. This is because the mean is insensitive to the range of pixel values within a local area, leading to identical SSIM scores for images with the same average brightness but significantly different light–dark variations. Inspired by this, we propose an adaptive weighted structural similarity (AW-SSIM) loss by introducing addition instead of multiplication between the luminance, contrast, and structure sub-functions. This allows for the removal of the independence between the three sub-functions to compensate for the luminance’s limitations through contrast or structure. Additionally, we dynamically adjust the standard deviation ( [formula omitted] ) for the Gaussian window. This parameter governs the spread of

| Verdict | Notes |
| --- | --- |
|  |  |

## G022

Judgment type: required claim

Question

In the two-stage surface-reconstruction study, when the input has made-up damage, which picture is used as the target for the repaired output?

Approved requirement or target

Artificially defective inputs are paired with their clean counterparts; reconstructed images are compared with the normal references.

Answer excerpt

Response status: `answered`

Section 1

> The target is the corresponding non-defective (normal) image—the original image without defects.

Citations: `pmc11121878:p17:w0`, `pmc11121878:p36:w0`

Cited visible passages

### `pmc11121878:p17:w0`

> The training is performed in two stages. In the first stage, the training is performed only on non-defective training samples ( [formula omitted] ), focusing on learning the inherent characteristics of normal images. First, the input image is divided into 128 × 128 patches, and the latent representation is extracted by the encoder. Then, the latent features are fed into the decoder to obtain the reconstructed image ( [formula omitted] ). This stage lays the foundation for the model to understand what constitutes a normal image. Using the weights learned from the first stage of training, the second stage focuses on equipping the model for defect detection. Here, images with artificially introduced defects ( [formula omitted] ) created by the ADGA are paired with their non-defect counterparts ( [formula omitted] ). During training, these pairs are fed into the model. The normal samples ( [formula omitted] ) are used as references to improve the reconstruction performance of the model by comparing a normal sample with the reconstructed image ( [formula omitted] ) from its artificially defective counterpart ( [formula omitted]

### `pmc11121878:p36:w0`

> Here, [formula omitted] is the combined structural and perceptual loss, [formula omitted] is the original image without defects, and [formula omitted] is the reconstructed image from the artificially defective image ( [formula omitted] ).

| Verdict | Notes |
| --- | --- |
|  |  |

## G023

Judgment type: abstention

Question

When the transparent cover is photographed twice, what stops it from shifting relative to the lens?

Approved requirement or target

Approved answerable question: return answered. Approved content: A flexible arm holder keeps lens and sample positions fixed between lighting conditions.

Answer excerpt

Response status: `insufficient_evidence`

No answer sections were returned.

Cited visible passages

There are no cited passages for this section-free response.

| Verdict | Notes |
| --- | --- |
|  |  |

## G024

Judgment type: qualification

Question

What software frameworks and GPU/memory configurations are reported for canopy training and painted-surface training?

Approved requirement or target

Different tasks and datasets; this is not a common-benchmark performance ranking.

Answer excerpt

Response status: `answered`

Section 1

> Canopy training used Python 3.10.14, PyTorch 2.2.2, and CUDA 11.8; the reported setup had 48 GB of memory and an NVIDIA GeForce RTX 4080 GPU with 16 GB of VRAM.

Citations: `pmc11510794:p48:w0`

Section 2

> Painted-surface training used Keras with a TensorFlow backend on a computer with 8 GB of RAM and an NVIDIA GeForce 930MX graphics card.

Citations: `pmc11768589:p24:w0`, `pmc11768589:p37:w0`

Cited visible passages

### `pmc11510794:p48:w0`

> The training environment for the experiments was configured with Python version 3.10.14 and PyTorch version 2.2.2, with CUDA version 11.8 for GPU acceleration. The Ultralytics version 8.2.2 was employed to support model implementation. The hardware setup included an AMD Ryzen™ 7 7800X3D CPU with 8 cores and 16 threads, 48GB of memory, and a NVIDIA® GeForce RTX™ 4080 GPU with 16GB of VRAM. During the training phase, we adopted the hyperparameter settings shown in Table 2.

### `pmc11768589:p24:w0`

> All training and classification employed open sourced Keras framework with TensorFlow backend, implemented on a computer with an Intel®core i7 processor, a RAM memory of 8 GB, and a NVIDIA Geforce 930MX graphic card.

### `pmc11768589:p37:w0`

> Firstly, the most efficient CNN for the detection and classification of defects in the painted surfaces was assessed for one of the defect categories—scratches, and the results are displayed in Figure 7. The self-built network achieved only 75% of accuracy and substantial loss throughout the 250 epochs (Figure 7a). In fact, when tested with images not used for training, this network prompted several incorrect predictions. Furthermore, this model exhibited a large gap between its training and testing losses’ curves, suggesting a possible overfitting problem. Similar results have been reported for models built from scratch [10,13], which can be attributed to the small dataset available for both training and testing in this work. As previously referred, given that defect occurrences are quite rare in most industrial sectors, the constitution of a sizable dataset is challenging, leading to problems of overfitting and unbalanced data [29,36,45]. TL and fine-tuning of pre-trained models were employed in this work to overcome this limitation. These pre-trained networks have shown higher prediction accuracy and possess more robust detection abilities than self-built CNNs [13,46], which was in fact

| Verdict | Notes |
| --- | --- |
|  |  |

## G025

Judgment type: required claim

Question

In the aircraft glass canopy study, why take pictures of the same transparent cover with light arriving from opposite sides, and what information can each view miss?

Approved requirement or target

Backward lighting reveals depth information but can lose surface detail and boundary contours.

Answer excerpt

Response status: `answered`

Section 1

> The two views provide complementary lighting because some canopy defects become sufficiently visible only at particular lighting angles; relying on one lighting condition can therefore lead to missed or false detections. The passages do not specify which particular defects either direction may miss.

Citations: `pmc11510794:p1:w0`, `pmc11510794:p36:w0`

Cited visible passages

### `pmc11510794:p1:w0`

> Defect detection in transparent materials typically relies on specific lighting conditions. However, through our work on defect detection for aircraft glass canopies, we found that using a single lighting condition often led to missed or false detections. This limitation arises from the optical properties of transparent materials, where certain defects only become sufficiently visible under specific lighting angles. To address this issue, we developed a dual-modal illumination system that integrates both forward and backward lighting to capture defect images. Additionally, we introduced the first dual-modal dataset for defect detection in aircraft glass canopies. Furthermore, we proposed an attention-based dual-branch modal fusion network (ADMF-Net) to enhance the detection process. Experimental results show that our system and model significantly improve the detection performance, with the dual-modal approach increasing the mAP by 5.6% over the single-modal baseline, achieving a mAP of 98.4%. Our research also provides valuable insights for defect detection in other transparent materials.

### `pmc11510794:p36:w0`

> The final dataset of aircraft glass canopy defects, named ag_dual_obb, includes four types of defects, totaling 1752 defect points and 4784 defect objects. Each defect point includes two images: a forward lighting image and a backward lighting image, which are strictly spatially aligned. The dataset is divided into a training set with 1576 image pairs and a test set with 176 image pairs, following a 9:1 split ratio. See Table 1.

| Verdict | Notes |
| --- | --- |
|  |  |

## G026

Judgment type: citation

Question

In the wafer study, how does following a moving spot across more sensor rows help a dim feature, and what ideal signal-to-noise improvement is expected when the number of rows is multiplied by m?

Approved requirement or target

Does the target citation support a substantive part of this section?

Answer excerpt

Response status: `answered`

Target section: 1. Target: single citation.

Target citation: `pmc10934137:p7:w0`

Section 1

> As the spot moves across sensor rows, TDI transfers and accumulates the charge from successive images of the same position. This builds up the image signal over multiple integrations, improving contrast and helping obtain a higher-SNR image in low-light conditions—so a dim feature is easier to detect.

Citations: `pmc10934137:p7:w0`

Cited visible passages

### `pmc10934137:p7:w0`

> A TDI image sensor is a kind of special line-scanning image sensor that captures image information through pixels arranged in an array and working in a line-scanning mode. The imaging principle of the TDI image sensor is illustrated in Figure 4. In Figure 4a, the object moves to the left and the integral direction of the TDI image sensor is to the right. At a certain moment, object position p1 is imaged at image position i1. When the object moves after ∆t time, position p1 moves to p2, and the corresponding image position i1 moves to i2. Meanwhile, the charge at position i1 is transferred to position i2 and accumulated. Finally, the entire image in the along-track direction is acquired with the movement of the object. Figure 4b shows that the contrast of the image captured at the same position improves over time. During multiple delay integrations, it is beneficial to obtain higher SNR images in low-light intensity environments.

| Verdict | Notes |
| --- | --- |
|  |  |

## G027

Judgment type: required claim

Question

Compare the canopy study's Mosaic-4 transformations with the painted heater study's crop-based data expansion.

Approved requirement or target

Heater images yield four crops followed by rotations, shifts, zoom, shear and flips.

Answer excerpt

Response status: `answered`

Section 1

> For canopy defects, Mosaic-4 combined images and applied random scaling and translation, contrast and exposure adjustments, and noise addition.

Citations: `pmc11510794:p35:w0`

Section 2

> For the painted-sample study, data expansion began by extracting four 450 × 450 sub-images from each 808 × 608 original, then applying rotations, shifts, zoom, shear, and horizontal and vertical flips; the strategies aimed to reach 500 images per defect category.

Citations: `pmc11768589:p21:w0`

Cited visible passages

### `pmc11510794:p35:w0`

> By following these steps, we ensure that the labels are correctly normalized. Additionally, during the training process, we employed the Mosaic-4 data augmentation method, which includes random image combinations, random scaling and translation, contrast adjustments, exposure adjustments, and noise addition.

### `pmc11768589:p21:w0`

> Given the low availability of painted samples (with and without defects), two strategies were employed to augment the dataset to 500 images per defect category (Figure 2a): (1) four sub-images with 450 × 450 were extracted from the original 808 × 608 images using the GIMP software; and (2) several data augmentation techniques were then performed on the extracted sub-images, including a random 5-degree rotation, height and width shift-range of 1.5, zoom-range of 0.7, shear-range of 0.2, and horizontal and vertical flip transformations. Besides increasing the size of the dataset, these data augmentations also prevented data overfitting and improved the overall performance of the CNNs [10].

| Verdict | Notes |
| --- | --- |
|  |  |

## G028

Judgment type: citation

Question

Why are oriented bounding boxes (OBB) selected for aircraft canopy defect annotation?

Approved requirement or target

Does this section's citation set support every substantive claim?

Answer excerpt

Response status: `answered`

Target section: 1. Target: set citation.

Section 1

> OBB are selected because many detected defects are slender, with high aspect ratios and large image spans, and may be interlaced; rotated boxes are used to annotate and detect these targets.

Citations: `pmc11510794:p31:w0`

Cited visible passages

### `pmc11510794:p31:w0`

> Considering that many of the detected target objects are slender, that is, they have high aspect ratios, large image spans, and may be interlaced, we choose to use oriented bounding boxes (OBB) for annotation and detection.

| Verdict | Notes |
| --- | --- |
|  |  |

## G029

Judgment type: required claim

Question

Compare the reported training/test partition in the canopy dataset with the painted heater dataset.

Approved requirement or target

Canopy uses 1576/176 image pairs, described as 9:1.

Answer excerpt

Response status: `answered`

Section 1

> The canopy dataset used 1,576 image pairs for training and 176 for testing (a 9:1 split); the painted-heater dataset used 80% of its images for training and 20% for testing. Thus, the reported training share was higher for the canopy dataset, while its test share was lower.

Citations: `pmc11510794:p36:w0`, `pmc11768589:p23:w0`

Cited visible passages

### `pmc11510794:p36:w0`

> The final dataset of aircraft glass canopy defects, named ag_dual_obb, includes four types of defects, totaling 1752 defect points and 4784 defect objects. Each defect point includes two images: a forward lighting image and a backward lighting image, which are strictly spatially aligned. The dataset is divided into a training set with 1576 image pairs and a test set with 176 image pairs, following a 9:1 split ratio. See Table 1.

### `pmc11768589:p23:w0`

> From the total dataset generated, 80% of the images were used for training and the remaining 20% for testing. It should be emphasized that models were trained using images acquired with both illumination modes.

| Verdict | Notes |
| --- | --- |
|  |  |

## G030

Judgment type: citation

Question

In the two-stage surface-reconstruction study, why did the network avoid shortcuts between every matching layer of its encoder and decoder?

Approved requirement or target

Does this section's citation set support every substantive claim?

Answer excerpt

Response status: `answered`

Target section: 1. Target: set citation.

Section 1

> Using skip connections at every layer led to partial reconstruction of defects, so the study used only two strategically placed connections to avoid that outcome.

Citations: `pmc11121878:p16:w0`

Cited visible passages

### `pmc11121878:p16:w0`

> The overall architecture of the proposed method is shown in Figure 1. It relies on three key components: the encoder, decoder, and artificial defect generation algorithm (ADGA). The encoder compresses the input image into a lower-dimensional representation using a series of convolutional layers, each employing a sequence of convolution, batch normalization, and activation functions. This compressed representation is then fed into the decoder, which utilizes transposed convolutional layers to progressively upsample the information and reconstruct the original image with high fidelity. Similar to the encoder, each transposed convolutional layer employs a sequence of transposed convolution, batch normalization, and activation functions. The ADGA algorithm create images with artificial defects of various shapes and sizes for the second stage of training. Our model incorporates skip-connections to significantly enhance the performance of the autoencoder. These skip-connections facilitate better information flow between the encoder and decoder, preserving critical fine-grained details in the reconstructed image. While experimenting with various skip-connection configurations, we found that utilizing two strategically placed connections yielded optimal results. Notably, applying skip-connections to all layers resulted in partial defect reconstruction.

| Verdict | Notes |
| --- | --- |
|  |  |

## G031

Judgment type: abstention

Question

In the two-stage surface-reconstruction study, when the input has made-up damage, which picture is used as the target for the repaired output?

Approved requirement or target

Approved answerable question: return answered. Approved content: Artificially defective inputs are paired with their clean counterparts; reconstructed images are compared with the normal references.

Answer excerpt

Response status: `answered`

Section 1

> The target is the clean normal image—the image onto which the artificial defect is pasted.

Citations: `pmc11121878:p19:w0`

Cited visible passages

### `pmc11121878:p19:w0`

> Here, [formula omitted] is an image with an artificial defect, [formula omitted] is a normal image that is used as a target image on which to paste the cropped section from the source image ( [formula omitted] ), and GB is Gaussian blur. The crop () operation represent the cropping of a portion of a source image, Resize () represents the resizing of a cropped portion, and the Paste () operation represents the pasting of the cropped and resized portion to the target image. As shown in Figure 3, the proposed artificial defect generation algorithm (ADGA) can create defective images with defects of different sizes and shapes.

| Verdict | Notes |
| --- | --- |
|  |  |

## G032

Judgment type: required claim

Question

What grayscale and adaptive-binarization preprocessing is applied to structured-illumination heater images, and is it applied to bright-field images?

Approved requirement or target

Structured images undergo RGB-to-grayscale conversion and adaptive binarization to reduce environmental-light effects; bright-field images are not processed this way.

Answer excerpt

Response status: `answered`

Section 1

> Images acquired under structured illumination were converted from RGB to grayscale and adaptively binarized to reduce the effect of environmental lighting.

Citations: `pmc11768589:p22:w0`

Section 2

> Bright-field images were not subjected to this processing.

Citations: `pmc11768589:p22:w0`

Cited visible passages

### `pmc11768589:p22:w0`

> Afterwards, the images were subjected to processing through the conversion RGB to grey scale and the application of adaptive binarization to reduce the effect of the environmental lighting (Figure 2b). It should be emphasized that images obtained via bright field illumination were not subjected to processing.

| Verdict | Notes |
| --- | --- |
|  |  |

## G033

Judgment type: citation

Question

What software frameworks and GPU/memory configurations are reported for canopy training and painted-surface training?

Approved requirement or target

Does the target citation support a substantive part of this section?

Answer excerpt

Response status: `answered`

Target section: 2. Target: single citation.

Target citation: `pmc11768589:p24:w0`

Section 2

> Painted-surface training used Keras with a TensorFlow backend. The reported computer had an Intel Core i7 processor, 8 GB of RAM, and an NVIDIA GeForce 930MX graphics card; GPU memory capacity was not specified.

Citations: `pmc11768589:p24:w0`

Cited visible passages

### `pmc11768589:p24:w0`

> All training and classification employed open sourced Keras framework with TensorFlow backend, implemented on a computer with an Intel®core i7 processor, a RAM memory of 8 GB, and a NVIDIA Geforce 930MX graphic card.

| Verdict | Notes |
| --- | --- |
|  |  |

## G034

Judgment type: qualification

Question

How can the aircraft-cover training pictures be turned and reflected without drawing their defect outlines again?

Approved requirement or target

The eightfold example is specific to 90-degree rotations and mirrors.

Answer excerpt

Response status: `answered`

Section 1

> Apply rotation and mirroring to each training image and its defect labels together, so the outlines are transformed with the image rather than redrawn. Adjust the rotation-angle step to control how many augmented versions are generated; for labels that extend beyond the image, adjust or delete them as needed.

Citations: `pmc11510794:p34:w0`, `pmc11510794:p34:w180`

Cited visible passages

### `pmc11510794:p34:w0`

> To address the limited number of defect images available for aviation transparent parts, we also adopted several data augmentation methods. In order to improve the defect detection performance under any rotation angle, we performed pre-rotation augmentation on the defect samples. In this process, rotation and mirroring operations are simultaneously applied to the images and their labels to avoid redundant annotation work. By adjusting the step size of the rotation angle, the augmentation rate can be controlled. For example, using 90-degree rotations and mirroring operations, an 8× augmentation can be achieved without information loss. For general angles, the background color RGB(114, 114, 0) is filled in the blank areas to reduce interference. Moreover, since the standard OBB format does not allow point coordinates to be located outside the image boundaries, labels that overflow during the rotation process need to be adjusted or deleted. The correction method for overflow labels is as follows:If all four points of the bounding box are outside the field of view, delete the target (process ends), otherwise go to step 2.If all four points of the bounding

### `pmc11510794:p34:w180`

> box are within the field of view, no adjustment is required (process ends), otherwise go to step 3.Select a point that is outside the field of view. Calculate the distance between the point and its adjacent two points to find the long and short sides connected to the point on the rectangle. Translate the short side along the direction of the long side until the point falls on the image boundary. The translation amount is determined by solving a linear programming problem. After adjustment, return to step 2 to re-evaluate.

| Verdict | Notes |
| --- | --- |
|  |  |

## G035

Judgment type: required claim

Question

Which pre-trained CNNs were compared with a model trained from scratch for painted heating-device surface classification?

Approved requirement or target

The paper compares transfer learning of ResNet-50 and Inception V3 with a self-built network.

Answer excerpt

Response status: `answered`

Section 1

> The pre-trained CNNs compared with a model trained from scratch were ResNet-50 and Inception V3.

Citations: `pmc11768589:p15:w180`, `pmc11768589:p44:w0`

Cited visible passages

### `pmc11768589:p15:w180`

> regard, in this work, a comparison will be performed between ResNet-50 and Inception V3 for defect detection and classification on the painted surfaces of heating devices. Furthermore, an additional comparison will be performed of these pre-trained models with a CNN built and trained from scratch to demonstrate the potential of TL for defect classification.

### `pmc11768589:p44:w0`

> An automatic inspection system was successfully developed for defect detection and classification on painted surfaces of heating devices, whose components exhibit different topographical features, requiring different illumination modes during acquisition. This system comprised deflectometry and bright light-based image acquisition for dataset generation, DL algorithms for defect detection and classification, surface’s information shipping to a MES server, and a final visual interface for defect information display. Three CNNs were tested: a lightweight CNN built and trained from scratch, and two fine-tuned pre-trained CNNs, ResNet-50, and Inception V3. From the experimental results, the following conclusions can be drawn:

| Verdict | Notes |
| --- | --- |
|  |  |

## G036

Judgment type: citation

Question

How does AW-SSIM combine the luminance, contrast and structure sub-functions differently from standard SSIM?

Approved requirement or target

Does the target citation support a substantive part of this section?

Answer excerpt

Response status: `answered`

Target section: 1. Target: single citation.

Target citation: `pmc11121878:p8:w0`

Section 1

> Standard SSIM multiplies the luminance, contrast, and structure sub-functions, treating them as independent. AW-SSIM instead adds the sub-functions and applies a separate weight to each, allowing their relative contributions to vary and reducing the independence between them.

Citations: `pmc11121878:p25:w0`, `pmc11121878:p26:w0`, `pmc11121878:p8:w0`

Cited visible passages

### `pmc11121878:p25:w0`

> The SSIM loss calculation uses multiplication between the three sub-functions to bring independence between these factors, as shown in Equation (6). As demonstrated in [25], the mean used to measure the difference in luminance limits the SSIM’s ability to differentiate between an image with high light–dark variance and an image with more consistent light and dark if the two images have the same mean luminance value. To compensate for the mean with the variance and co-variance values, we should remove the independence between the luminance and other sub-functions through using addition instead of multiplication. [formula omitted]

### `pmc11121878:p26:w0`

> For AW-SSIM, we apply addition between the three sub-functions, as shown in Equation (6). In addition, we multiply each sub-function, luminance, contrast, and structure, by a constant [formula omitted] , [formula omitted] , and [formula omitted] , respectively. This multiplication with a constant determines the relative importance of each sub-function in the overall AW-SSIM calculation. In weighting the influences of the luminance, contrast, and structure based on the training data content, the model’s robustness and generalization ability are improved. According to our experiment, using different weights based on each sub-function’s importance for a specific training samples, as shown in Figure 4, shows a better result than using equal weights for all sub-functions. The calculations of the luminance, contrast, and structure values in AW-SSIM are the same as in the standard SSIM.

### `pmc11121878:p8:w0`

> In this paper, we propose an autoencoder-based method with training in two stages. The first stage of training is exclusively conducted only on normal samples, and the second stage is training on normal and artificially defective samples using the model weight from the first stage. Experiments in [25] demonstrated that using the mean difference for the luminance calculation in the structural similarity (SSIM) metric [28] can be problematic when used as a loss function for image reconstruction tasks. This is because the mean is insensitive to the range of pixel values within a local area, leading to identical SSIM scores for images with the same average brightness but significantly different light–dark variations. Inspired by this, we propose an adaptive weighted structural similarity (AW-SSIM) loss by introducing addition instead of multiplication between the luminance, contrast, and structure sub-functions. This allows for the removal of the independence between the three sub-functions to compensate for the luminance’s limitations through contrast or structure. Additionally, we dynamically adjust the standard deviation ( [formula omitted] ) for the Gaussian window. This parameter governs the spread of

| Verdict | Notes |
| --- | --- |
|  |  |

## G037

Judgment type: qualification

Question

In the wafer study, what caused the background stripes in the particle images, and how did the researchers reduce them?

Approved requirement or target

Correlated dual sampling did not eliminate that noise completely.

Answer excerpt

Response status: `answered`

Section 1

> The background stripes were column fixed-pattern noise (CFPN), caused by mismatches between the readout circuits of different sensor columns. Correlated dual sampling reduced the noise but did not eliminate it completely.

Citations: `pmc10934137:p15:w0`

Section 2

> The researchers reduced the stripes by subtracting particle-free background images from the particle images; the background standard deviations after this reduction were almost 50% lower.

Citations: `pmc10934137:p15:w0`

Cited visible passages

### `pmc10934137:p15:w0`

> It should be noted that in Figure 9e, when the signal intensity of particles is weak at low TDI stages, the presence of stripe-like column fixed pattern noise (CFPN) in the background can impact particle detection. This CFPN is caused by a mismatch between the readout circuits of different columns. Although the correlated dual sampling circuit structure is an effective method to eliminate CFPN, this elimination is incomplete. Figure 11 shows the average CFPN distribution of background images. It is obtained by calculating the average DN value of 200 rows of pixels in the defect-free red dashed area corresponding to different TDI stages in Figure 9. Changing the number of TDI stages does not significantly alter the distribution of CFPN, but only varies in the amplitude of the background signal. Image difference is a simple and effective method to reduce the CFPN. The background images without particles are subtracted from the particle images taken at different TDI stages. Table 4 shows the standard deviations of background images at different TDI stages after CFPN reduction, which are reduced by almost 50%

| Verdict | Notes |
| --- | --- |
|  |  |

## G038

Judgment type: qualification

Question

In the wafer study, how does following a moving spot across more sensor rows help a dim feature, and what ideal signal-to-noise improvement is expected when the number of rows is multiplied by m?

Approved requirement or target

The square-root relation is ideal, not a measured guarantee under every noise condition.

Answer excerpt

Response status: `answered`

Section 1

> As the moving feature is tracked across TDI rows, its charge is accumulated over multiple integrations, strengthening its image contrast and helping produce a higher-SNR image in low-light conditions—useful for dim features.

Citations: `pmc10934137:p7:w0`

Section 2

> Ideally, multiplying the number of TDI stages (rows) by m improves SNR by √m.

Citations: `pmc10934137:p8:w180`

Cited visible passages

### `pmc10934137:p7:w0`

> A TDI image sensor is a kind of special line-scanning image sensor that captures image information through pixels arranged in an array and working in a line-scanning mode. The imaging principle of the TDI image sensor is illustrated in Figure 4. In Figure 4a, the object moves to the left and the integral direction of the TDI image sensor is to the right. At a certain moment, object position p1 is imaged at image position i1. When the object moves after ∆t time, position p1 moves to p2, and the corresponding image position i1 moves to i2. Meanwhile, the charge at position i1 is transferred to position i2 and accumulated. Finally, the entire image in the along-track direction is acquired with the movement of the object. Figure 4b shows that the contrast of the image captured at the same position improves over time. During multiple delay integrations, it is beneficial to obtain higher SNR images in low-light intensity environments.

### `pmc10934137:p8:w180`

> Although the significance of TDI sensor noise is acknowledged, it is noteworthy that increasing the number of TDI stages yields a more substantial signal gain compared to the accompanying background noise. Ideally, increasing the number of TDI stages by a factor of m is expected to improve the SNR by √m. This is an effective strategy for enhancing overall system performance.

| Verdict | Notes |
| --- | --- |
|  |  |

## G039

Judgment type: abstention

Question

What optical cues reveal scratches/dents on painted heaters and particle defects on non-patterned wafers?

Approved requirement or target

Approved answerable question: return answered. Approved content: Heater structured illumination detects 3D marks through distortion of reflected patterns. Wafer dark-field inspection collects defect-scattered light against a dark background.

Answer excerpt

Response status: `answered`

Section 1

> On specular painted heater surfaces, scratches and dents distort the reflected structured pattern under deflectometry-based illumination, revealing their three-dimensional features.

Citations: `pmc11768589:p35:w0`

Section 2

> On non-patterned wafers, oblique dark-field illumination produces scattered light from defects, making particles appear bright against a dark background.

Citations: `pmc10934137:p6:w0`

Cited visible passages

### `pmc11768589:p35:w0`

> The application of the two illumination modes—deflectometry-based structured illumination and bright field—was quite successful in the detection of all defects categories, despite their significantly different characteristics and sizes. Indeed, the deflectometry-based illumination was appropriate for the detection of defects with three-dimensional features such as scratches and dents in specular surfaces such as those obtained after the painting process, due to the distortion of the reflected pattern (Figure 6b,c) [2,4]. Conversely, defects derived from the lack of paint, which were much smaller (<0.5 mm), generate different superficial textures that were more easily detected using bright field (Figure 6d). In fact, using deflectometry-based illumination in this instance could trigger incorrect classifications, on the cases that the spots without paint appear in the black stripes of the sinusoidal patterns [18]. A similar multi-modal concept was previously reported by Guan et al. [7]. However, unlike Guan et al. that employed a feature-level fusion, a decision-level fusion method was applied in this work. This method not only preserved all the features extracted from the images retrieved using each illumination mode, but also significantly reduced the

### `pmc10934137:p6:w0`

> Dark-field scattering has emerged as a powerful microscopy technique for detecting and characterizing microscopic particles, structures, and defects. Unlike bright-field microscopy, which illuminates the sample under test with direct light resulting in a bright background, dark-field microscopy employs oblique illumination [30]. Figure 2 illustrates the principle of dark-field and bright-field scattering imaging. The wafer surface is illuminated obliquely by incident light. Complete reflection of the light occurs when there are no defects on the wafer surface. In the presence of defects, the microscopy system collects scattering light, resulting in an image of bright defects against a dark background [31]. This imaging technique can improve the visualization and characterization of small, low-contrast defects that may be difficult to discern using bright-field microscopy [32]. Figure 3 shows the comparison of particles on the non-patterned wafer under bright-field and dark-field conditions via KEYENCE VHX-5000 (Keyence Corporation, Osaka, Japan). Particle scattering on wafer surfaces is complex and its rigorous solution is difficult to obtain. However, it can be expressed qualitatively as [33] [formula omitted] where [formula omitted] represents the particle scattering light intensity, [formula

| Verdict | Notes |
| --- | --- |
|  |  |

## G040

Judgment type: abstention

Question

Who composed the music for the opera The Magic Flute?

Approved requirement or target

Approved negative: return insufficient_evidence and no sections. Approved content: This technical corpus is not evidence for an unrelated music-history answer.

Answer excerpt

Response status: `no_matches`

No answer sections were returned.

Cited visible passages

There are no cited passages for this section-free response.

| Verdict | Notes |
| --- | --- |
|  |  |

## G041

Judgment type: citation

Question

What training examples are used in each stage of the two-stage autoencoder method, and how are stage-one weights used?

Approved requirement or target

Does this section's citation set support every substantive claim?

Answer excerpt

Response status: `answered`

Target section: 1. Target: set citation.

Section 1

> Stage one trains on normal (non-defective) samples only, learning the characteristics of normal images.

Citations: `pmc11121878:p17:w0`, `pmc11121878:p8:w0`

Cited visible passages

### `pmc11121878:p17:w0`

> The training is performed in two stages. In the first stage, the training is performed only on non-defective training samples ( [formula omitted] ), focusing on learning the inherent characteristics of normal images. First, the input image is divided into 128 × 128 patches, and the latent representation is extracted by the encoder. Then, the latent features are fed into the decoder to obtain the reconstructed image ( [formula omitted] ). This stage lays the foundation for the model to understand what constitutes a normal image. Using the weights learned from the first stage of training, the second stage focuses on equipping the model for defect detection. Here, images with artificially introduced defects ( [formula omitted] ) created by the ADGA are paired with their non-defect counterparts ( [formula omitted] ). During training, these pairs are fed into the model. The normal samples ( [formula omitted] ) are used as references to improve the reconstruction performance of the model by comparing a normal sample with the reconstructed image ( [formula omitted] ) from its artificially defective counterpart ( [formula omitted]

### `pmc11121878:p8:w0`

> In this paper, we propose an autoencoder-based method with training in two stages. The first stage of training is exclusively conducted only on normal samples, and the second stage is training on normal and artificially defective samples using the model weight from the first stage. Experiments in [25] demonstrated that using the mean difference for the luminance calculation in the structural similarity (SSIM) metric [28] can be problematic when used as a loss function for image reconstruction tasks. This is because the mean is insensitive to the range of pixel values within a local area, leading to identical SSIM scores for images with the same average brightness but significantly different light–dark variations. Inspired by this, we propose an adaptive weighted structural similarity (AW-SSIM) loss by introducing addition instead of multiplication between the luminance, contrast, and structure sub-functions. This allows for the removal of the independence between the three sub-functions to compensate for the luminance’s limitations through contrast or structure. Additionally, we dynamically adjust the standard deviation ( [formula omitted] ) for the Gaussian window. This parameter governs the spread of

| Verdict | Notes |
| --- | --- |
|  |  |

## G042

Judgment type: qualification

Question

Which sinusoidal frequencies, stripe counts and phase are tested for painted heating-device illumination?

Approved requirement or target

Hz is the paper's reported label for generated spatial patterns; do not infer a temporal monitor-refresh frequency or convert to cycles/mm without calibration.

Answer excerpt

Response status: `answered`

Section 1

> The tested sinusoidal patterns used 0.8 Hz for 20 stripes and 1.6 Hz for 40 stripes; the phase θ was 0 for both frequencies.

Citations: `pmc11768589:p18:w0`

Cited visible passages

### `pmc11768589:p18:w0`

> The frequency controlled the thickness of the strips, while the phase shifted the pattern in X or Y direction [4]. Two frequencies were used to generate patterns with different numbers of stripes: 0.8 Hz for 20 stripes, and 1.6 Hz for 40 stripes. The θ was 0 for both frequencies tested.

| Verdict | Notes |
| --- | --- |
|  |  |

## G043

Judgment type: abstention

Question

Which SQL transaction isolation level prevents phantom reads?

Approved requirement or target

Approved negative: return insufficient_evidence and no sections. Approved content: The four surface-inspection papers do not support this unrelated question; abstain from a document-only answer.

Answer excerpt

Response status: `insufficient_evidence`

No answer sections were returned.

Cited visible passages

There are no cited passages for this section-free response.

| Verdict | Notes |
| --- | --- |
|  |  |

## G044

Judgment type: citation

Question

Which sinusoidal frequencies, stripe counts and phase are tested for painted heating-device illumination?

Approved requirement or target

Does this section's citation set support every substantive claim?

Answer excerpt

Response status: `answered`

Target section: 1. Target: set citation.

Section 1

> The sinusoidal patterns tested were 0.8 Hz for 20 stripes and 1.6 Hz for 40 stripes; θ (phase) was 0 for both frequencies.

Citations: `pmc11768589:p18:w0`

Cited visible passages

### `pmc11768589:p18:w0`

> The frequency controlled the thickness of the strips, while the phase shifted the pattern in X or Y direction [4]. Two frequencies were used to generate patterns with different numbers of stripes: 0.8 Hz for 20 stripes, and 1.6 Hz for 40 stripes. The θ was 0 for both frequencies tested.

| Verdict | Notes |
| --- | --- |
|  |  |

## G045

Judgment type: citation

Question

What grayscale and adaptive-binarization preprocessing is applied to structured-illumination heater images, and is it applied to bright-field images?

Approved requirement or target

Does the target citation support a substantive part of this section?

Answer excerpt

Response status: `answered`

Target section: 1. Target: single citation.

Target citation: `pmc11768589:p22:w0`

Section 1

> Structured-illumination heater images are converted from RGB to grayscale and adaptively binarized to reduce the effects of environmental lighting.

Citations: `pmc11768589:p22:w0`

Cited visible passages

### `pmc11768589:p22:w0`

> Afterwards, the images were subjected to processing through the conversion RGB to grey scale and the application of adaptive binarization to reduce the effect of the environmental lighting (Figure 2b). It should be emphasized that images obtained via bright field illumination were not subjected to processing.

| Verdict | Notes |
| --- | --- |
|  |  |

## G046

Judgment type: abstention

Question

How many confirmed moons does Jupiter have as of September 2026?

Approved requirement or target

Approved negative: return insufficient_evidence and no sections. Approved content: The four surface-inspection papers do not support this unrelated question; abstain from a document-only answer.

Answer excerpt

Response status: `insufficient_evidence`

No answer sections were returned.

Cited visible passages

There are no cited passages for this section-free response.

| Verdict | Notes |
| --- | --- |
|  |  |

## G047

Judgment type: forbidden claim

Question

What X-AnyLabeling version and Segment Anything variant are used for canopy pre-labeling, and how are OBBs derived?

Approved requirement or target

Human annotation checks were unnecessary.

Answer excerpt

Response status: `answered`

Section 1

> The described workflow uses X-AnyLabeling version 2.3.5 with the Segment Anything ViT-Large model for pre-labeling; it produces polygon boundaries, from which a script calculates the minimum enclosing rectangle to create a rotated bounding box. The passage describes this for selected defects, not specifically canopy.

Citations: `pmc11510794:p32:w0`

Cited visible passages

### `pmc11510794:p32:w0`

> We use X-AnyLabeling [27] (version 2.3.5) for data annotation, which allows the use of existing segmentation models to improve annotation efficiency. We choose the Segment Anything (ViT-Large) model for pre-labeling, which provides preparatory polygon boundaries of the selected defects. Then, a script is written to calculate the minimum enclosing rectangle for each defect, resulting in a more precise rotated bounding box.

| Verdict | Notes |
| --- | --- |
|  |  |

## G048

Judgment type: required claim

Question

How do the canopy and painted heating-device studies differ in their illumination modalities and fusion levels?

Approved requirement or target

Canopy inspection combines forward/backward lighting with RGB data-level fusion and an ADMF-Net feature-level method.

Answer excerpt

Response status: `answered`

Section 1

> The canopy study used forward and backward lighting, with data-level RGB Channel Fusion and a separate feature-level fusion network (ADMF-Net).

Citations: `pmc11510794:p5:w0`, `pmc11510794:p59:w0`

Section 2

> The painted heating-device study used bright-field and deflectometry-based structured illumination, combining the modalities at the decision level.

Citations: `pmc11768589:p5:w0`, `pmc11768589:p11:w0`

Cited visible passages

### `pmc11510794:p5:w0`

> Our contributions can be summarized as follows:An automated prototype system with a dual-modal illumination structure is proposed. For the same sampling point, the system sequentially uses forward lighting and backward lighting to capture defect images. By integrating the information from both types of images, more accurate defect detection is achieved.A curated dataset is presented, which, to the best of our knowledge, is the first benchmark in the field of defect detection for aircraft transparent materials.A dual-modal baseline is designed and proved to be competitive, in which we designed two fusion detection methods: a data-level fusion method named RGB Channel Fusion, and an attention-based dual-branch modal fusion network using feature-level fusion. Both methods achieved excellent results on our dataset.

### `pmc11510794:p59:w0`

> Furthermore, we proposed a data-level fusion method named RGB Channel Fusion, and a feature-level fusion model, the attention-based dual-branch modal fusion network (ADMF-Net). The model uses two feature extraction backbones to independently extract multi-scale features from the forward and backward lighting modalities. Next, through the attention-based multi-modal feature fusion block (AMFF) and improved SPPF module, the network adaptively integrates the multi-scale features from the two modalities. Finally, the features are fed into the detection layers, where an OBB detection head is used to provide the rotated bounding boxes of defects.

### `pmc11768589:p5:w0`

> Heating devices, such as water heaters (electric and gas), boilers, and heat pumps, usually require a paint coating for aesthetic and protection purposes. Despite the extensive vision-based deep learning reports for surface defect detection, to the best of the authors’ knowledge, only a few reports applied this technology to the heating products [15]. The components of these products usually have different topographical features (specular and diffuse) that require a detection system with different illumination modes to effectively identify all possible defects on their surface. Hence, in the present work, an automatic vision inspection system was proposed for the detection and classification of defects on the painted surfaces of heating devices, which included the following: (1) an image acquisition module for dataset generation employing two illumination strategies (bright field and deflectometry-based lighting), (2) DL models for defect detection and classification with decision-level fusion, (3) painted surface information dispatching to a designed server, and (4) image graphical display. Regarding the feature extraction and decision-making performed by the DL models, two approaches were compared: (1) a CNN built and trained from scratch; and

### `pmc11768589:p11:w0`

> Conversely, the decision-level fusion employs two different decision-making models for each acquisition source for defect detection, whose outputs are then combined [9]. In this instance, besides being compatible with feature extraction of the information obtained from different illumination strategies/sources, this fusion method has low computational complexity and is suitable for real-time applications [21]. Using this approach, Hu et al. proposed an object detection system combining the output of two models classifying information retrieved from bright field and infrared imaging. The results indicated that this system effectively fuses the information from multiple decision-making models to improve the overall performance of the object detection [21]. Similarly, Cong et al. also employed a decision-level fusion method of bright field and infrared-based light that exhibited higher precision and robustness for object detection than single-modal methods [22]. Despite its more prevalent use with infrared imaging, this type of information fusion can be easily employed for other illumination strategies. Addressing this gap, this work will explore decision-level fusion in images retrieved from bright field and deflectometry-based structured illumination.

| Verdict | Notes |
| --- | --- |
|  |  |

## G049

Judgment type: forbidden claim

Question

Compare the canopy study's Mosaic-4 transformations with the painted heater study's crop-based data expansion.

Approved requirement or target

Claiming a head-to-head evaluation on identical data.

Answer excerpt

Response status: `answered`

Section 1

> For canopy defects, Mosaic-4 combined images and applied random scaling and translation, contrast and exposure adjustments, and noise addition.

Citations: `pmc11510794:p35:w0`

Section 2

> For the painted-sample study, data expansion began by extracting four 450 × 450 sub-images from each 808 × 608 original, then applying rotations, shifts, zoom, shear, and horizontal and vertical flips; the strategies aimed to reach 500 images per defect category.

Citations: `pmc11768589:p21:w0`

Cited visible passages

### `pmc11510794:p35:w0`

> By following these steps, we ensure that the labels are correctly normalized. Additionally, during the training process, we employed the Mosaic-4 data augmentation method, which includes random image combinations, random scaling and translation, contrast adjustments, exposure adjustments, and noise addition.

### `pmc11768589:p21:w0`

> Given the low availability of painted samples (with and without defects), two strategies were employed to augment the dataset to 500 images per defect category (Figure 2a): (1) four sub-images with 450 × 450 were extracted from the original 808 × 608 images using the GIMP software; and (2) several data augmentation techniques were then performed on the extracted sub-images, including a random 5-degree rotation, height and width shift-range of 1.5, zoom-range of 0.7, shear-range of 0.2, and horizontal and vertical flip transformations. Besides increasing the size of the dataset, these data augmentations also prevented data overfitting and improved the overall performance of the CNNs [10].

| Verdict | Notes |
| --- | --- |
|  |  |

## G050

Judgment type: citation

Question

Which metrics quantify canopy object-detection performance and autoencoder anomaly-detection performance, and can their numerical scores be ranked directly?

Approved requirement or target

Does the target citation support a substantive part of this section?

Answer excerpt

Response status: `answered`

Target section: 3. Target: single citation.

Target citation: `pmc11510794:p47:w0`

Section 3

> Their numerical scores should not be ranked directly: they are different metrics, with mAP based on precision-recall performance and AuROC evaluating anomaly-detection performance.

Citations: `pmc11510794:p47:w0`, `pmc11121878:p38:w0`

Cited visible passages

### `pmc11510794:p47:w0`

> We evaluate the model’s detection performance using the mean average precision (mAP). Precision is the ratio of true positives (TP) to the sum of true positives and false positives (FP), indicating the accuracy of positive predictions. Recall is the ratio of true positives to the sum of true positives and false negatives (FN), reflecting how well the model detects all relevant instances. Average precision (AP) measures the area under the precision-recall curve, denoted as [formula omitted] , which describes the relationship between precision and recall as the confidence threshold changes. The final mAP is obtained by averaging the AP values across all classes. In this study, we use both the conventional mAP50, which evaluates at an intersection over union (IoU) threshold of 0.5, and the stricter mAP50-95, which averages over multiple IoU thresholds from 0.5 to 0.95 in steps of 0.05. [formula omitted]

### `pmc11121878:p38:w0`

> For our experiments, we used diverse anomaly detection samples sourced from the MVTec AD dataset [47], including leather, carpet, hazelnut, pill, wood, and tile textures. In total, 1660 and 714 samples were used for training and testing, respectively. All images were resized to 512 × 512 pixels during training. Training was performed using an Adam optimizer trained for a total of 25 epochs in two stages. To quantitatively assess the performances of various methods, we chose the area under the receiver operating characteristic curve (AuROC) as the evaluation metric. This metric is insensitive to threshold variations and provides a more accurate evaluation of the models’ inspection capabilities.

| Verdict | Notes |
| --- | --- |
|  |  |

## G051

Judgment type: abstention

Question

What X-AnyLabeling version and Segment Anything variant are used for canopy pre-labeling, and how are OBBs derived?

Approved requirement or target

Approved answerable question: return answered. Approved content: X-AnyLabeling 2.3.5 uses Segment Anything ViT-Large to propose polygons; a script calculates each minimum enclosing rectangle.

Answer excerpt

Response status: `answered`

Section 1

> Canopy defects are pre-labeled with X-AnyLabeling version 2.3.5 using the Segment Anything ViT-Large model, which provides preparatory polygon boundaries.

Citations: `pmc11510794:p32:w0`

Section 2

> OBBs are derived by calculating the minimum enclosing rectangle for each defect’s polygon boundary, producing a rotated bounding box.

Citations: `pmc11510794:p32:w0`

Cited visible passages

### `pmc11510794:p32:w0`

> We use X-AnyLabeling [27] (version 2.3.5) for data annotation, which allows the use of existing segmentation models to improve annotation efficiency. We choose the Segment Anything (ViT-Large) model for pre-labeling, which provides preparatory polygon boundaries of the selected defects. Then, a script is written to calculate the minimum enclosing rectangle for each defect, resulting in a more precise rotated bounding box.

| Verdict | Notes |
| --- | --- |
|  |  |

## G052

Judgment type: forbidden claim

Question

How must TDI line frequency and charge-accumulation direction relate to wafer motion to avoid blur?

Approved requirement or target

Increasing line frequency alone guarantees sharp images at arbitrary speeds.

Answer excerpt

Response status: `answered`

Section 1

> To avoid blur, set the TDI line frequency to match the wafer’s motion speed and make the charge-accumulation direction opposite to the wafer’s motion direction.

Citations: `pmc10934137:p10:w0`

Cited visible passages

### `pmc10934137:p10:w0`

> Imaging quality is affected by multiple factors such as illumination conditions, mechanical movement, and imaging systems. To ensure that the 2D image captured by the TDI image sensor is not blurry due to the rapid motion of the object, the line frequency needs to match the wafer movement speed, and the direction of charge accumulation needs to be opposite to the motion direction of the wafer. Thus, the image has the same resolution in the x-direction and the y-direction. We set the line frequency of the TDI image sensor according to the following equation: [formula omitted] where [formula omitted] is the FOV width, [formula omitted] is the number of pixels in the across-track direction, and [formula omitted] is the motion speed of the object. The diffraction-limited resolution is calculated as [formula omitted] according to the Rayleigh criterion and the Nyquist sampling law. In addition, the system achieves a detection sensitivity of defect size 0.5 μm, and possibly even smaller ones. This is described in Experimental Section.

| Verdict | Notes |
| --- | --- |
|  |  |

## G053

Judgment type: qualification

Question

In the two-stage surface-reconstruction study, when the input has made-up damage, which picture is used as the target for the repaired output?

Approved requirement or target

The artificial defect is on the input, not the desired output.

Answer excerpt

Response status: `answered`

Section 1

> The target is the clean normal image—the image onto which the artificial defect is pasted.

Citations: `pmc11121878:p19:w0`

Cited visible passages

### `pmc11121878:p19:w0`

> Here, [formula omitted] is an image with an artificial defect, [formula omitted] is a normal image that is used as a target image on which to paste the cropped section from the source image ( [formula omitted] ), and GB is Gaussian blur. The crop () operation represent the cropping of a portion of a source image, Resize () represents the resizing of a cropped portion, and the Paste () operation represents the pasting of the cropped and resized portion to the target image. As shown in Figure 3, the proposed artificial defect generation algorithm (ADGA) can create defective images with defects of different sizes and shapes.

| Verdict | Notes |
| --- | --- |
|  |  |

## G054

Judgment type: qualification

Question

How do the canopy and painted heating-device studies differ in their illumination modalities and fusion levels?

Approved requirement or target

These are different tasks and datasets; no common-benchmark superiority follows.

Answer excerpt

Response status: `answered`

Section 1

> The canopy study uses forward and backward lighting images and combines them at the data level: grayscale versions are assigned to the red and green channels, and their average forms the blue channel.

Citations: `pmc11510794:p38:w0`

Section 2

> The painted heating-device study uses bright-field and deflectometry-based lighting, with fusion at the decision level.

Citations: `pmc11768589:p5:w0`, `pmc11768589:p45:w0`

Cited visible passages

### `pmc11510794:p38:w0`

> To initially validate the effectiveness of fusion detection for this task, we first designed a data-level fusion method named RGB Channel Fusion, as shown in Figure 7. In the RGB Channel Fusion method, the forward lighting image and the backward lighting image are each converted to grayscale. These grayscale images are then assigned to the red channel and green channel of the fused image, respectively, while the blue channel is obtained by averaging the two grayscale images.

### `pmc11768589:p5:w0`

> Heating devices, such as water heaters (electric and gas), boilers, and heat pumps, usually require a paint coating for aesthetic and protection purposes. Despite the extensive vision-based deep learning reports for surface defect detection, to the best of the authors’ knowledge, only a few reports applied this technology to the heating products [15]. The components of these products usually have different topographical features (specular and diffuse) that require a detection system with different illumination modes to effectively identify all possible defects on their surface. Hence, in the present work, an automatic vision inspection system was proposed for the detection and classification of defects on the painted surfaces of heating devices, which included the following: (1) an image acquisition module for dataset generation employing two illumination strategies (bright field and deflectometry-based lighting), (2) DL models for defect detection and classification with decision-level fusion, (3) painted surface information dispatching to a designed server, and (4) image graphical display. Regarding the feature extraction and decision-making performed by the DL models, two approaches were compared: (1) a CNN built and trained from scratch; and

### `pmc11768589:p45:w0`

> The two illumination modes of the image acquisition module significantly widened the type of defects that could be identified with this system, while maintaining its computational complexity by performing multi-modal fusion at the decision level.

| Verdict | Notes |
| --- | --- |
|  |  |

## G055

Judgment type: forbidden claim

Question

How did the heater researchers enlarge a limited supply of surface photographs before fitting their classifiers?

Approved requirement or target

The study inspected 500 independently acquired heaters per category.

Answer excerpt

Response status: `answered`

Section 1

> They extracted four 450 × 450 sub-images from each original 808 × 608 image, then augmented the crops with random 5° rotations, height and width shifts, zoom, shear, and horizontal and vertical flips. These steps expanded the dataset to 500 images per defect category before classifier training.

Citations: `pmc11768589:p21:w0`

Cited visible passages

### `pmc11768589:p21:w0`

> Given the low availability of painted samples (with and without defects), two strategies were employed to augment the dataset to 500 images per defect category (Figure 2a): (1) four sub-images with 450 × 450 were extracted from the original 808 × 608 images using the GIMP software; and (2) several data augmentation techniques were then performed on the extracted sub-images, including a random 5-degree rotation, height and width shift-range of 1.5, zoom-range of 0.7, shear-range of 0.2, and horizontal and vertical flip transformations. Besides increasing the size of the dataset, these data augmentations also prevented data overfitting and improved the overall performance of the CNNs [10].

| Verdict | Notes |
| --- | --- |
|  |  |

## G056

Judgment type: qualification

Question

Which pretraining dataset and input image size are reported for the transferred ResNet-50 and Inception V3 classifiers?

Approved requirement or target

This describes classifier initialization and study inputs, not new training on the complete ImageNet dataset.

Answer excerpt

Response status: `answered`

Section 1

> The transferred ResNet-50 and Inception V3 classifiers were pretrained on ImageNet, using at least one million images; their input image size was 450 × 450 pixels.

Citations: `pmc11768589:p26:w0`

Cited visible passages

### `pmc11768589:p26:w0`

> The second approach entailed the TL and fine-tunning of two common pre-trained CNNs: ResNet-50 and Inception V3. These networks have been trained on at least one million images from the ImageNet and have over 23 million trainable parameters [43]. The input image size of these pre-trained CNNs was also 450 × 450.

| Verdict | Notes |
| --- | --- |
|  |  |

## G057

Judgment type: qualification

Question

When the transparent cover is photographed twice, what stops it from shifting relative to the lens?

Approved requirement or target

This explains the fixture's role, not a measured registration-error bound.

Answer excerpt

Response status: `answered`

Section 1

> A flexible arm holder supports the setup to maintain a fixed position between the camera lens and the sample during the two image captures.

Citations: `pmc11510794:p27:w0`

Cited visible passages

### `pmc11510794:p27:w0`

> Due to the necessity of maintaining a fixed position between the camera lens and the sample when capturing images under two lighting conditions, we used a flexible arm holder as the support device. This device has a length of 60 cm and a maximum load capacity of 1.0 kg, providing sufficient stability for the image acquisition process.

| Verdict | Notes |
| --- | --- |
|  |  |

## G058

Judgment type: abstention

Question

Which pretraining dataset and input image size are reported for the transferred ResNet-50 and Inception V3 classifiers?

Approved requirement or target

Approved answerable question: return answered. Approved content: They are pretrained on ImageNet; both use 450 by 450 input images in this study.

Answer excerpt

Response status: `answered`

Section 1

> The transferred ResNet-50 and Inception V3 classifiers were pretrained on ImageNet and used input images sized 450 × 450 pixels.

Citations: `pmc11768589:p26:w0`

Cited visible passages

### `pmc11768589:p26:w0`

> The second approach entailed the TL and fine-tunning of two common pre-trained CNNs: ResNet-50 and Inception V3. These networks have been trained on at least one million images from the ImageNet and have over 23 million trainable parameters [43]. The input image size of these pre-trained CNNs was also 450 × 450.

| Verdict | Notes |
| --- | --- |
|  |  |

## G059

Judgment type: citation

Question

In the wafer study, what caused the background stripes in the particle images, and how did the researchers reduce them?

Approved requirement or target

Does the target citation support a substantive part of this section?

Answer excerpt

Response status: `answered`

Target section: 2. Target: single citation.

Target citation: `pmc10934137:p15:w0`

Section 2

> The researchers reduced the stripes by subtracting particle-free background images from the particle images; the background standard deviations after this reduction were almost 50% lower.

Citations: `pmc10934137:p15:w0`

Cited visible passages

### `pmc10934137:p15:w0`

> It should be noted that in Figure 9e, when the signal intensity of particles is weak at low TDI stages, the presence of stripe-like column fixed pattern noise (CFPN) in the background can impact particle detection. This CFPN is caused by a mismatch between the readout circuits of different columns. Although the correlated dual sampling circuit structure is an effective method to eliminate CFPN, this elimination is incomplete. Figure 11 shows the average CFPN distribution of background images. It is obtained by calculating the average DN value of 200 rows of pixels in the defect-free red dashed area corresponding to different TDI stages in Figure 9. Changing the number of TDI stages does not significantly alter the distribution of CFPN, but only varies in the amplitude of the background signal. Image difference is a simple and effective method to reduce the CFPN. The background images without particles are subtracted from the particle images taken at different TDI stages. Table 4 shows the standard deviations of background images at different TDI stages after CFPN reduction, which are reduced by almost 50%

| Verdict | Notes |
| --- | --- |
|  |  |

## G060

Judgment type: forbidden claim

Question

Which pretraining dataset and input image size are reported for the transferred ResNet-50 and Inception V3 classifiers?

Approved requirement or target

The study collected a million new heater images.

Answer excerpt

Response status: `answered`

Section 1

> The transferred ResNet-50 and Inception V3 classifiers were pretrained on ImageNet, using at least one million images.

Citations: `pmc11768589:p26:w0`

Section 2

> Their input image size was 450 × 450 pixels.

Citations: `pmc11768589:p26:w0`

Cited visible passages

### `pmc11768589:p26:w0`

> The second approach entailed the TL and fine-tunning of two common pre-trained CNNs: ResNet-50 and Inception V3. These networks have been trained on at least one million images from the ImageNet and have over 23 million trainable parameters [43]. The input image size of these pre-trained CNNs was also 450 × 450.

| Verdict | Notes |
| --- | --- |
|  |  |

## Source attribution

The passages above are normalized, sometimes truncated excerpts from these licensed articles. The archived extraction omitted formulas and other non-prose material. Source links identify attribution; grade only the visible text above.

- `pmc10934137`: Fei Yu, Min Xu, Junhua Wang, Xiangchao Zhang, Xinlan Tang. [Balancing the Efficiency and Sensitivity of Defect Inspection of Non-Patterned Wafers with TDI-Based Dark-Field Scattering Microscopy](https://pmc.ncbi.nlm.nih.gov/articles/PMC10934137/). 2024-03-01. [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).
- `pmc11121878`: Tesfaye Getachew Shiferaw, Li Yao. [Autoencoder-Based Unsupervised Surface Defect Detection Using Two-Stage Training](https://pmc.ncbi.nlm.nih.gov/articles/PMC11121878/). 2024-05-05. [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).
- `pmc11510794`: Zijian Li, Yong Yao, Runyuan Wen, Qiyang Liu. [Dual-Modal Illumination System for Defect Detection of Aircraft Glass Canopies](https://pmc.ncbi.nlm.nih.gov/articles/PMC11510794/). 2024-10-18. [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).
- `pmc11768589`: Ângela Semitela, Miguel Pereira, António Completo, Nuno Lau, José P Santos. [Improving Industrial Quality Control: A Transfer Learning Approach to Surface Defect Detection](https://pmc.ncbi.nlm.nih.gov/articles/PMC11768589/). 2025-01-17. [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).
