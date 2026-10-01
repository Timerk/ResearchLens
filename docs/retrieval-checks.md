# Retrieval implementation checks — 2026-09-28

Historical MiniLM/synthetic diagnostics. The evaluation integration below has since
been replaced by direct schema-2 loading and multi-model CPU comparisons; see
[current model comparison](model-comparison.md). The temporary passage view is no
longer needed, and the old encoding metadata requires rebuilding before current startup.

These are AI-authored synthetic development diagnostics on three test documents, not
research-quality evaluation or evidence that embeddings improve answer quality. No
retrieval setting or threshold was tuned on these results. No held-out questions were
used. No OpenAI requests were made: generated answers, token usage and API cost were zero.
Human claim/support judgments and real-corpus comparisons remain pending.

## Local runtime and contract verification

- Windows 11 x64, Python 3.13.14; ONNX Runtime 1.30.0, tokenizers 0.23.2,
  huggingface-hub 1.33.0, NumPy 2.5.3. Dependencies are recorded in `uv.lock`.
- Pinned model downloaded successfully; ingestion wrote six 384-dimensional vectors.
  Cache-only startup and local FastAPI preview succeeded with the real encoder.
- 58 offline tests passed, including original answer-provider tests, invalid/stale
  artifacts, cosine ranking, identical passage metadata/IDs, encoder pooling and pinned
  cache loading, one-time startup, API limits, and mocked provider abstention with
  unrelated embedding neighbors. These tests do not assess semantic quality.
- Backend Ruff lint/format and Git whitespace checks passed. The existing upstream
  Starlette/httpx TestClient deprecation warning remains.
- The same 58 tests passed without the optional embedding packages installed;
  TF-IDF ingestion also succeeded in that environment. Angular production build passed
  after updating the notice to describe either retrieval mode accurately.
- Model/download failures never select a remote embedding API or silently switch modes.

## Five-question local smoke comparison

Same corpus and passage artifact, `limit=4`, no embedding threshold. Startup was outside
the query loop, which issued each question once in the order below. TF-IDF used its existing
English stop-word/unigram-bigram configuration and positive-score filter. Full question
strings are supplied for reproducibility; this is not an additional evaluation dataset.

| Question | TF-IDF observations | Embedding observations |
| --- | --- | --- |
| Does dust cause false positives? | Dark-field paragraph 2 first (0.270028); two hits | Same first (0.417805); four hits |
| Can contamination trigger erroneous alarms? | No hits | Learning paragraph 2 first (0.362363), bright-field second (0.192729), **dust/dark-field third** (0.184543) |
| What does dark-field illumination reveal? | Dark-field paragraph 2 first (0.257704) | Same first (0.679435) |
| How do bright-field and dark-field imaging compare? | Dark-field then bright-field paragraphs 2; both sources covered | Same first two; both sources covered, plus two neighbors |
| Who composed Beethoven symphonies? | No hits; preview `no_matches` | Four neighbors; preview `passages_found`; first is a synthetic-material disclaimer (0.063622), fourth has negative similarity (-0.036583) |

The actual IDs are `fixture-dark-field:p2:w0`, `fixture-bright-field:p2:w0` and
`fixture-learning:p2:w0`; disclaimers use `p1:w0`. Near-identical floating point scores
for duplicate disclaimer text can affect their order; exact ties use artifact order.

The paraphrase exposes a ranking weakness: the dust passage is present at k=4 but would
be missed at k=1. Embeddings also fill the context with less relevant neighbors. The
unrelated question demonstrates why nearest-neighbor scores cannot establish answerability.
Neither mode's coverage proves that a requested comparison exists: the fixture explicitly
does not report comparative detection accuracy. There is no threshold calibration here.

Single-process startup from disk/cache was 5.39 ms for TF-IDF and 220.29 ms for embeddings
(not a cold-download benchmark). Query median/max were 0.38/0.54 ms and 1.03/1.80 ms,
respectively, over five calls. These tiny samples are diagnostic only, not performance SLAs.
The JSON embedding artifact was 75,158 bytes. The local Windows corpus-byte hash was
`89cbffb663b8a92812e6a77b5f76683a7bb1d78cf3e9cd40dee98ea263ff7202`.

To reproduce the rankings, build the embedding artifact per [setup](embeddings.md),
load it with `load_retriever("tfidf", path)` and `load_retriever("embeddings", path)`,
then call `search(question, limit=4)` for each question above. Use local preview or call
retrievers directly; do not instantiate an OpenAI provider.

## Integration with the separate evaluation runner

[PR #8](https://github.com/Timerk/ResearchLens/pull/8) became available during this work.
Its runner, schema and datasets were read from commit
`2c4ed9881a19bbff4b469e482e13fadcad449d58` into an ignored scratch directory and left
unchanged. The three unreviewed development cases were run through its `run_evaluation`
function with each retriever at k=4, no answer provider, and no parameter tuning. Its
empty held-out placeholder was loaded only for `validate_splits`; no held-out cases ran.

| Runner diagnostic | TF-IDF | Embeddings |
| --- | --- | --- |
| Development cases / errors | 3 / 0 | 3 / 0 |
| Answerable cases scored | 2 | 2 |
| Mean source recall at 4 | 1.00 | 1.00 |
| Expected-passage recall on each answerable case | 1.00 | 1.00 |
| Full comparison-source coverage | 1/1 | 1/1 |
| Generated answers / human reviews | 0 / 0 | 0 / 0 |
| Median / maximum per-case latency | 0.435 / 0.561 ms | 1.623 / 2.010 ms |
| API calls / cost | 0 / $0 | 0 / $0 |

Both retrieved dark-field paragraph 2 first for `dev-dust` and `dev-compare-imaging`,
and bright-field paragraph 2 first for `dev-missing-size`. The missing-size case has
no recall score and provides no measured abstention result. Embeddings returned an
additional disclaimer passage for every case. These diagnostics demonstrate interface
compatibility, not superiority or answer quality. Runs used the working implementation
in this PR; they are not a frozen published baseline.

Identity recorded for this check:

- Canonical dataset SHA-256: `6bb9c4a4f9e882eea9382c4bd1c63f85d1207e90199e099761da580b73878488`.
- LF corpus SHA-256 from the evaluation branch: `220769f04b408f2475065106410261651051091a4afe827b8ee6e9b66f363c33`.
- Full embedding artifact byte SHA-256: `0278ac40d313a78f1d12d5c5f85f7124dddeb2ebc60282beaf8f9c7d006872a7`.
- Canonical passage-only view SHA-256: `6cabfb173a8894a1f4a2b32d3249871a1bcddd43deaa9b7729e0ebcef148ff9b`.

The two corpus hashes differ because PR #8 enforces LF, while this Windows checkout
started with CRLF. Passage text and citation identities are unchanged. The integration
check ingested PR #8's exact LF bytes separately, without editing either branch's data.

### Remaining runner integration limitation

At the pinned PR #8 commit, `validate_artifact` accepts only schema 1. This PR emits
schema 2 with optional vectors, so the evaluation CLI cannot directly consume the new
artifact until the runner accepts schema 2. We did **not** modify the runner or relabel
the on-disk index. The check first loaded/validated the full schema-2 artifact with
`load_retriever`, then provided a legacy passage-only view to the injected Python API:

```python
full = json.loads(index_path.read_bytes())
retriever = load_retriever("embeddings", index_path, source=corpus_path)
passage_view = {
    "schema_version": 1,
    **{key: full[key] for key in ("source_sha256", "chunking", "passages")},
}
# Use the identical passage_view for both modes. Keep model/revision, normalization,
# limit and score threshold in RetrievalConfig. Record the full vector artifact too:
config = RetrievalConfig(
    implementation="researchlens.retrieval.EmbeddingRetriever",
    version="onnx-masked-mean-v1",
    limit=4,
    model=MODEL,
    revision=REVISION,
    normalization="l2",
    score_threshold=None,
    artifact_sha256=hashlib.sha256(index_path.read_bytes()).hexdigest(),
)
validate_splits(development, held_out)
run = run_evaluation(development, passage_view, retriever, config)
```

The full artifact hash is separate from the runner's passage-view hash. Its encoding
contract includes tokenizer limits, pooling and text conventions; retain it alongside
runner outputs. Once schema-2 support lands in the runner, pass the full artifact directly.
The model's 256-token truncation, technical-domain coverage, cross-document retrieval on
real sources, unrelated/in-domain missing-evidence behavior, answer correctness and
provider abstention still require reviewed development and held-out evaluation.
