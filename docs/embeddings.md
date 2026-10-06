# Local embeddings and hybrid retrieval

`RETRIEVAL_BACKEND=tfidf|embeddings|hybrid` selects retrieval independently of answer
generation. TF-IDF remains the default; `Retriever` is its compatibility alias. All
encoders run locally on CPU. Startup is cache-only; no vector database or embedding API
is used. Restart after changing configuration, corpus or artifacts.

## Pinned model catalog

| Alias | Upstream model | Pinned revision | License / languages | Dimensions / runtime |
| --- | --- | --- | --- | --- |
| `minilm` | [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41) | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` | Apache-2.0 / English | 384 / ONNX Runtime |
| `bge-m3` | [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3/tree/5617a9f61b028005a4858fdac845db406aefb181) | `5617a9f61b028005a4858fdac845db406aefb181` | MIT / multilingual, 100+ languages | 1024 / Torch + Transformers |
| `qwen3-0.6b` | [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/tree/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3) | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | Apache-2.0 / 100+ languages | 1024 / Torch + Transformers |
| `qwen3-4b` | [Qwen3-Embedding-4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B/tree/5cf2132abc99cad020ac570b19d031efec650f2b) | `5cf2132abc99cad020ac570b19d031efec650f2b` | Apache-2.0 / 100+ languages | 2560 / Torch + Transformers |

Licenses/language coverage are upstream claims, not corpus quality measurements. Model
files are allowlisted at these revisions; no `main` resolution or repository Python code
is used (`trust_remote_code=False`). BGE uses dense output only, without sparse/ColBERT heads.

## Install, ingest and start

MiniLM requires the smaller extra; BGE/Qwen require `embedding-models`, whose uv source
selects CPU PyTorch wheels. Keep the extras on subsequent `uv run`/`uv sync` commands.

```sh
rtk proxy uv sync --locked --extra embeddings --extra embedding-models --python 3.13
rtk proxy uv run --extra embedding-models --directory backend python -m researchlens.ingest --corpus technical --retrieval embeddings --embedding-model bge-m3
```

Configure `.env` without changing an existing API key:

```dotenv
ANSWER_PROVIDER=local
RETRIEVAL_BACKEND=hybrid
EMBEDDING_MODEL=bge-m3
RETRIEVAL_INDEX=data/index.json
RETRIEVAL_CORPUS=data/technical/documents.json
```

```sh
rtk proxy uv run --extra embedding-models --directory backend uvicorn researchlens.api:app --host 127.0.0.1 --port 8000
```

Use `--extra embeddings`/`--embedding-model minilm` for MiniLM alone. CLI and application
defaults select the technical corpus. For fixtures, use `--corpus sample` and set the app's
`RETRIEVAL_CORPUS=data/sample_documents.json`. `CORPUS` and Python `build_index()` defaults
remain sample-compatible. TF-IDF uses any valid passage artifact without optional packages.
Ingestion reads retrieval configuration without constructing an answer provider.

Explicit ingestion flags override configuration: `--retrieval`, `--embedding-model`,
`--source`, `--destination`; `--corpus` selects a bundled source. Environment paths are
repository-relative. CLI paths are relative to the launch directory (`backend` with
`--directory backend`); use absolute paths for integrations.

The first ingestion downloads roughly 91 MB (MiniLM), 2.3 GB (BGE-M3), 1.2 GB (Qwen0.6B)
or 8 GB (Qwen4B), plus Python packages. BGE's pinned weights are `pytorch_model.bin`;
Qwen uses safetensors. Inference precision does not reduce download size. Downloads are
unauthenticated (`token=False`), never upload text and use the Hugging Face cache
(`HF_HOME`/`HF_HUB_CACHE` can relocate it). Windows without symlink privileges can use
extra disk space; administrator privileges are not needed. Startup uses only cached
files (`local_files_only=True`) and fails explicitly when files/dependencies are missing.
For offline deployment, carry the pinned cache, corpus, index and dependencies. Running
servers retain their loaded snapshot until restarted.

## Encoding contract

Documents encode `Passage.text` alone. IDs/titles/attribution are not prepended. Chunking
stays paragraph/180-word windows, with complete original text and all metadata preserved.
Stored vectors are normalized float32 arrays; exact cosine search is a dot product.

| Model | Query/document conventions | Pooling | Default token cap / batch / intra-op threads | Precision |
| --- | --- | --- | --- | --- |
| MiniLM | Raw text, no prefixes | Attention-masked mean, including non-padding special tokens | 256 / 32 / 2 | float32 |
| BGE-M3 | Raw text, no instructions | First/CLS token, normalized | 512 / 1 / 8 | bfloat16 |
| Qwen3, both sizes | Fixed query instruction; raw documents | Last non-padding token, normalized | 512 / 1 / 8 | bfloat16 |

Qwen's fixed query prefix is:

```text
Instruct: Given a research question, retrieve relevant passages that answer the question
Query: <question>
```

Tokenization pads/truncates on the right; Qwen uses the attention mask to exclude padding.
Decoder KV caching is disabled. All runtimes use one inter-operation thread. Ingestion
accepts `--max-tokens`, `--batch-size`, `--threads` and Torch `--precision float32|bfloat16`;
startup reuses saved settings. MiniLM stays float32. CPU bfloat16 speed depends on CPU
features and is measured separately. There is no quantization or GPU allocation.

Upstream limits are 256 for MiniLM, 8192 for BGE-M3 and 32768 for the Qwen adapters. The
smaller Torch default bounds CPU work while preserving existing passage boundaries.
**180 words can exceed a token cap**, especially with technical notation; such vectors
represent only the prefix. Stored/returned passage text remains complete. Instructions
also count toward Qwen's query cap; the HTTP 2000-character limit remains unchanged.
Token-aware rechunking is a separate experiment because it changes citation boundaries.

## Artifacts and compatibility

Ingestion atomically publishes one schema-2 JSON with raw-corpus SHA-256, chunking, full
passages, model/revision and encoding/runtime settings, ordered passage IDs, vectors and
their little-endian float32 checksum. JSON on disk and a matrix in memory suffice here.
Generated comparison indexes live in ignored `evaluation/runs/`; keep other custom indexes
out of Git. No weights or credentials are committed.

Retrieval and evaluation share `artifacts.load_artifact`. It validates vector dimensions,
finite/nonzero values, normalization, checksum and row identity. With `source=...`, it
checks corpus bytes and reconstructed text/attribution/section/XML metadata. The retriever
additionally checks the allowlisted revision, exact encoding and installed runtime before
loading weights; the application explicitly supplies its configured source/model.
Unsupported/stale/corrupt artifacts fail with rebuild instructions. Re-ingest using the
matching corpus/model/settings, then restart; do not relabel metadata to bypass checks.
Checksums detect corruption, not malicious tampering. Schema 1 stays usable by TF-IDF.
Old incomplete embedding contracts and changed recorded runtime versions require rebuilding.

## Hybrid and runner integration

Hybrid combines up to 20 positive-score lexical candidates and 20 dense neighbors with
reciprocal rank fusion: sum `1 / (60 + rank)`, using one-based ranks. It deduplicates by
stable passage ID; exact ties use artifact order. Raw similarity scores are not added.
The final limit defaults to four. Optional static weights, a pinned local cross-encoder
and redundancy selection are documented in [retrieval experiments](retrieval-improvements.md).
They are disabled by default; no relevance threshold or learned weighting is implemented.
Unrelated questions can still have dense/hybrid neighbors and reach
the paid answer provider. Scores never prove answerability; existing prompt/context
limits and provider abstention remain intact. Local preview does not judge support.

```python
from pathlib import Path
from researchlens.retrieval import load_retriever

retriever = load_retriever(
    "hybrid", Path("data/index.json"), source=Path("data/technical/documents.json")
)
hits = retriever.search(question, limit=4)
```

Run with `backend` on `PYTHONPATH` or inside that directory. Model/index loading happens
once; dense search encodes only the question. Optional reranking encodes question/passage
pairs for its fixed candidate pool. Evaluation derives settings from the artifact
independently of `.env`; app startup also verifies `EMBEDDING_MODEL`. `source` is optional
for legacy callers; supply it for corpus validation. Citation identities remain unchanged.

The new evaluator accepts an optional `get_encoding_diagnostics()` hook or
`--encoding-diagnostics` sidecar for measured token counts and retained text ranges.
Embedding adapters now publish this hook using the actual loaded tokenizers, including
special-token counts and retained canonical-text character ranges. Hybrid and reranked
adapters delegate the same cached measurements. Artifact/encoding/text hashes bind the
measurements to the saved vectors. Full-passage scoring and encoder visibility remain
separate measures; a correctly retrieved passage can contain evidence beyond its encoded prefix.
Provider-context selection/truncation preview is measured separately without API calls.

The existing evaluation CLI consumes full schema-2 artifacts directly. Hybrid defaults
are recorded in `RetrievalConfig`; explicit `--retrieval-config` candidate counts/RRF k
and static weights are passed to the actual adapter. A nested allowlisted reranker
configuration records its pin, runtime, candidate pool and optional diversity penalty.
Only RRF is implemented for fusion. Tune settings on reviewed
development questions and freeze before held-out comparisons. See
[CPU model comparison](model-comparison.md) for measured diagnostics and remaining limits.
Use [current comparison commands](retrieval-readiness.md) to pass the approved evidence
labels and ranking cutoffs. Changing labels or approval provenance requires fresh runs
for every compared configuration. `--limit 4` measures application retrieval; use a
separate `--limit 10 --cutoffs 1 4 10` run for ranking prefixes. The comparison helper
records label identity/review status and saves `paired.json` against TF-IDF alongside
the existing runner's `comparison.md`.
