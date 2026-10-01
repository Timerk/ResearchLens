# Retrieval development experiments

The [approved baseline](approved-model-comparison.md) found complete evidence for
24/36 answerable development questions with Qwen3-4B dense at k=4. This work adds
actual tokenizer visibility, weighted RRF, optional local cross-encoder reranking
and a predefined development experiment. TF-IDF stays the application default.
No settings are selected from held-out questions, and no answer generation is needed.

## Local reranker and configuration

The reranker is [cross-encoder/ms-marco-MiniLM-L6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2/tree/233902d25c440f23af6f7d6e94d2946bac0bee0a),
pinned to revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`. Its model card declares
Apache-2.0 and English. It was trained on MS MARCO passage ranking; performance on
this research corpus must be measured. The float32 ONNX file is 91,011,230 bytes,
plus the tokenizer. It uses the existing `embeddings` extra on Windows/Python 3.13,
without Torch, a GPU, paid embedding calls or remote repository code.

Explicitly download the pinned files before startup:

```sh
rtk proxy uv run --locked --extra embeddings --directory backend python -m researchlens.reranking --download
```

Startup and evaluation are cache-only. One tokenizer and ONNX session are loaded
per retriever. Question and passage are encoded as a BERT pair in that order, with
special tokens, longest-first truncation at 512 tokens, right padding and batch size
eight. CPU intra/inter-op threads are two/one. Raw relevance logits determine rank;
they are not probabilities or answerability thresholds. Full original passages and
citation IDs survive reranking, even when the pair encoder sees a prefix only.

Optional application settings in `.env`:

```dotenv
RETRIEVAL_BACKEND=embeddings
RETRIEVAL_RERANKER=minilm
RETRIEVAL_RERANK_CANDIDATES=40
RETRIEVAL_DIVERSITY=0
```

Use the existing model-specific embedding artifact and `EMBEDDING_MODEL`. Reranking
uses a fixed candidate pool independently of the returned limit, preserving ranking
prefixes and `search(question, limit)` compatibility up to that pool size. Default
reranking is `none`; enabling it with TF-IDF fails explicitly in this integration.

Hybrid settings use `HYBRID_CANDIDATES`, `HYBRID_LEXICAL_WEIGHT` and
`HYBRID_EMBEDDING_WEIGHT`. Weighted RRF sums `weight / (60 + rank)` for each active
component, deduplicates by stable passage ID and resolves ties by artifact order.
Defaults remain 20 candidates per component and weights 1/1, preserving previous
scores and rankings. Weights 0.5/0.5 have the same ranking with half the scores.
A zero-weight component is not searched. Scores are not calibrated across settings.

Optional diversity selection follows reranking. It fixes the best passage first,
then maximizes `(1 - diversity) * rank_utility - diversity * maximum_similarity`
against already selected passages. Rank utility is `1 - zero_based_rank / pool_size`;
redundancy is nonnegative cosine similarity between saved dense passage vectors.
The default penalty is zero; the experiment tests 0.2. No evidence labels, source
quotas or question-specific oracle enter retrieval. Ordering with a diversity penalty
can differ from descending relevance logits, which remain available as hit scores.

## Encoding and runner integration

`EmbeddingRetriever.get_encoding_diagnostics()` now measures every saved passage
with the loaded tokenizer, caches the result and returns the existing strict runner
contract. Hybrid and reranked adapters delegate this hook. Full token counts include
special tokens; retained character ranges come from actual truncated offsets. A
tokenizer clone measures the untruncated ONNX inputs; Torch uses its pinned fast
tokenizer. Measurements do not mutate live tokenization or regenerate vectors.
Artifact, encoding and text hashes bind these measurements to the unchanged passages.

The existing runner records an allowlisted nested `RetrievalConfig.reranker` with
the pin, runtime, precision, pair convention, candidate count and diversity penalty.
`get_reranking_diagnostics(question)` supplies per-pair counts and retained passage
ranges, validated against source text before recording them. Pair counts include
the question and special tokens. Reranking timing includes tokenization and visibility
measurement. These measurements describe encoder visibility, not answer support.

`retrieval_analysis` uses the existing evidence scorer for offline context previews
at four, six and eight passages. The 3,000-character passage and 16,000-character
serialized context caps remain fixed. The application's provider still receives at
most four passages; larger previews are explicit experiments, not changed defaults.
No generated-answer correctness, citation support or abstention result is implied.

Its label-only failure oracle finds minimal passage sets satisfying all approved
OR/AND alternatives. It distinguishes missing candidate support, poor ordering and
evidence requiring more than four passages. This happens after retrieval, never at
query time. Labels are conservative and not exhaustive, so these are bounds relative
to the approved annotations rather than proof that another valid answer is impossible.

## Predefined development grid

The helper delegates every run and paired report to the existing evaluation runner;
it introduces no alternative relevance scorer or dataset. It verifies every artifact
and approved label identity before loading a model, uses fresh sequential processes,
and writes the entire plan before executing the first question. Existing output
directories are rejected. Failed stages are recorded without automatic retries or
upstream exception strings. Downloading is a separate explicit operation.

Twenty-one configurations are defined before inspecting their results:

- TF-IDF, MiniLM dense and Qwen3-0.6B dense for baseline/visibility diagnostics.
- For each of BGE-M3 and Qwen3-4B: dense; equal RRF with 20 and 40 candidates per
  component; RRF with 40 candidates and lexical/dense weights 0.25/0.75 and 0.75/0.25.
- For each of those two models: dense reranking with 20 and 40 candidates;
  dense reranking with 40 candidates and diversity 0.2; and 0.25/0.75 hybrid with
  40 candidates per component followed by reranking of its first 40 unique passages.

Each returns a ranking of 40 passages, except the 20-candidate rerankers, which
return 20. Prefixes 1/4/10/20/40 are scored where available. Context previews use
the same rankings. Candidate-pool differences are part of the experiment, not
hidden changes to corpus or labels. Timing reflects the recorded requested limit.

```sh
rtk proxy uv run --locked --extra embeddings --extra embedding-models --directory backend python -m researchlens.retrieval_experiments --indexes ../evaluation/runs/approved-models-2026-10-01-k4/indexes --output ../evaluation/runs/retrieval-improvements-2026-10-02 --repeats 3 --warmups 1
```

The referenced indexes are local baseline artifacts. On another machine, first
reproduce ingestion using the baseline comparison helper. The three timed searches
and one warmup per question are fixed across this grid. They provide 150 timing
samples per configuration and stability checks; they do not measure server throughput.
All runs use the 50 approved development questions and unchanged evidence labels.

## Measurements and next decision

The full grid is pending. A preliminary real MiniLM visibility check measured all
204 passages, finding eight truncated by the 256-token limit. At k=4,
`tech-too-many-shortcuts` retrieves labeled evidence outside the encoded prefix.
That check verifies instrumentation; it does not measure an improvement or establish
why a ranking failed. The full grid will measure all four embedding tokenizers.

Select future settings using complete evidence at the application limit, cohort and
paired regressions, context character use and CPU latency. Freeze settings before
held-out retrieval. Chunking is unchanged; changes to extraction or passage identities
need separate evidence-label mapping and comparison work. Answer abstention remains
a separate pending evaluation. No paid API calls are planned.
