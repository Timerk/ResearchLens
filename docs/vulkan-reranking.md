# Vulkan reranker development tests

This optional evaluation adapter runs BGE-reranker-v2-m3 and Qwen3-Reranker-0.6B
locally on the Windows RX 6800 using llama.cpp Vulkan. It is separate from application
startup configuration. TF-IDF remains the default; answer prompts, context limits,
corpus metadata and passage identities are unchanged. No answer generation is used.

## Pinned assets and scoring

- Runtime: llama.cpp `b11327`, commit `552f18f912a32ea86edf82e2b76431cb7131538d`.
  Official Windows Vulkan archive SHA-256:
  `89d1308941d5a86182395a07f57286da3898a9530246e8f755c26ec71267d4a2`.
- BGE: `BAAI/bge-reranker-v2-m3`, revision
  `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, Apache-2.0, multilingual.
  Query/document pair tokens; raw sequence-classifier logits, not vector similarity.
- Qwen: `Qwen/Qwen3-Reranker-0.6B`, revision
  `e61197ed45024b0ed8a2d74b80b4d909f1255473`, Apache-2.0, multilingual.
  The upstream rerank template uses its default web-search instruction and the prescribed
  system/user/assistant suffix. Conversion extracts the yes/no classifier head.
  Scores are two-class softmax values, not calibrated answerability probabilities.
- Both use locally converted F16 GGUF weights without integer quantization.
  BGE GGUF is 1,159,775,008 bytes; Qwen GGUF is 1,197,634,304 bytes.
  Original downloads, GGUFs and runtime files require several GB of disk space.
  Sources: [BGE card](https://huggingface.co/BAAI/bge-reranker-v2-m3),
  [Qwen card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B), and
  [pinned runtime source](https://github.com/ggml-org/llama.cpp/tree/552f18f912a32ea86edf82e2b76431cb7131538d).

## Reproduce

From the repository root with the existing CPU embedding extras installed:

```powershell
rtk proxy uv sync --locked --extra embeddings --extra embedding-models --python 3.13
rtk proxy uv pip install --python .venv/Scripts/python.exe --target .venv/vulkan/convert-deps sentencepiece==0.2.1
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.vulkan_prepare --runtime ../.venv/vulkan
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.vulkan_experiments --runtime ../.venv/vulkan --indexes ../evaluation/runs/approved-models-2026-10-01-k4/indexes --output ../evaluation/runs/vulkan-rerankers-cache-off-2026-10-02
```

Preparation explicitly downloads public assets at pinned revisions. Startup/scoring
are cache-only. Conversion uses the pinned upstream source with the project's Torch
and Transformers versions, plus isolated SentencePiece. No global Python or driver
installation is required. Generate the existing CPU artifacts with the documented
CPU comparison helper if they are absent; do not substitute a different corpus.

The adapter owns a hidden loopback-only server and closes it after each run. It checks
the executable hash and startup logs for RX 6800 selection and expected layer offload.
Its HTTP client ignores proxy environment variables and follows no redirects.
Inference errors fail explicitly without retries or CPU substitution. Reserved upstream
template placeholders are rejected. At most the last question's token diagnostics
are cached; inference results are never cached for timing.

The runtime uses Vulkan0, 99 requested GPU layers, 2,048 context/batch/microbatch tokens,
four slots, and eight CPU threads. Each pair must fit within 511 tokens; overflow fails
instead of silently clipping evidence. Measured pair-token totals must match the runtime's
reported evaluated tokens. Each run records executable/weight hashes, revision, scoring
and prompt conventions. GPU layer offload does not imply every tensor or operation is
on GPU; token embeddings can remain CPU-mapped.

The adapter explicitly disables the idle prompt cache with `--cache-ram 0`. In this
runtime the default 8 GiB host cache stores reranking state but restores state only
for completion tasks. Distinct requests therefore fill a cache that reranking cannot
use. See [the source diagnosis](amd-gpu-research.md#follow-up-reranker-host-memory-growth).
Native Windows server counters are sampled at startup and before/after each request;
`server-memory.json` records working set, private memory and their native high-water
counters separately from Python and VRAM. A 6 GiB server private-memory high-water
limit stops the owned server with an actionable error. It is a per-server check,
not a total-system or continuous memory guarantee.

A 12-request reproduction using the first approved development cases and the saved
20 Qwen3-4B candidates reproduced the RAM increase. After two requests, the default
cache grew by 3.93 GiB and ended at about 7.83 GiB private memory. With the fixed
adapter, private memory stayed between 3.36 and 3.60 GiB after the first request,
ending at 3.60 GiB; working set ended at 2.01 GiB. This check ran the actual adapter
without injected flags. The full comparison repeats changing questions and records
memory for every GPU configuration. Earlier interrupted timings are excluded because
system RAM reached 96%.

## Development protocol

The complete ten-configuration plan is recorded before queries: Qwen3-4B and BGE-M3
dense controls, and both rerankers over 20/40 dense candidates from each model. Every
configuration runs in a fresh process, with the same approved 50 development questions
and reviewed evidence groups, actual output limit four, cutoffs one/four, one warmup
and three timed repeats. Existing vectors are reused unchanged. Held-out is read only
for split validation, never searched. The existing runner, evidence scorer, review
template and paired report implement evaluation; no alternative scoring framework
is introduced.

Selection considers complete evidence at four, cohort regressions and latency. CPU
query encoding remains included in reported retrieval latency. Reranker server loading
is part of setup, excluded from timed searches. The runner's process peak RSS covers
the Python process, not the separate server or total VRAM. Runtime GPU buffer sizes
must be reported separately and must not be called measured peak VRAM.

Three synthetic relevance pairs passed both Vulkan adapters and
kept the Transformers float32 ordering. Maximum score differences were 0.099643 raw
BGE logits and 0.00001520 Qwen softmax values. These establish a smoke check, not corpus
quality or full numerical/ranking equivalence.


## Completed development comparison

The owner paused the comparison for machine shutdown after nine configurations on
2026-10-02, then authorized resuming. All ten configurations now completed all 50
approved development cases, with zero errors and stable rankings across repeats.
The interrupted attempt is retained but not scored. The final configuration ran in
`evaluation/runs/vulkan-rerankers-resume-2026-10-02/`; the preceding nine remain in
`evaluation/runs/vulkan-rerankers-cache-off-2026-10-02/`. The existing runner produced
the combined comparison and paired report. No datasets or evidence labels changed.

There are 1,500 timed searches plus 500 warmups. These timings include CPU query
encoding and GPU reranking, with actual output limit four. They exclude loading.

| CPU embedding model | Retrieval | Complete evidence / 36 | Median | p95 |
| --- | --- | ---: | ---: | ---: |
| Qwen3-4B | Dense | 24 | 218 ms | 265 ms |
| BGE-M3 | Dense | 22 | 26 ms | 30 ms |
| Qwen3-4B | BGE reranker, 20 candidates | 25 | 626 ms | 853 ms |
| Qwen3-4B | BGE reranker, 40 candidates | 25 | 1,024 ms | 1,269 ms |
| Qwen3-4B | Qwen reranker, 20 candidates | 25 | 1,580 ms | 1,848 ms |
| Qwen3-4B | Qwen reranker, 40 candidates | 23 | 2,915 ms | 3,190 ms |
| BGE-M3 | BGE reranker, 20 candidates | 26 | 481 ms | 675 ms |
| BGE-M3 | BGE reranker, 40 candidates | 25 | 939 ms | 1,192 ms |
| BGE-M3 | Qwen reranker, 20 candidates | 23 | 1,452 ms | 1,647 ms |
| BGE-M3 | Qwen reranker, 40 candidates | 23 | 2,873 ms | 3,149 ms |

Selected metrics, hashes, cohorts, question regressions and memory summaries are in
[vulkan-reranking-results.json](vulkan-reranking-results.json). The existing runner's
paired diagnostics for the selected candidate against both dense controls are archived
in [vulkan-reranking-paired.json](vulkan-reranking-paired.json). Full generated runs,
logs and weights remain ignored. Historical draft-question scores are not comparable
to this approved-evidence study.

### Development selection and regressions

BGE-M3 plus BGE reranking over 20 candidates has the highest complete-evidence count,
26/36, or 72.2%. Its mean group coverage is 80.3%; group coverage and complete-evidence
rate are different metrics. The complete-evidence result remains below the provisional
80% goal. Qwen3-4B dense reaches 24/36, or 66.7%, with lower latency.

| Configuration | Terminology / 14 | Paraphrase / 13 | Cross-document / 9 |
| --- | ---: | ---: | ---: |
| Qwen3-4B dense | 11 | 8 | 5 |
| BGE-M3 dense | 10 | 8 | 4 |
| BGE-M3 + BGE rerank-20 | 11 | 8 | 7 |

Against Qwen3-4B dense, the selected candidate gains `tech-amff-layers`,
`tech-compare-network-inputs` and `tech-compare-network-roles`, but loses
`tech-stripe-frequencies`. Equal cohort totals do not mean identical successful questions.
Increasing the pool to 40 regressed the BGE-M3/BGE and Qwen3-4B/Qwen configurations.
No additional weights, thresholds or candidate counts were tuned after these results.

The experimental Vulkan candidate is frozen in
[development-selected-vulkan-retrieval.json](development-selected-vulkan-retrieval.json)
before any held-out retrieval. Application defaults and the prior CPU selection remain
unchanged. This small development comparison does not establish generalization or
statistical superiority. All 14 negative questions still return neighbors; answerability,
generated answers, citation support and provider abstention were not evaluated. No
OpenAI calls or paid API cost occurred. The Vulkan adapter remains evaluation-only.

### Memory, truncation and reference checks

Across the eight GPU configurations, measured native server private-memory peaks are
2.12 to 2.20 GiB for BGE and 3.60 to 3.61 GiB for Qwen. Peak server working sets are
2.00 to 2.08 GiB and 2.01 to 2.03 GiB respectively. These exclude the separate Python
encoder and are not peak VRAM. Runtime-reported Vulkan buffers total 635.24 MiB for
BGE and 2,651.44 MiB for Qwen, also not measured peak VRAM. The cache-off reruns match
all 50 prior rankings and metrics in each of the five earlier completed configurations.

All 12,000 recorded question/candidate pairs fit the budget with zero truncation.
Maximum pair lengths are 366 BGE tokens and 382 Qwen tokens, below the 511-token cap.
Every GPU run confirmed the RX 6800 and expected layer offload in its startup log.

The CPU float32 reference check selects the first development question in each of
five query-style cohorts, independent of outcomes, and scores the same 20 candidates
per question. All 100 pair-token counts per model match. BGE's top-four order and set
match on 5/5 questions. Qwen's set matches on 5/5; its order matches on 4/5, with
positions three/four swapped on `tech-unrelated`. Maximum absolute score differences
on the 20 returned pairs per model are 0.062778 BGE raw logits and 0.021175 Qwen softmax.
These scores are not calibrated answerability probabilities. This subset does not
prove full numerical or ranking equivalence across backends.

Reference records are in [vulkan-reference-results.json](vulkan-reference-results.json).
To reproduce from the repository root after the GPU grid, run:

```powershell
rtk proxy .venv/Scripts/python.exe docs/vulkan-reference-check.py
```

The reference uses cached original pinned models, float32, SDPA, eight CPU threads,
one inter-op thread and batches of four. Its single-sample timings have no dedicated
warmup and exclude CPU embedding searches. They are diagnostic measurements and do
not establish a controlled CPU/GPU speedup against the end-to-end table.

To reproduce the resumed final configuration separately, use a fresh output directory:

```powershell
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.vulkan_experiments --single bge-m3-qwen-rerank40 --runtime ../.venv/vulkan --indexes ../evaluation/runs/approved-models-2026-10-01-k4/indexes --output ../evaluation/runs/vulkan-rerankers-resume-new
```
