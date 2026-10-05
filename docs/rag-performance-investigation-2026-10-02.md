# RAG performance investigation, 2026-10-02

The strongest evidence points to incomplete selection of complementary passages, rather than a missing model-specific embedding setting. Qwen3-4B retrieves enough approved evidence within its first 40 results to answer 34 of 36 answerable development questions. Only 24 receive complete evidence in the final four. Ten of its twelve failures therefore have an ordering or selection problem; two also have missing candidate evidence.

The supplied percentages measure **complete evidence**, not passage recall. Public embedding benchmarks do not provide an expected percentage for this local metric. The current targets are plausible development objectives, but they are not performance guarantees from the model authors.

This investigation combines online primary-source research, code inspection, replay of saved evaluation results, and focused tests. It does not change retrieval behavior, datasets, evidence labels, application settings, or the held-out evaluation.

Supporting notes contain the detailed sources and checks:

- [Embedding model benchmarks and required settings](model-retrieval-research-2026-10-02.md).
- [Research on retrieval improvements](rag-methods-research-2026-10-02.md).
- [Evaluation audit and reproducible checks](retrieval-evaluation-audit-2026-10-02.md).

## Where the current pipeline stands

The [approved comparison](approved-model-comparison.md) uses four research papers, 204 passages, and 50 development questions. Thirty-six questions are answerable. Fourteen negatives are excluded from positive retrieval metrics. The original dense/hybrid percentages are exactly the number of completely supported questions divided by 36.

Qwen3-4B dense has the following results, verified against saved per-question rankings:

| Requested metric | Current result | Target | Interpretation |
| --- | ---: | ---: | --- |
| Evidence passage recall@4 | 69.25% under the existing reference-passage metric | 80% | This metric uses the question's original reference passages, not the approved alternative evidence groups. |
| At least one approved evidence passage in the first four | 32/36, 88.9% | 90% | One additional successful question reaches the empirical target. |
| Complete evidence for all required parts | 24/36, 66.7% | 80% | Five additional complete questions are needed to reach 29/36, or 80.6%. |
| Both expected documents represented on cross-document questions | 6/9, 66.7% | 90% | With nine questions, all nine must pass to reach at least 90%. |
| MRR@4 using approved evidence passages | 0.715 | 0.65 | This target is already met. |

Mean approved evidence-group coverage is 78.3%. This is useful partial-credit information, but it is neither complete-evidence rate nor the existing passage-recall metric. A first passage that satisfies one part can give excellent MRR while missing a qualification or the second document.

The reference-passage recall denominator also needs care. `tech-compare-fusion` lists 13 reference passages. Its maximum reference recall@4 is therefore 4/13, or 30.8%, although two appropriately chosen passages can satisfy all approved evidence groups. Across the full answerable set, the maximum possible mean reference recall@4 is 96.04%, so the aggregate 80% target is feasible. The metric nevertheless penalizes valid alternatives that complete-evidence scoring correctly accepts. Keep its name and historical values explicit; do not silently replace it with group coverage.

Every answerable development question has an approved support set of at most three existing passages: 18 need one, 16 need two, and two need three. The four-passage budget is therefore sufficient under these labels. This is a label-based upper bound used only for diagnosis, not a retrieval algorithm or proof that runtime selection will find those sets.

There are newer results than the supplied table. The completed [Vulkan reranker study](vulkan-reranking.md) selects BGE-M3 with BGE-reranker-v2-m3 over 20 candidates at **26/36, or 72.2%**, with a median query time of about 481 ms. Its cross-document completeness is 7/9 and mean group coverage is 80.3%. This improves completeness over 24/36, but still misses the 80% complete-evidence target. All ten configurations finished. The five-question-per-reranker CPU reference checks support the implementation on that subset, not full numerical equivalence. This study completed independently while the investigation was in progress; its frozen evaluation-only candidate and results remain separate from the original dense/hybrid comparison and application defaults.

## What the models' published results actually tell us

The following numbers are published retrieval benchmark scores, not expected ResearchLens success rates. nDCG@10 rewards relevant documents near the top of a ten-result ranking. It does not require every fact and qualification needed by a multi-part answer to fit in four passages.

| Model | Published retrieval score, multiplied by 100 | Benchmark |
| --- | ---: | --- |
| TF-IDF | No universal value | Depends on the corpus, tokenization, chunking, and IDF statistics. |
| MiniLM-L6-v2 | 41.95 | Original MTEB, 15 English retrieval datasets. [1] |
| BGE-M3 | 54.60 | Multilingual MTEB comparison published by Qwen. [2] |
| Qwen3-Embedding-0.6B | 64.64 | Same multilingual MTEB comparison. [2] |
| Qwen3-Embedding-4B | 69.60 | Same multilingual MTEB comparison. [2] |

The MiniLM row uses a different benchmark suite and cannot establish a numerical gap against the other rows. Qwen also reports English v2 retrieval scores of 61.83 for 0.6B and 68.46 for 4B. The broader expectation that Qwen3-4B is a stronger retriever is reasonable. A claim that it should achieve 80% complete evidence@4 on this dataset is not supported by those benchmarks.

There is no universal hybrid uplift. BGE-M3's corrected MIRACL results are 69.2 for dense, 70.4 for dense plus learned sparse retrieval, and 71.5 when multi-vector scoring is included. That native hybrid system uses the model's learned sparse weights and a much deeper candidate procedure. ResearchLens combines TF-IDF and dense rankings through RRF, so it is a different experiment. [3]

Published reranking improvements are also conditional. Qwen's English retrieval experiment improves a 61.82 dense baseline to 65.80 with its 0.6B reranker, but BGE-reranker-v2-m3 scores 57.03 in that same experiment. The local BGE reranker results can improve while that external comparison regresses. Candidate source, domain, model, metric, and serving implementation all matter. [2]

## Code findings and their practical effects

### 1. The basic model adaptations are already correct

The [model definitions](../backend/researchlens/embedding_models.py) use the correct family-specific pooling: masked mean for MiniLM, CLS for BGE-M3, and the last non-padding token for Qwen. Qwen receives a query-only `Instruct: ...\nQuery: ...` prefix. Documents receive no query instruction. The current right-padding implementation indexes the last unmasked token correctly, and vectors are normalized before exact cosine ranking. [2, 3, 4]

Relevant implementation locations are `embedding_models.py:10`, `embedding_models.py:200`, `embedding_models.py:238`, `embeddings.py:98`, and `retrieval.py:157`. Focused tests cover the query prefix and pooling with different sequence lengths.

The adapters impose 512 tokens for BGE and Qwen, below their advertised capacities. That is not causing truncation here: measured maximum passage lengths are 322 tokens for BGE and 284 for Qwen. MiniLM truncates eight of 204 passages at 256 tokens. This deserves a small MiniLM-specific experiment, but it cannot explain the BGE/Qwen shortfall. All measured MiniLM reranker pairs also fit their 512-token limit.

No missing Qwen instruction, incorrect pooling rule, vector-normalization error, or approximate-nearest-neighbor recall loss was found. Search scores every saved dense vector exactly at `retrieval.py:161`. These checks do not establish full numerical equivalence with every official runtime.

### 2. Each passage is ranked independently against the whole question

`EmbeddingRetriever.search` encodes one question and returns the highest individual cosine scores. `RerankedRetriever.search` scores each candidate against that same whole question and sorts its individual relevance score. Neither selects a set that explicitly covers the question's distinct requested parts. The optional diversity step penalizes passage similarity; it does not measure missing factual coverage.

This is the best-supported improvement priority. The existing 40-candidate Qwen3-4B run contains complete support for 34/36 questions, yet its first four complete only 24. Examples reproduced from the saved rankings:

| Question | Observed miss | Why it matters |
| --- | --- | --- |
| `tech-compare-network-roles` | All first four passages are from the canopy paper; the needed autoencoder paragraph `pmc11121878:p16:w0` is rank 18. | Several related passages from one document crowd out the other requested explanation. |
| `tech-both-checks-clean` | The structured-illumination-to-bright-field step is rank 23; a final both-modes condition is available at rank 7. | General descriptions outrank the procedure and its completion condition. |
| `tech-wafer-exact` | Main SNR evidence is present, but efficiency qualifications need passages at ranks 9 and 18. | Topical relevance misses necessary qualifications. |
| `tech-amff-layers` | Paragraph 41 is rank 1, but paragraph 46, needed to acknowledge conflicting source statements, is rank 5. | A high MRR can coexist with incomplete support. |

For `tech-changing-neighborhood`, the required Gaussian-weighting definition is missing even from the first 40. `tech-compare-localization-outputs` also lacks required canopy evidence in those candidates. These two need better candidate retrieval as well as selection.

Test query decomposition and selection for complementary evidence. Derive subquestions from the user's question and identify documents through indexed metadata. Retrieve for each part, merge candidates, and allocate the four final slots by relevance and coverage. Never use evaluation `required_claims`, approved evidence IDs, or `expected_source_ids` at query time. Research on iterative retrieval supports testing retrieval aligned with intermediate information needs, but supplies no guaranteed local uplift. [5]

Source quotas alone are insufficient. Qwen hybrid already represents both documents on all nine cross-document questions, but completes only four of them. Selection must find the right evidence within each document.

### 3. Available document context is omitted from every main scoring input

The ingestion code stores document title and source section, but embeds only `passage.text` at `ingest.py:92`. TF-IDF also indexes only that text at `retrieval.py:53`. The MiniLM reranker pairs the question with only that text at `reranking.py:88`.

A paragraph can say "the network" or "this method" without naming its study or section. Many questions explicitly name or paraphrase the study. The stored title and section could help connect them. This omission is verified; its contribution to the current miss count has not been measured.

Test an encoding input such as document title, section path, and passage text. Preserve canonical passage text, IDs, citation spans, and labels. Version the new encoding contract and rebuild vectors. Token-visibility diagnostics must measure the actual enriched input and map retained offsets back to canonical passage text; the existing diagnostics currently measure plain text.

Start with deterministic title and section metadata before adding generated context. Anthropic reports retrieval failure@20 dropping from 5.7% to 2.9% with contextual embeddings plus contextual BM25, and to 1.9% with reranking in its experiment. These are contextual-retrieval results on another evaluation, not predicted ResearchLens completeness@4 gains, and they do not isolate title-prefixing alone. [6]

### 4. Equal RRF demonstrably removes useful dense-only results

The implementation at `retrieval.py:220` correctly computes reciprocal rank fusion. The default configuration uses 20 candidates per component and `rrf_k=60`. A passage at rank 20 in both components scores `2/80 = 0.025`, while a dense-only rank-1 passage scores `1/61 = 0.01639`. Agreement can outweigh much stronger rank in one component. [7]

This happens on `tech-turn-and-flip-labels`, whose question asks how aircraft-cover training pictures can be turned and reflected without redrawing defect outlines. Qwen dense ranks the supporting augmentation paragraph `pmc11510794:p34:w0` first and supplies complete evidence. TF-IDF does not find it in its first 20. Four passages with support from both rankings score between 0.02886 and 0.03252 and displace it. Hybrid then has zero approved evidence for this question.

The TF-IDF ranking was recomputed locally; the dense ranks were taken from the saved real-model run. This demonstrates the fusion mechanism behind a regression, not an arithmetic implementation bug.

Retain a dense-only control. Evaluate lexical retrieval separately, then test a small predefined choice of BM25 or BGE-M3 learned sparse retrieval, candidate union followed by selection, and a lower RRF constant or dense-first policy. Do not assume BM25 or native BGE sparse will improve this corpus. The previous grid already tested deeper pools and several lexical/dense weights without beating Qwen dense; repeating those settings has little value. [3, 7]

### 5. Chunk boundaries can separate definitions and qualifications

`chunk_documents` at `ingest.py:24` splits each paragraph into nonoverlapping 180-word windows. It does not preserve sentence boundaries or attach neighboring explanatory text. `tech-wafer-exact` needs the continuation `p14:w180`, while `tech-moving-signal-addition` needs `p8:w180`. Other required definitions are in separate nearby paragraphs.

The split behavior and these evidence locations are verified. A chunking change improving rankings is still a hypothesis. Start by testing neighboring-passage retrieval or surrounding context in the retrieval representation, keeping the four canonical output passages and scorer fixed. If changing canonical chunk boundaries, create a versioned experiment and remap and review evidence spans. Do not compare against stale labels or call four larger parent documents the same four-passage task.

Longer encoder context alone will not repair a window that ingestion already split. Late chunking addresses loss of surrounding context by contextualizing tokens before pooling chunks, but is a separate experimental architecture with model and resource requirements. [8]

The extractor also intentionally excludes figures, tables, and captions and replaces mathematical formulas with `[formula omitted]`, as documented in `corpus.py:27` and implemented by `prose_text` and `extract`. This limits scientific questions whose evidence exists only in that material, and can remove useful mathematical context from otherwise retained prose. It does not explain absent corpus support for the current 36 answerable cases: all have approved support in the extracted text. Broader scientific QA should evaluate structured tables, captions, and faithful formula extraction with a separately versioned corpus and labels.

### 6. Retrieval depth and the answer-provider budget are separate

`prepare_answer_context` takes only the first four passages at `answers.py:64`; the provider also declares `MAX_PASSAGES = 4` at line 106. Raising the search limit does not by itself deliver more evidence to generation.

The saved Qwen hybrid ranking reaches 29/36 complete evidence at ten passages, but its four-passage context remains 21/36. Existing six/eight-slot previews reach at most 27/36 across the tested CPU configurations. More context may help, but it changes the product constraint and does not replace better four-passage selection. Generation quality and abstention need their own evaluation after retrieval is selected.

The workspace's resolved retrieval settings were `tfidf` and `minilm` during this investigation. Offline model selection does not automatically change the application backend. This does not explain the benchmark results; it matters when adopting a selected configuration. It also does not establish the configuration of an independently running server.

## Recommended next experiment

Keep the approved development labels fixed and preserve the existing frozen selection as a comparison. Define a small experiment before running it, rather than combining all suggested changes at once.

| Priority | Experiment | What it tests | Evidence needed to adopt it |
| --- | --- | --- | --- |
| 1 | Split multi-part questions into subqueries, retrieve per part, select complementary evidence within four slots. | Whether the ten ordering/selection failures can be reduced. | Complete evidence improves, especially the named cross-document and qualification failures, without offsetting regressions. |
| 2 | Add title and section path to retrieval inputs; rebuild dense vectors and compare lexical inputs separately. | Whether missing document context harms study identification and paragraph relevance. | Better candidate coverage or final completeness with unchanged canonical evidence. |
| 3 | Use the completed BGE reranker study as a control, then apply the reranker to subqueries or a coverage selector. | Whether stronger pair scores help when paired with a selection objective matching complete evidence. | Improvements beyond the saved 26/36 setting, with latency and the limits of the reference-runtime checks reported. |
| 4 | Evaluate BM25 or BGE native sparse candidates, then one predefined alternative fusion policy. | Whether lexical matching can add evidence without removing dense-only successes. | Preserve dense successes such as `tech-turn-and-flip-labels`; report every gain and regression. |
| 5 | Test neighbor expansion or sentence-aware chunking on remaining definition/qualification failures. | Whether representation boundaries obstruct retrieval. | Versioned evidence mapping if canonical chunks change; no accidental budget increase. |
| 6 | Compare the official Qwen task prompt against one scientific-evidence prompt. | Whether a prompt refinement provides a small additional gain. | Same corpus and candidate/selection policy; do not expect the author's reported instruction gains when an instruction is already present. |

For each configuration, report candidate complete-support coverage at 20/40, final complete evidence@4, approved group coverage@4, hit@4, MRR@4, both-documents success on the nine cross-document cases, and per-question gains/losses. Keep legacy reference recall separately named. Include p50/p95 latency and memory, since the stronger models and rerankers have material costs.

Use the 36 answerable development questions for diagnosis, but acknowledge their small size and shared four-paper corpus. One answerable case changes the success rate by 2.78 percentage points; one cross-document case changes that cohort by 11.11 points. Freeze the selected configuration before running held-out retrieval. No claimed improvement in generated-answer correctness follows from retrieval metrics alone.

The immediate success criterion is five additional complete questions over Qwen dense, or three over the saved BGE reranker result. The diagnostic upper bound shows enough evidence exists within the four-passage budget. It does not predict that any particular proposed method will reach the target.

## Verification performed

- Replayed the current evidence scorer over all nine baseline configurations and all 50 questions: 450/450 saved metric sets match.
- Recomputed four saved failure analyses: per-question classifications and failure counts match. A newer summary metadata field does not change scoring.
- Reran TF-IDF against the saved artifact: all 50 rankings and metrics match, including 15/36 complete questions.
- Reproduced the dense-only evidence displacement in the turn-and-flip hybrid example using actual TF-IDF rankings and saved Qwen rankings.
- Ran `.venv/Scripts/python.exe -m pytest backend/tests/test_embedding_models.py backend/tests/test_retrieval.py backend/tests/test_evaluation_evidence.py -q`: **84 passed**. One existing Starlette/httpx deprecation warning remains.
- Fetched the primary sources online. No embedding weights were downloaded, dense models rerun, paid inference invoked, or held-out questions searched for this investigation.

The findings separate observed behavior from untested improvements. The concrete problems are the metric mismatch, lost complementary evidence during selection, and harmful fusion on identified cases. Metadata omission and chunk boundaries are verified design limitations whose quality impact needs controlled measurement. No evidence supports promising that a model setting alone will produce 80% completeness.

## Primary online sources

1. [MTEB paper, task metrics and original English results](https://arxiv.org/html/2210.07316v3).
2. [Official Qwen3-Embedding repository and evaluation tables](https://github.com/QwenLM/Qwen3-Embedding), [model card and instructions](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B), and [Qwen3 Embedding paper](https://arxiv.org/html/2506.05176v1).
3. [BGE-M3 model card](https://huggingface.co/BAAI/bge-m3) and [corrected paper, version 5](https://arxiv.org/html/2402.03216v5).
4. [MiniLM model card, pooling and truncation guidance](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).
5. [IRCoT, interleaving retrieval with information needs in multi-step questions](https://aclanthology.org/2023.acl-long.557/).
6. [Anthropic contextual retrieval experiment](https://www.anthropic.com/engineering/contextual-retrieval).
7. [Elasticsearch RRF formula and rank-constant behavior](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion).
8. [Late chunking paper](https://arxiv.org/abs/2409.04701).
