# Local embedding retrieval

TF-IDF remains the default and an explicitly selectable baseline. `RETRIEVAL_BACKEND`
accepts `tfidf` or `embeddings`, independently of `ANSWER_PROVIDER`. No paid embedding
service or automatic fallback is used. Restart the backend after configuration changes.

## Model and encoding contract

- Model: [`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41).
- Pinned revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Code never resolves `main`.
- License: Apache-2.0; language: English, per the
  [pinned model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/blob/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/README.md).
  Multilingual retrieval is not supported or evaluated by this integration.
- Small six-layer MiniLM encoder, 384-dimensional vectors. We use the repository's
  float32 `onnx/model.onnx` and `tokenizer.json`, not a quantized variant. ONNX Runtime's
  `CPUExecutionProvider` uses two intra-operation threads; batches contain at most 32 texts.
  This avoids the PyTorch dependency and runs on Windows x64/Python 3.13.
- Queries and documents use the **same encoding**: raw text, no instruction or prefix,
  the model's uncased WordPiece tokenizer, attention-mask mean pooling (including
  non-padding special tokens), then L2 normalization. Documents encode only `Passage.text`,
  without titles, IDs or source metadata. Similarity is the dot product of unit vectors.
- Both inputs truncate on the right to 256 tokens including special tokens, following
  the model's [sentence configuration](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/blob/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/sentence_bert_config.json).
  The existing paragraph/180-word chunks and IDs are unchanged. **180 words can exceed
  256 WordPieces**, particularly with technical terms; such a passage's vector represents
  only its prefix. The stored and returned text remains complete. Long questions can also
  be truncated for retrieval; the HTTP 2,000-character question limit is unchanged.
  Token-aware rechunking would change citation boundaries and needs separate evaluation.

## Install, ingest and start

From the repository root (Windows can replace `uv` with `py -m uv`):

```sh
rtk proxy uv sync --locked --extra embeddings --python 3.13
rtk proxy uv run --extra embeddings --directory backend python -m researchlens.ingest --retrieval embeddings
rtk proxy uv run --extra embeddings --directory backend uvicorn researchlens.api:app --host 127.0.0.1 --port 8000
```

Before starting, set these in `.env` without changing an existing API key:

```dotenv
ANSWER_PROVIDER=local
RETRIEVAL_BACKEND=embeddings
RETRIEVAL_INDEX=data/index.json
RETRIEVAL_CORPUS=data/sample_documents.json
```

The first ingestion needs network access to Hugging Face and its download hosts for
roughly 91 MB of model/tokenizer files, in addition to the Python dependencies. Files
are cached through `huggingface_hub` (normally under `~/.cache/huggingface/hub`;
`HF_HOME`/`HF_HUB_CACHE` can relocate them). Downloads are unauthenticated, require no
Hugging Face token, and do not upload passages or questions. No model files are committed.
Windows without symlink privileges may report a harmless cache warning and use extra
disk space; administrator privileges are not required. Python dependencies are locked
in `uv.lock`; retain `--extra embeddings` on `uv run`/`uv sync` to keep them installed.

Ingestion reads only retrieval configuration and does not instantiate an answer provider.
Startup uses `local_files_only=True`: a missing cache fails with an ingestion command,
never a hidden network download. For offline deployment, ingest once while online and
carry the pinned cache files, corpus and index to the target machine. A running server
keeps its snapshot until restarted; it does not watch files or reload per request.

Run ingestion without `--retrieval` to use `RETRIEVAL_BACKEND`. Explicit CLI flags override
retrieval settings. Environment paths are resolved relative to the repository root;
CLI `--source` and `--destination` paths are relative to the command's working directory
(`backend` when using `--directory backend`). For custom corpora, configure both
`RETRIEVAL_CORPUS` and `RETRIEVAL_INDEX` or provide absolute CLI paths. Keep generated
custom artifacts out of Git; only `data/index.json` is ignored by default.

`RETRIEVAL_BACKEND=tfidf` selects lexical retrieval without optional dependencies or model
downloads. A schema-2 embedding artifact also works for TF-IDF. A TF-IDF-only artifact
must be rebuilt before selecting embeddings. Existing schema-1 artifacts remain readable
by TF-IDF when their source hash and passages match the configured corpus.

## Artifact validation and lifecycle

Ingestion writes one JSON artifact atomically, after all vectors have been computed.
It contains schema version 2, SHA-256 of raw corpus bytes, chunking method/max words,
unchanged complete passage metadata, and (in embedding mode) encoding/model/revision
metadata, ordered passage IDs, vectors and a SHA-256 of little-endian float32 vector bytes.
This single file avoids partially updated vector/metadata pairs. JSON is deliberate for
this tiny corpus; vectors are loaded into one float32 matrix in memory, with exact search.

Startup verifies the corpus hash, chunking contract and reconstructed passage records.
Embedding startup also checks the exact encoding contract, row identities/order, count,
384-dimensional finite unit vectors and vector checksum before loading the model.
Checksums detect accidental corruption; they are not signatures for untrusted artifacts.
Changed source bytes (even whitespace), changed model/encoding, unsupported schemas,
missing vectors or corrupt records fail with an actionable rebuild error. Re-run ingestion
with the same configured corpus/index and desired backend, then restart. Do not hand-edit
metadata to bypass the checks. Model/encoding changes require rebuilding all vectors.

## Integration interface for the evaluation thread

```python
from pathlib import Path
from researchlens.retrieval import PassageRetriever, load_retriever

retriever: PassageRetriever = load_retriever(
    "embeddings",  # or "tfidf"; use the same embedding artifact for both
    Path("data/index.json"),
    source=Path("data/sample_documents.json"),
)
hits = retriever.search(question, limit=4)
```

Run from the repository root with `backend` on `PYTHONPATH`, or import from a runner
already configured that way. Explicit `source` is required for a custom corpus; the
default is the bundled corpus. Each retriever instance loads once and reuses its index;
each embedding search encodes only the question. `SearchHit` fields and citation identities
are unchanged. `Retriever(passages)` and `Retriever.from_path(path, source=...)` remain
aliases for the lexical baseline, preserving existing `Retriever.search(question, limit)`
callers. Do not use the alias when intending to select embeddings.

Both implementations rank descending; exact score ties use artifact order. `limit` defaults
to four, must be positive and is capped by corpus size. Blank questions return no hits.
TF-IDF returns only positive word-overlap scores. Embeddings return up to `limit` neighbors
even for zero or negative cosine scores. Scores across modes are not calibrated or directly
comparable. There is **no relevance threshold**, reranking or document-diversity heuristic.
Any subsequent tuning must use reviewed development questions, never held-out questions.

The HTTP answer schema, generation prompt/settings, four-passage/3,000-character per
passage/16,000 serialized-character context limits, and provider abstention checks are
unchanged. The local preview does not generate answers or judge support. With embeddings,
an unrelated query can still reach the OpenAI provider and incur cost; nearest neighbors
alone never establish evidence sufficiency. Actual abstention quality is pending evaluation.

Record artifact hash, corpus hash, chunking/encoding metadata, backend, `limit` and any
future threshold alongside results. No evaluation datasets or competing runner are added
here. See [implementation measurements and pending comparisons](retrieval-checks.md).
