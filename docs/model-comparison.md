# CPU retrieval diagnostics, 2026-10-01

Historical preliminary comparison on the original 12 draft questions. The current
evaluation has 50 approved development questions and separately approved evidence
groups with a new scoring contract. Do not compare these old scores with new runs.
See [current integration and readiness checks](retrieval-readiness.md) for the updated
commands and limitations. The four-model comparison below has not yet been rerun
on the new questions and labels.

Four pinned local embedding models and their TF-IDF hybrids completed the existing
evaluation runner on the same technical passages and development questions. TF-IDF
remains the default. These are **unreviewed draft diagnostics**, not evidence of model
superiority or improved answers. No settings were tuned, no held-out questions ran,
and no answer generation or OpenAI calls occurred (API cost: $0).

## Reproduce and inspect

From the repository root, with Python 3.13 and the committed lockfile:

```sh
rtk proxy uv sync --locked --extra embeddings --extra embedding-models --python 3.13
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.compare_retrieval --output ../evaluation/runs/cpu-comparison
```

Choose a fresh output directory. The command delegates ingestion and every run/report
to the existing modules, each in a fresh child process. It adds no separate scoring
framework and refuses a held-out dataset as its comparison input. The other split is
read only to validate split separation. Failed stages are recorded without automatic
retries or child output. The default timeout is one hour per stage.

The first run produced ignored local `evaluation/runs/cpu-models-2026-10-01/` indexes,
runs, manifest and comparison report. A sequential cached rerun produced
`evaluation/runs/cpu-models-final-2026-10-01/`; the tables below use that rerun's query
and process measurements. To repeat a cached run through the existing CLI:

```sh
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.evaluation run --dataset ../evaluation/datasets/technical-development.json --other-split ../evaluation/datasets/held-out.json --source ../data/technical/documents.json --index ../evaluation/runs/cpu-comparison/indexes/bge-m3.json --retriever hybrid --output ../evaluation/runs/bge-cached-check --limit 4 --repeats 5 --warmups 1 --measure-memory
```

[Archived result excerpts](model-comparison-results.json) contain run IDs, file hashes,
corpus/artifact identity, runtime and retrieval settings, runner summaries, and each
case's retrieved IDs, ranks and recalls. Full local outputs and vectors stay ignored;
model weights stay in the Hugging Face cache. Dataset files were not edited.

The cached runs used implementation commit
`19b416f6aaf13885cec36d67cf12e9054c91adf7`. Their recorded dirty flag is true because
documentation edits and unrelated untracked `.serena/` existed; executable code and
the lockfile matched that commit. The subsequent code change only clarifies error
messages for rebuilding invalid artifacts. Rankings and retrieval configurations
matched the first run exactly for all nine modes. This is an archived development
measurement, not a reviewed clean-worktree benchmark release.

## Fixed inputs and settings

- Four CC BY 4.0 technical papers; 204 passages. Attribution, section/XML locations,
  IDs and paragraph/180-word chunking are identical across modes.
- `technical-development`, version `1-draft`: 12 AI-authored, unreviewed cases;
  four exact-terminology, four paraphrase, two cross-document, one unrelated and one
  missing-evidence question. Ten answerable cases contribute relevance scores.
- Dataset SHA-256: `77b5060e0c74639357beb534c596cef530fd9cfda134243abde560fca978c56a`.
  Corpus: `cda1b161618373b9c7b9701d3326fda4707f9501bbc3bf29c802d9a000908bce`.
  Shared passage identity: `c7bf2f1f6b9c866573669f946866b5b0635ae4afcee1d06511e3109ab47c1157`.
- Final k=4. Hybrid uses 20 lexical and 20 dense candidates, RRF k=60 and artifact
  order for exact ties. No threshold, reranker, diversity policy or tuned weighting.
- Five timed repeats and one warmup **per question**: 60 timed searches per mode,
  540 across nine modes. Zero errors and zero unstable rankings across repeats.
- AMD Ryzen 7 9800X3D (8 cores/16 threads), 32 GiB RAM; Windows AMD64/Python 3.13.14.
  The RX 6800's 16 GiB VRAM was unused. Every encoder ran on CPU.
- MiniLM: ONNX Runtime 1.30.0, float32, 256-token cap, batch 32, two intra-op threads.
  BGE/Qwen: Torch 2.14.1+cpu, Transformers 5.18.0, bfloat16, 512-token cap,
  batch 1, eight intra-op threads. All use one inter-op thread and no quantization.
  See [encoding contracts and pinned revisions](embeddings.md).

Precision, token caps and pooling differ by adapter. This compares these concrete
configurations, not isolated model architecture or maximum upstream capabilities.

## Observed draft relevance

Source recall counts expected documents appearing anywhere in the top four. Passage
recall counts the draft's expected evidence IDs. MRR uses the first expected passage
rank, with misses contributing zero. Cross coverage counts questions with both
expected documents present; it does not establish that the retrieved text answers
both parts. High source recall can coexist with poor evidence ranking.

| Configuration | Source recall@4 | Passage recall@4 | MRR@4 | Cross coverage |
| --- | ---: | ---: | ---: | ---: |
| TF-IDF | 1.00 | 0.30 | 0.1583 | 2/2 |
| MiniLM dense | 0.95 | 0.30 | 0.0833 | 1/2 |
| MiniLM hybrid | 0.90 | 0.35 | 0.2833 | 0/2 |
| BGE-M3 dense | 1.00 | 0.35 | 0.4000 | 2/2 |
| BGE-M3 hybrid | 0.95 | 0.55 | 0.2583 | 1/2 |
| Qwen3-0.6B dense | 0.95 | 0.50 | 0.2333 | 1/2 |
| Qwen3-0.6B hybrid | 0.95 | 0.50 | 0.2917 | 1/2 |
| Qwen3-4B dense | 1.00 | 0.65 | 0.4167 | 2/2 |
| Qwen3-4B hybrid | 1.00 | 0.50 | 0.4333 | 2/2 |

The four exact and four paraphrase cases have the following expected-passage MRR:

| Configuration | Exact terminology | Paraphrases |
| --- | ---: | ---: |
| TF-IDF | 0.3125 | 0.0833 |
| MiniLM dense | 0.0625 | 0.1458 |
| MiniLM hybrid | 0.2083 | 0.2500 |
| BGE-M3 dense | 0.2500 | 0.5000 |
| BGE-M3 hybrid | 0.2708 | 0.2500 |
| Qwen3-0.6B dense | 0.2708 | 0.3125 |
| Qwen3-0.6B hybrid | 0.4167 | 0.3125 |
| Qwen3-4B dense | 0.3333 | 0.4583 |
| Qwen3-4B hybrid | 0.3333 | 0.5000 |

Specific regressions make a universal hybrid recommendation premature:

- MiniLM dense has lower overall draft MRR than TF-IDF; MiniLM hybrid retrieves
  only one expected document on both comparison questions.
- On `tech-glass-paraphrase`, BGE dense finds expected evidence at rank 1; hybrid
  moves it to rank 2. BGE hybrid loses one source on `tech-compare-fusion`, whereas
  BGE dense covers both sources.
- On `tech-autoencoder-exact`, Qwen3-4B dense finds expected evidence at rank 2;
  hybrid misses it within four. Qwen3-4B hybrid's aggregate MRR is slightly higher
  while its passage recall is lower; these metrics expose different tradeoffs.
- Every dense/hybrid mode returns four neighbors for `tech-unrelated`; TF-IDF
  returns none. Every mode returns passages for the absent shared CPU-cost question.
  Neither outcome establishes answerability. No generated abstention was tested.

Draft expectations may omit alternative relevant passages. Human source review is
required before treating these ranks as a research-quality comparison.

## Observed CPU resources

Query medians pool the 60 timed searches and exclude warmups, imports and index/model
setup. Setup below is the CLI's artifact/model loading interval, not complete server
startup. Peak RSS is a fresh process's **lifetime high-water mark**, not vector size,
current memory or incremental model memory. OS caches and scheduling affect timing;
small differences between dense and hybrid do not establish a speed advantage.

| Configuration | Query median, ms | Index/model load, s | Peak RSS, GiB |
| --- | ---: | ---: | ---: |
| TF-IDF | 0.46 | 0.028 | 0.145 |
| MiniLM dense | 1.75 | 0.594 | 0.308 |
| MiniLM hybrid | 2.62 | 0.287 | 0.308 |
| BGE-M3 dense | 24.36 | 12.632 | 3.900 |
| BGE-M3 hybrid | 22.76 | 5.320 | 3.900 |
| Qwen3-0.6B dense | 42.89 | 5.372 | 1.651 |
| Qwen3-0.6B hybrid | 43.58 | 4.327 | 1.652 |
| Qwen3-4B dense | 201.42 | 10.998 | 8.123 |
| Qwen3-4B hybrid | 202.95 | 6.872 | 8.078 |

Initial ingestion wall times were TF-IDF 0.149 s, MiniLM 4.810 s, BGE-M3 90.083 s,
Qwen3-0.6B 68.315 s and Qwen3-4B 331.835 s. These include process setup and first
downloads; some development checks ran concurrently. They are **not pure encoding
benchmarks**. The cached rerun reused those vectors and made no model downloads.

Qwen3-4B fits this machine and completes a warmed query in roughly 0.2 seconds in
this configuration. That establishes local feasibility for this small corpus, not
production throughput or better answer quality. CPU/GPU, float32/bfloat16 and
concurrency comparisons remain separate experiments.

## Remaining evaluation work

Human review of the development questions, expected evidence and alternative valid
passages is pending. Once reviewed, tune candidate counts/token caps or a relevance
policy on development only, freeze all settings, and then run a separately reviewed
held-out set. No relevance threshold was calibrated here; nearest-neighbor similarity
cannot prove support. Token truncation and the partial prose extraction also require
review against full original sources.

Answer correctness, citation support and abstention quality remain pending. The
answer API, prompt/settings and context/question limits are unchanged, and local
preview remains available. Retrieval comparisons need no paid calls. Any later
authorized live comparison must keep generation fixed across modes and use only
gpt-6-luna with medium reasoning, bounded output, zero retries and a dated cost
estimate before running, as required by the existing evaluation workflow.
