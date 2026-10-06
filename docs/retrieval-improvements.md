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

The complete grid and a fresh application-limit confirmation ran on 2026-10-02.
None of the new configurations beats Qwen3-4B dense at k=4. The predefined selection
rule maximizes complete evidence, then mean group coverage, then prefers lower median
latency. Group-coverage ties ignore rounding noise below 12 decimal places. Larger
context budgets do not enter this four-passage application selection.

The [selected configuration](development-selected-retrieval.json) is therefore the
existing Qwen3-4B dense setup, with no reranker, hybrid fusion, diversity penalty or
relevance threshold. This is a frozen development selection, not held-out superiority
or an automatic change to the TF-IDF application default. No held-out questions or
answer generation were executed. No configuration reaches the provisional 80%
complete-evidence target at four, six or eight context slots.
The existing evaluation CLI accepts the frozen JSON through `--retrieval-config`;
use the matching Qwen3-4B artifact, `--retriever embeddings` and `--limit 4`.

### Protocol verification

All 21 grid runs and their analysis/report stages completed without errors. Three
timed searches and one warmup per question provide 3,150 timed samples. The selected
configuration's actual limit-4 confirmation adds five searches and one warmup per
question, for 250 samples and 3,400 timed samples in total. Rankings were stable
across repeats in every run. All 50 confirmation IDs and metrics match the selected
grid's first four passages. Seven unchanged control configurations also reproduce
the previous approved k=4 IDs and metrics for all 50 questions, giving 350 control
prefix checks. Timing protocols and requested limits differ from the earlier study;
do not infer a speed change from small cross-study timing differences.

All runs use implementation commit `28a0174f633a24d55ffecaaa49a3eabcbac3367c`, the
same lockfile, cached vectors, 50 approved development questions and separately
approved labels. The approved label hash remains
`8e1b118b740f615c5985eda60936b796cf7abb8c2c302b7845ffbcaa93b1973f`.
Hardware is Ryzen 7 9800X3D/32 GiB RAM, Windows AMD64/Python 3.13.14, CPU only.
The dirty flags reflect untracked `.serena/` and documentation edits; retrieval,
evaluation and lockfile contents matched that commit throughout the measurements.
Subsequent hardening makes partial-label diagnosis explicitly unknown and validates
configured models against one artifact read. Neither changes these fully labeled
ranking results. The final backend suite passes 193 tests; lint and formatting pass.

Full generated runs remain ignored under `evaluation/runs/retrieval-improvements-2026-10-02/`
and `evaluation/runs/retrieval-improvements-confirmation-2026-10-02/`.
[Selected result excerpts](retrieval-improvement-results.json) archive code/runtime,
artifact/run hashes, all settings, cutoff/cohort/context summaries, aggregate
failure classifications and paired outcome summaries. Full per-case records are
linked in the JSON archive's `archive_provenance`. They contain no model weights, vectors,
duplicate dataset text or credentials. The existing runner supplies every relevance
score and paired comparison.

### Four-passage results

Complete evidence is counted out of the 36 answerable questions. Mean group coverage
averages each question's fraction of satisfied groups, including OR/AND alternatives.
The 14 negatives have no positive relevance score. Medians measure the grid's recorded
limit of 40, or 20 for the 20-candidate rerankers, and exclude warmup/setup.

| Configuration | Complete /36 | Group coverage | Median ms |
| --- | ---: | ---: | ---: |
| TF-IDF | 15 | 55.2% | 0.61 |
| MiniLM dense | 17 | 61.8% | 1.65 |
| Qwen3-0.6B dense | 18 | 61.3% | 46.11 |
| BGE-M3 dense | 22 | 70.8% | 25.45 |
| BGE-M3 equal hybrid, 20 each | 21 | 67.8% | 27.07 |
| BGE-M3 equal hybrid, 40 each | 21 | 67.8% | 27.19 |
| BGE-M3 hybrid, 40 each, lexical 25% | 21 | 68.5% | 27.28 |
| BGE-M3 hybrid, 40 each, lexical 75% | 21 | 69.2% | 27.36 |
| BGE-M3 dense + rerank 20 | 22 | 73.8% | 392.52 |
| BGE-M3 dense + rerank 40 | 19 | 68.2% | 798.32 |
| BGE-M3 dense + rerank 40 + diversity 0.2 | 18 | 65.5% | 799.18 |
| BGE-M3 hybrid lexical 25% + rerank 40 | 19 | 68.2% | 834.72 |
| Qwen3-4B dense | 24 | 78.3% | 216.74 |
| Qwen3-4B equal hybrid, 20 each | 21 | 68.7% | 217.59 |
| Qwen3-4B equal hybrid, 40 each | 21 | 68.7% | 219.75 |
| Qwen3-4B hybrid, 40 each, lexical 25% | 20 | 67.2% | 221.85 |
| Qwen3-4B hybrid, 40 each, lexical 75% | 23 | 72.2% | 217.65 |
| Qwen3-4B dense + rerank 20 | 20 | 69.6% | 513.48 |
| Qwen3-4B dense + rerank 40 | 19 | 68.2% | 915.96 |
| Qwen3-4B dense + rerank 40 + diversity 0.2 | 21 | 71.0% | 911.36 |
| Qwen3-4B hybrid lexical 25% + rerank 40 | 19 | 68.2% | 957.75 |

The application-limit Qwen3-4B confirmation retains 24/36 complete cases (66.7%),
78.3% mean group coverage and MRR 0.715. Its median is 218.95 ms, p95 254.31 ms and
process lifetime peak RSS 8.134 GiB. Grid reranking medians range from 392.52 to
957.75 ms. Qwen3-4B reranking peaks around 8.49 GiB versus dense 8.13 GiB. These
figures include native allocations/model loading in the memory peak and do not
establish concurrent throughput, steady-state model RAM or GPU performance.

BGE-M3 rerank-20 improves mean group coverage by three percentage points, but leaves
the complete-evidence count at 22 and costs about 15 times its dense query latency.
Larger pools and the tested diversity penalty generally worsen four-passage support.
The best tested Qwen3-4B hybrid reaches 23 complete cases, still below dense's 24.
It gains completeness on four questions and loses it on five, including
`tech-turn-and-flip-labels`, `tech-manual-outline-union`, `tech-small-photo-supply`
and `tech-compare-evaluation-metrics`. Aggregate counts do not remove these regressions.

Complete-evidence counts by query style at k=4:

| Configuration | Exact /14 | Paraphrase /13 | Cross-document /9 |
| --- | ---: | ---: | ---: |
| TF-IDF | 11 | 3 | 1 |
| BGE-M3 dense | 10 | 8 | 4 |
| BGE-M3 dense + rerank 20 | 11 | 7 | 4 |
| BGE-M3 dense + rerank 40 | 10 | 6 | 3 |
| Qwen3-4B dense | 11 | 8 | 5 |
| Qwen3-4B hybrid lexical 75%, 40 each | 12 | 5 | 6 |
| Qwen3-4B dense + rerank 20 | 10 | 6 | 4 |
| Qwen3-4B dense + rerank 40 | 10 | 6 | 3 |

The best tested Qwen hybrid improves exact terminology and cross-document counts
while losing three paraphrase completions. Reranking 40 candidates reduces both
paraphrase and cross-document completeness for BGE-M3 and Qwen3-4B. These small,
correlated cohorts do not establish general performance on other papers or languages.

### Failure and truncation diagnosis

The label-only oracle finds a complete support set of at most four passages somewhere
in the corpus for every answerable case. For dense candidate pools of 40:

| Configuration | Complete top four | Support fits four within candidates, poorly ordered | Missing candidate support |
| --- | ---: | ---: | ---: |
| TF-IDF | 15 | 15 | 6 |
| MiniLM | 17 | 16 | 3 |
| Qwen3-0.6B | 18 | 16 | 2 |
| BGE-M3 | 22 | 11 | 3 |
| Qwen3-4B | 24 | 10 | 2 |

These are bounds relative to the approved alternatives, not proof that the corpus
lacks another valid answer. Reranking can address ordering only when suitable evidence
is in its candidate pool. Equal hybrid expansion from 20 to 40 candidates per component
reduces missing candidate support to one case for BGE-M3 and Qwen3-4B, while both
still supply complete top-four evidence for only 21 questions.

All 204 passages were measured for every embedding model. MiniLM truncates eight
(3.9%) at 256 tokens; its largest full input is 280 tokens. BGE-M3's largest is 322,
and both Qwen models' largest is 284. None of those three truncates at the configured
512-token limit. MiniLM's `tech-too-many-shortcuts` has labeled evidence beyond a
retrieved encoded prefix; this does not establish that truncation caused a miss.
All 14,000 recorded reranker case/candidate pairs fit below 512 tokens (maximum 312),
with zero observed passage truncation. Truncation therefore does not explain the
reranker's regressions in this grid. No causal claim about its training domain is made.

### Offline context experiments and remaining work

Selected examples show complete-evidence counts with the unchanged character caps:

| Configuration | Four slots | Six slots | Eight slots |
| --- | ---: | ---: | ---: |
| TF-IDF | 15 | 21 | 24 |
| BGE-M3 dense | 22 | 27 | 27 |
| Qwen3-4B dense | 24 | 25 | 25 |
| Qwen3-4B equal hybrid, 20 each | 21 | 24 | 27 |

The best six/eight-slot previews reach 27/36 (75%), below the provisional 80% goal.
They are potential contexts, not generated answers or a change to the provider's
four-passage budget. More context is not sufficient by itself, and its effect on answer
quality, distracting evidence, citation support and generation cost remains unmeasured.

TF-IDF returns neighbors for six of seven unrelated and all seven missing-evidence
questions. Every dense/hybrid/reranked mode returns neighbors on all 14 negatives.
No threshold was calibrated, and no abstention performance is claimed. API cost is zero.

Keep Qwen3-4B dense as the frozen four-passage development choice. BGE-M3 dense remains
a useful faster comparison, especially for a separately approved larger-context study.
The tested MiniLM cross-encoder and diversity penalty should remain optional experiments.
Future work can inspect the remaining candidate misses and test a research-suitable
reranker or selection that covers multiple requested facts without using labels at
runtime. Those would require a new predefined development experiment. Chunking stays
unchanged because these labels fit four passages and the stronger encoders retain all
passage text. Held-out retrieval and generated-answer/abstention evaluation remain pending.
