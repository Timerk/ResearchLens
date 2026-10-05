# Embedding model performance and configuration research

Researched on 2026-10-02 from official model cards, model configuration files, benchmark papers, and library documentation. This note covers published expectations and model setup. The separate pipeline investigation connects these findings to ResearchLens code and evaluation results.

## What performance should we expect?

There is no defensible conversion from a model's public benchmark score to ResearchLens evidence recall@4. The public results below measure ranking quality over other collections and relevance labels. They do not establish expected rates for finding every evidence passage, answering every required part, or representing both documents within four slots.

The original MTEB paper defines retrieval's primary metric as nDCG@10. It also computes recall and MRR, but they are different metrics. nDCG discounts relevant results at lower ranks and can use graded relevance. Evidence recall counts recovered evidence; hit rate only asks whether at least one qualifying result appeared. Even on the same collection, none of these percentages are interchangeable. [S1]

| Model | Published retrieval result | Benchmark and scope |
| --- | ---: | --- |
| TF-IDF | No universal model score | A corpus-dependent term-weighting method. Results depend on the vocabulary, tokenization, document segmentation, and IDF statistics. [S2] |
| `sentence-transformers/all-MiniLM-L6-v2` | 41.95 | nDCG@10 multiplied by 100; 15 English retrieval datasets in the original MTEB paper. Table 1 reports this score, and Table 9 identifies the exact checkpoint. [S1] |
| `BAAI/bge-m3` | 54.60 | Multilingual MTEB retrieval category, as reported in Qwen's published comparison. This is a different benchmark suite from the MiniLM row. [S3] |
| `Qwen/Qwen3-Embedding-0.6B` | 64.64 multilingual; 61.83 English v2 | Retrieval category scores in Qwen's official results. [S3] |
| `Qwen/Qwen3-Embedding-4B` | 69.60 multilingual; 68.46 English v2 | Retrieval category scores in Qwen's official results. [S3] |

These are dated, reproducible publication references, not a claim about today's live leaderboard. Qwen's model card attributes the comparison-model results to a May 2025 leaderboard snapshot; its paper and repository record other June 2025 snapshot dates. The scores above agree across those sources. Use the explicitly named benchmark when quoting them. [S3, S4]

Qwen's multilingual comparison supports a prior expectation that its 4B model will usually be stronger than its 0.6B model and BGE-M3 over that benchmark suite. It does not imply that every local query set follows that ordering. MiniLM's 41.95 cannot be used to calculate a quality gap against the newer multilingual or English v2 results. [S1, S3]

The user's table is the **complete-evidence rate**, not evidence passage recall. The [approved model comparison](approved-model-comparison.md) records 24 of 36 answerable questions with complete evidence for Qwen3-4B dense, which gives 66.7%. That same run has 78.3% mean evidence-group coverage and MRR@4 of 0.715. MRR already exceeds the stated 0.65 target while complete evidence misses its 80% target. The measures answer different questions.

The local results therefore cannot be called abnormal just because the product target is 80% or 90%. Equally, the public benchmarks do not prove that the local implementation is correct. The next useful comparison is an ablation on the same questions, corpus, evidence labels, and cutoff.

## What does the literature say about hybrid retrieval?

BGE-M3's own paper provides a controlled dense versus hybrid comparison. Its current version reports these MIRACL development-set nDCG@10 scores. [S5]

| BGE-M3 configuration | nDCG@10 multiplied by 100 |
| --- | ---: |
| Dense | 69.2 |
| Learned sparse | 53.9 |
| Dense plus learned sparse | 70.4 |
| Dense, learned sparse, and multi-vector scores | 71.5 |

The hybrid implementation matters. The paper retrieves the union of the top 1,000 dense and top 1,000 sparse candidates, then combines dense and learned sparse scores with weights of 1 and 0.3. Its multi-vector comparison uses a different candidate procedure. These results are not a benchmark of ResearchLens's lexical implementation or fusion settings. BGE-M3's learned sparse weights are also distinct from TF-IDF and BM25. [S5, S6]

ResearchLens's [approved comparison](approved-model-comparison.md) uses 20 lexical and 20 dense candidates with equal-contribution reciprocal rank fusion and `k=60`. Its lexical side is TF-IDF. It therefore evaluates a different hybrid system from the BGE-M3 paper. A local regression from 61.1% to 58.3% complete evidence does not contradict that paper's native sparse hybrid result.

The same paper reports a much larger native hybrid gain on its MLDR long-document benchmark, from 52.5 dense to 64.8 dense plus sparse. It explicitly trains on MLDR's training set, so that gain is neither a universal zero-shot expectation nor a promised gain for research-paper chunks. [S5, S6]

Use the corrected MIRACL results. BGE's model card records a July 2024 evaluation bug: earlier code removed passages whose IDs happened to match query IDs. The paper's older 67.8 dense and 68.9 hybrid results are superseded. This is also a useful reminder to audit the evaluation before attributing all shortfalls to the embedding model. [S5, S6]

## Required model-specific setup

| Model | Query formatting | Pooling and similarity | Input-length constraint |
| --- | --- | --- | --- |
| MiniLM-L6-v2 | Plain text in the official example | Attention-mask-aware mean pooling; normalize for cosine or normalized dot product | Sentence Transformers defaults to 256 wordpieces. Longer text is truncated. [S7] |
| BGE-M3 | Plain text; the model card explicitly says query instructions are unnecessary | CLS-token pooling; the official Sentence Transformers module chain includes normalization | 8,192 tokens. [S6, S8] |
| Qwen3-Embedding-0.6B | Query-only `Instruct: {task}\nQuery:{query}`; documents have no task instruction | Last non-padding token; normalize before dot-product scoring, or use cosine | Advertised 32K context; runtime settings can impose a shorter limit. [S3, S9] |
| Qwen3-Embedding-4B | Same query-only instruction format | Last non-padding token; 2,560 dimensions at full width | Advertised 32K context; runtime settings can impose a shorter limit. [S3, S9] |

Qwen's Sentence Transformers configuration has a named `query` prompt but `default_prompt_name` is `null`. Calling `model.encode(queries)` without a prompt does not activate that query instruction. Its official usage calls `model.encode(queries, prompt_name="query")`, while documents use plain `model.encode(documents)`. The 4B model has the same prompt configuration. [S3, S9]

Qwen reports that query instructions improve its tested downstream tasks by approximately 1% to 5%, and recommends a task-specific instruction written in English. That is the author's reported range, with no guarantee of the same local improvement. A suitable scientific-document instruction is an experiment, for example `Given a question about research papers, retrieve passages that provide evidence needed to answer it`. Evaluate it against the official default prompt before adopting it. [S3]

Padding and pooling must agree. Qwen's raw Transformers example uses left padding and pools the final token; its pooling helper also handles right padding by indexing the last unmasked token. Blindly averaging Qwen's token states, or selecting a padding token, departs from the reference implementation. BGE-M3 and MiniLM also use different pooling rules. A single generic pooling function is not valid for all three families. [S3, S7, S8, S9]

Count tokens with the embedding model's tokenizer. A chunk length in characters or words is not a token limit. For MiniLM, a long chunk can retain evidence in the stored text while its embedding never sees that evidence because it appears after token 256. Test the fraction of chunks truncated, and the position of labeled evidence relative to the retained tokens. Raising `max_seq_length` alone does not establish that MiniLM will perform well at the longer length. Its card describes a sentence and short-paragraph model trained with a 128-token sequence limit. [S7]

Use full-dimensional reference embeddings first. Qwen supports reduced output dimensions, but that option should be treated as a measured quality/cost tradeoff. Treat lower precision, quantization, alternative serving backends, and changed input formatting the same way. Compare the deployed backend against the official implementation on representative passages before claiming benchmark parity. BGE's card specifically notes a slight quality loss from its `use_fp16=True` setting. [S3, S6]

## Improvements supported by the sources

1. Verify query prompts, pooling, truncation, normalization, and the exact checkpoint before spending effort on fine-tuning. The model families require different input and output handling. [S3, S6-S9]
2. Measure candidate evidence recall at a larger depth, such as 20, 50, and 100, while retaining four as the final context budget. A reranker cannot recover evidence absent from its candidates. Sentence Transformers recommends retrieving about 100 candidates before reranking, and the Qwen reranker evaluation uses the top 100 candidates from Qwen3-Embedding-0.6B. [S4, S10]
3. Evaluate a reranker on that candidate set. Qwen's English retrieval experiment moves from 61.82 for 0.6B dense retrieval to 65.80 with Qwen3-Reranker-0.6B, or 69.76 with Qwen3-Reranker-4B. These are benchmark results, not predicted local gains. [S4]
4. Keep a dense-only control and measure each hybrid component separately. BGE-M3's native sparse output is worth testing as a separate option, but requires the appropriate encoder interface. Its dense embedding alone does not supply learned lexical weights. [S6]
5. Select improvements on a development split and report their effect on held-out questions. The exact chunk size, candidate depth, lexical weight, and diversity policy are local design choices; none of the model cards supplies a setting guaranteed to satisfy ResearchLens's four-passage evidence targets.

Reranking can also regress. In Qwen's same top-100-candidate experiment, `BGE-reranker-v2-m3` scores 57.03 on English retrieval, below the 61.82 dense baseline. A general recommendation to rerank does not establish that an arbitrary reranker, prompt, or serving implementation will help this corpus. [S4]

## Sources

- S1: [MTEB paper, version 3, task definitions and Tables 1 and 9](https://arxiv.org/html/2210.07316v3).
- S2: [Scikit-learn text feature extraction documentation](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction).
- S3: [Official Qwen3-Embedding-0.6B model card, usage and evaluation tables](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B). The card includes the 4B comparison and shared model-family guidance.
- S4: [Qwen3 Embedding paper, version 1, retrieval and reranking results](https://arxiv.org/html/2506.05176v1), and [official repository evaluation tables](https://github.com/QwenLM/Qwen3-Embedding#evaluation).
- S5: [BGE-M3 paper, version 5, Tables 1 and 3 and retrieval implementation](https://arxiv.org/html/2402.03216v5).
- S6: [Official BGE-M3 model card](https://huggingface.co/BAAI/bge-m3), including the evaluation correction, RAG recommendations, and sparse/multi-vector examples.
- S7: [Official MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), and [default sequence-length configuration](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/blob/main/sentence_bert_config.json).
- S8: [BGE-M3 pooling configuration](https://huggingface.co/BAAI/bge-m3/blob/main/1_Pooling/config.json), [normalization module chain](https://huggingface.co/BAAI/bge-m3/blob/main/modules.json), and [sequence-length configuration](https://huggingface.co/BAAI/bge-m3/blob/main/sentence_bert_config.json).
- S9: Qwen [0.6B prompt configuration](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/blob/main/config_sentence_transformers.json), [0.6B pooling](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/blob/main/1_Pooling/config.json), [4B prompt configuration](https://huggingface.co/Qwen/Qwen3-Embedding-4B/blob/main/config_sentence_transformers.json), and [4B pooling](https://huggingface.co/Qwen/Qwen3-Embedding-4B/blob/main/1_Pooling/config.json).
- S10: [Sentence Transformers retrieve-and-rerank documentation source](https://github.com/huggingface/sentence-transformers/blob/master/examples/sentence_transformer/applications/retrieve_rerank/README.md).

All sources above were fetched online during this investigation. No model quality experiment was run for this note; proposed improvements remain hypotheses until tested against ResearchLens evidence labels.
