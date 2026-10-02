# Fixed-pool information-needs experiments

This development study tests factual subquestions and new document representations
after the earlier rule-based selector regressed. It keeps all 50 approved questions,
the separate approved evidence groups, four canonical output passages and existing
answer limits fixed. It never searches held-out questions or generates answers.

## Fixed candidates and separate inference stages

The saved Qwen3-4B dense run supplies the same ordered 40 candidates for every
selection policy. Loading verifies the dataset, embedding artifact hash, successful
stable rankings, unique IDs and complete canonical metadata/text against the index.
Selection cannot add candidates, inspect evidence labels or change citation identity.
The pool contains complete approved support for 34/36 answerable questions.

The predefined policies are dense order, whole-question BGE reranking, earlier rule
subqueries with maximum-rank selection, and three local-model subquery selectors:
maximum-rank utility, saturation utility, and round-robin selection.

The model extracts one to six subject/aspect pairs. Each value must be a contiguous
phrase copied exactly from the question. Queries concatenate those copied phrases.
No indexed documents, expected sources, claims or evidence annotations enter the
extraction prompt. Copying prevents invented query entities and synonyms; it does
not ensure that every qualification is preserved or that decomposition is sensible.
The resulting subquestions are experimental model outputs, not reviewed labels.

The initial prompt-only grounding run rejected 24/50 outputs. Rejected cases remain
explicit errors without retries or fallback. A separately recorded development
correction constrains JSON decoding to question phrases of at most 12 words, plus
the complete question. An empty subject is permitted; an aspect cannot be empty.
The revised schema produces valid outputs for all 50 questions. The prompt and
selection weights were unchanged. The initial run and its source snapshot remain
archived; this correction is not presented as a clean first attempt.

The local model and BGE reranker load once each. Each distinct question/subquery is
scored once against all 40 candidates. Shared score matrices and model outputs are
saved and reused across policies. This explicitly isolates the selection objective
and avoids repeating expensive inference for every policy. Shared-runner quality
scoring, evidence coverage and answer-context previews remain authoritative.

Replay timing measures selection and observation only. It excludes CPU query
encoding, question decomposition and reranker inference, so it must not be advertised
as live query latency. The measurement bundle records per-case decomposition time,
per-query scoring time, token visibility, usage and server memory separately.
These single staged timings have no matched warmup/repeat protocol and do not
establish CPU/GPU speedup or complete application throughput.

## Model and selection conventions

Question extraction uses [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507),
served locally through the already pinned llama.cpp b11327 Windows Vulkan runtime.
The public GGUF comes from
[unsloth/Qwen3-4B-Instruct-2507-GGUF](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/tree/a06e946bb6b655725eafa393f4a9745d460374c9),
revision `a06e946bb6b655725eafa393f4a9745d460374c9`, file
`Qwen3-4B-Instruct-2507-Q4_K_M.gguf`. The model card declares Apache-2.0 and
multilingual support; this study tests English only. The first explicit preparation
downloads several GB. Startup is cache-only and verifies both the recorded GGUF
checksum and pinned runtime executable. No Hugging Face credentials are used.
There is no claim of equivalence with upstream full-precision generation.

Settings are temperature 0, seed 42, at most 384 output tokens, a 4,096-token
context, one slot and verified RX 6800 Vulkan offload. JSON-schema decoding and
postvalidation both enforce the copied-phrase contract. The server binds only
loopback, starts hidden, disables the host prompt cache and has a 6 GiB native
private-memory guard. Assets and server processes are independent of production
startup. This model performs query extraction, not answer generation.

Maximum-rank selection uses `11 / (11 + rank)` and greedily improves the best utility
already covered for each query. Original-query weight is 0.5; subquery weights are 1.
This is the same objective as the previous experiment, with a fixed candidate pool.
The rule ablation uses previous subquery strings without candidate/document quotas.

Saturation selection maps BGE logits through a sigmoid, uses original-query weight
0.25 and subquery weights 1, and adds diminishing utility through
`remaining *= 1 - utility`. A 0.1 penalty discourages cosine similarity with selected
passages. These are uncalibrated utilities, not support probabilities or an
answerability threshold. Round-robin selection takes the best unused passage for
each subquery in turn. All policies break ties deterministically and preserve the
full canonical passages.

## Enriched vector experiments

Two separately built Qwen3-4B artifacts test title/section context and that context
plus at most 60 words from each immediately adjacent passage in the same document.
The representation puts canonical passage text before auxiliary neighboring text.
Neighbor evidence influences scoring but is not added to the returned passage or
provider budget. Query instructions, pooling, precision and the 512-token limit
remain fixed. No canonical chunks, extraction, IDs or evidence mappings change.

Artifacts persist original corpus/chunking metadata, canonical passages, the pinned
encoding settings, representation version, actual input hash, canonical-text input
ranges, vector order and checksums. Their encoding contract is version 3; normal
application startup rejects these experimental artifacts. Use the explicit
`RepresentedRetriever` integration instead. It checks representation identity and
query-encoder compatibility before searching.

Raw input measurements retain actual token counts, encoded ranges and input hashes.
The evaluator's visibility sidecar maps those offsets back to canonical passage text.
Clipped auxiliary text and clipped canonical text are reported separately. A full
canonical range does not mean every neighbor was encoded. Each representation is
built before its queries run, and its encoder/index remain loaded for the study.
Both variants share one Python process, so peak working set is a cumulative process
measurement, not an isolated per-model memory allocation.

## Reproduce and integrate

From the repository root, using the existing pinned artifacts and Vulkan assets:

```sh
rtk proxy uv run --locked --extra embedding-models --directory backend python -m researchlens.local_needs --download
rtk proxy uv run --locked --extra embedding-models --directory backend python -m researchlens.information_experiments measure --output ../evaluation/runs/information-needs-new
rtk proxy uv run --locked --extra embedding-models --directory backend python -m researchlens.information_experiments evaluate --output ../evaluation/runs/information-needs-new
rtk proxy uv run --locked --extra embedding-models --directory backend python -m researchlens.representation_experiments --output ../evaluation/runs/enriched-representations-new
```

The first command is the only explicit new-model download. Subsequent stages verify
their inputs and refuse to overwrite run directories. Source/input/model/prompt/schema
hashes and plans are recorded before searches. Frozen matrices with stale source or
dataset provenance fail. No automatic retries, paid API or hidden CPU substitution
are used. `--other-split` validates separation without executing held-out questions.

`FixedPoolSelector.search(question, limit)` replays the frozen measurement bundle,
so it intentionally rejects arbitrary questions absent from that bundle. Its
`information_settings` exposes strict provenance including `replay-selection-only`.
It is a diagnostic adapter, not a deployable end-to-end retriever. The pure
`select_indices` function can be reused with live scores in a later integration.
`LocalNeeds.extract(question)` validates and returns grounded query strings.
`RepresentedRetriever.search` encodes arbitrary questions locally against the
loaded enriched vectors. Both adapters preserve existing evaluator compatibility.

## Results and decision

None of the new configurations beats the existing BGE-M3/BGE20 candidate. Retain
`development-selected-vulkan-retrieval.json` unchanged. The 29/36 target required to
exceed 80% completeness was not reached; application defaults remain unchanged.

| Configuration | Complete evidence@4 /36 | Hit@4 /36 | Approved group coverage | MRR@4 | Both sources /9 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing BGE-M3 + BGE20 | 26 | 33 | 80.3% | 0.833 | 8 |
| Fixed Qwen dense order | 24 | 32 | 78.3% | 0.715 | 6 |
| Fixed Qwen pool + whole-question BGE40 | 25 | 33 | 79.4% | 0.833 | 8 |
| Fixed Qwen pool + rule queries, max rank | 25 | 33 | 79.4% | 0.757 | 8 |
| Fixed Qwen pool + local needs, max rank | 25 | 34 | 81.3% | 0.780 | 9 |
| Fixed Qwen pool + local needs, round-robin | 21 | 30 | 72.0% | 0.616 | 8 |
| Fixed Qwen pool + local needs, saturation | 19 | 29 | 68.6% | 0.736 | 9 |
| Qwen title/section vectors | 22 | 33 | 74.7% | 0.713 | 2 |
| Qwen title/section/neighbor vectors | 22 | 33 | 74.6% | 0.731 | 3 |

The local-needs maximum-rank selector improves partial group coverage and hits,
but does not improve completeness over whole-question reranking. Against the
existing best BGE20 configuration it has no complete-case gains and loses
`tech-compare-training-computers`. All six corrected fixed-pool policies finish
50 cases without errors or unstable repeat rankings. Dense replay matches every
saved prefix; whole-question reranking also reproduces the previous Qwen/BGE40
selected IDs. Every fixed policy has the same 34/36 candidate upper bound.

| Configuration | Terminology /14 | Paraphrase /13 | Cross-document /9 | Reference recall@4 |
| --- | ---: | ---: | ---: | ---: |
| Existing BGE-M3 + BGE20 | 11 | 8 | 7 | 71.7% |
| Fixed Qwen dense | 11 | 8 | 5 | 69.3% |
| Whole-question BGE40 | 11 | 8 | 6 | 71.7% |
| Rule-query max rank | 11 | 8 | 6 | 70.3% |
| Local-needs max rank | 11 | 8 | 6 | 71.4% |
| Local-needs round-robin | 10 | 7 | 4 | 58.2% |
| Local-needs saturation | 9 | 4 | 6 | 56.1% |
| Title/section vectors | 11 | 9 | 2 | 69.2% |
| Title/section/neighbor vectors | 11 | 9 | 2 | 65.3% |

Reference recall uses the original passage reference list. It is distinct from
approved evidence-group coverage and complete support. Representing both papers
for all nine comparisons does not prove that the right facts from both are present.
The saturation selector loses seven incumbent completions; round-robin loses five.
Their full selected IDs, metrics and queries are archived for each question.

The initial extraction run's three local-needs policies retain all 24 errors.
Counting failed questions as incomplete, their complete-evidence counts are 14/36
for maximum-rank, 11/36 for round-robin and 9/36 for saturation. They are failed
configurations, not competing quality candidates with errors dropped from the
denominator. The corrected grammar addresses output reliability but does not
establish semantic completeness of the extracted needs.

The enriched vectors also reduce aggregate candidate coverage:

| Representation | Complete evidence in top 20 /36 | In top 40 /36 | Final top four /36 |
| --- | ---: | ---: | ---: |
| Original Qwen passage text | 33 | 34 | 24 |
| Title/section | 30 | 32 | 22 |
| Title/section and neighbors | 30 | 33 | 22 |

Both enriched variants recover complete candidate support for
`tech-compare-localization-outputs` at 40, which the original representation missed,
but neither selects it in four. They introduce other candidate misses and still
miss `tech-changing-neighborhood` at 40. The neighbor variant gains
`tech-moving-signal-addition` and `tech-stripe-frequencies` against the incumbent
but loses six other completions. Title/section gains `tech-glass-paraphrase` and
`tech-stripe-frequencies` and also loses six. These are measured regressions;
there is no basis to adopt either representation wholesale.

## Timing, visibility and limits

The corrected extraction stage has a 652 ms median per question. Scoring the whole
question over 40 candidates has an 836 ms median in the staged measurements.
Summing extraction and the required original/subquery score times gives a median
of about 2,974 ms, excluding dense query encoding and replay selection. This is a
reconstruction from single staged measurements, not a controlled live-query
benchmark. Replay selection itself is about 0.14 to 0.21 ms and cannot be used as
the end-to-end timing. The new selectors therefore add substantial inference work
without increasing complete support over the incumbent.

Actual enriched-vector searches use one warmup and three timed repeats per question
at output limit four. Their medians/p95 are 185/246 ms for title/section and
176/230 ms for neighbors. Candidate-coverage searches request 40 separately, with
one attempt and no warmup. Timing changes relative to earlier dense controls do
not establish a representation-caused speedup; the query encoder conventions are
unchanged and the runs are not matched contemporaneous CPU timing controls.

All 204 enriched inputs are fully encoded: maximum 325 tokens for title/section and
493 for neighbors, under the unchanged 512-token limit. There is no observed
auxiliary or canonical-text truncation. The two extraction studies measure 5,320
and 7,680 BGE pairs respectively, maximum 413 tokens and zero pair truncation.
Truncation does not explain these regressions.

Corrected-run server private-memory peaks are 3.27 GiB for question extraction and
2.30 GiB for BGE reranking. These are separate native process high-water values,
not simultaneous totals or VRAM. The enriched-vector Python process reaches a
cumulative peak working set of 8.62 GiB after title/section and 8.98 GiB after
neighbors. All owned benchmark servers are stopped. API cost is zero.

The initial source snapshot is `e995879`; the schema-corrected snapshot is `aed7f3e`.
Frozen inference manifests include individual runtime source hashes. Untracked
research notes and result documentation account for dirty worktree provenance;
runtime source matches those recorded snapshots. New offline tests cover copied
phrases, schema grounding, selection ties, canonical identity, explicit extraction
failures, neighbor document boundaries, visibility offset mapping and stale inputs.
Synthetic tests establish functionality, not scientific quality.

[Compact archived results](information-needs-results.json) contain plans, pins,
source/input hashes, staged score matrices, model outputs, per-question outcomes,
candidate IDs, cohorts, token summaries and memory counters. Recreate the archive:

```sh
rtk proxy uv run python docs/information-needs-results.py --studies evaluation/runs/information-needs-2026-10-02 evaluation/runs/information-needs-schema-v2-2026-10-02 evaluation/runs/enriched-representations-2026-10-02 --output docs/information-needs-results.json
```

Full runs, measured visibility sidecars, vectors, GGUF weights and server logs stay
ignored. The small correlated four-paper development set, conservative evidence
labels and extractive query formulation limit what this result establishes. The
study rejects these particular configurations; it does not prove that all query
decomposition or contextual embedding methods fail. No winner was selected from
held-out questions. Generated-answer correctness, citation support, semantic
decomposition review and abstention remain unmeasured. All negatives still receive
neighbors; no similarity or utility threshold proves answerability.
