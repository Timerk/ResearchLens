# Research on improving evidence retrieval, 2026-10-02

This note compares primary-source retrieval methods with the current implementation and its saved experiments. Sources were fetched online on 2026-10-02. No new model evaluation, production change, label change, or held-out search was performed for this note. Proposed gains on ResearchLens are unmeasured unless identified as existing local results.

## What the local results already establish

The percentages in the user's dense/hybrid table are **complete evidence at four passages**, measured on 36 answerable development questions. They are not an embedding benchmark's nDCG score or a universal expectation for a model. The corpus has four articles and 204 passages. One success changes the completeness percentage by 2.78 points; one of the nine cross-document cases changes that cohort by 11.11 points. Repeated timing runs do not add independent quality samples.

The repository already contains more experiments than that table:

| Existing experiment | Local result | Consequence |
| --- | --- | --- |
| Qwen3-4B dense | 24/36 complete, 78.3% mean evidence-group coverage, MRR 0.715 | Completeness remains below target; the reported MRR already exceeds 0.65. |
| 21-configuration CPU grid | Weighted RRF, 20/40 candidates, MiniLM cross-encoder and dense diversity did not beat 24/36 | Repeating these generic recipes has weak justification. |
| Qwen3-4B dense candidate set of 40 | Complete support fitting four slots exists for 34/36 questions; 10 cases contain support but rank it poorly, and two lack candidate support | Selection and coverage deserve more attention than increasing embedding size or candidate depth alone. |
| BGE-M3 with BGE-reranker-v2-m3 over 20 candidates, Vulkan | 26/36 complete, 72.2%, including 7/9 cross-document cases | Highest completeness in the completed ten-configuration development study; the evaluation-only candidate is frozen. |
| Six/eight-slot context previews | Best tested configurations reach 27/36; Qwen3-4B dense reaches 25/36 | Increasing context alone has not reached 80%. |

Concurrent work completed the Vulkan study during this investigation. The updated report records all ten configurations completing all 50 development cases. BGE-M3 plus BGE-reranker-v2-m3 over 20 candidates remains the highest-completeness setting in that study and is frozen in [development-selected-vulkan-retrieval.json](development-selected-vulkan-retrieval.json). CPU float32 reference checks cover five questions and 20 candidates per question for each reranker. BGE's top-four order and set match on all five; Qwen's set matches on all five and order on four. These limited checks do not establish full backend equivalence. Application defaults and the earlier CPU selection remain unchanged; no held-out retrieval or answer generation is reported. No GPU jobs were rerun for this note. Existing measurements and caveats are in [the CPU report](retrieval-improvements.md), [its archived results](retrieval-improvement-results.json), [the completed Vulkan report](vulkan-reranking.md), and [its archived results](vulkan-reranking-results.json).

The label-only oracle also found that every answerable case has some approved complete support set of at most four corpus passages. Four slots are therefore feasible for the approved annotations. That does not prove a retriever can learn the right set or that the annotations cover every valid alternative.

## Primary-source findings and their limits

### Retrieve enough candidates, then select evidence for the actual question

Sentence Transformers documents a two-stage design that retrieves a broad candidate set, for example 100 passages, then scores question/passage pairs with a cross-encoder [1]. This motivates measuring candidate recall before changing the reranker. It does not establish that 100 candidates or any particular cross-encoder is optimal here.

ResearchLens already implements this design. The local MiniLM reranker regressed Qwen3-4B completeness, while the saved BGE-reranker-v2-m3 result improved completeness over the dense baseline. Larger candidate pools also sometimes regressed completeness. A reranker cannot recover evidence absent from its candidates; a larger pool can add competing passages that displace complementary evidence from four slots.

The next design question is how to select passages that jointly answer all requested parts. The current dense retriever encodes the whole question once. The reranker independently scores each passage against that same question. Its optional diversity penalty measures similarity between passages, not whether each requested fact has support. These are legitimate retrieval designs, but neither explicitly optimizes the project's all-parts metric.

IRCoT is a primary research example of retrieving again as a multi-step question is resolved. Its ACL paper reports improvements of up to 21 points in retrieval and 15 points in downstream QA on HotpotQA, 2WikiMultihopQA, MuSiQue, and IIRC [2]. Those are results on different tasks and metrics, not an expected ResearchLens uplift. Many ResearchLens comparisons have explicit independent subquestions and can start with simpler decomposition, without adopting the full IRCoT procedure.

A concrete experiment is to split a question such as the canopy/heater training-computer comparison into one query for each study and requested fact. Retrieve and rerank each subquery, retain the original question's candidates, deduplicate by passage ID, and select four passages using estimated subquestion support. Derive study identity from the user's question and corpus metadata. Never use evaluation `expected_source_ids`, required claims, or evidence groups inside retrieval. An unconditional two-documents quota would harm ordinary single-document questions and would not establish that either document supplies the requested evidence.

### Add document context to the text used for retrieval

Anthropic's Contextual Retrieval prepends a document-specific description, usually 50 to 100 tokens, to each chunk before embedding and BM25 indexing [3]. In its study, contextual embeddings reduced failure measured as `1 - recall@20` from 5.7% to 3.7%; contextual embeddings plus contextual BM25 reduced it to 2.9%; adding reranking reduced it to 1.9%. These are relative failure reductions of 35%, 49%, and 67%. They are **not** absolute recall gains of those sizes, top-four results, or guarantees for these embedding models.

The local code has a concrete gap this method could address. `Passage` retains titles and section paths, but embedding ingestion uses only `passage.text` at [ingest.py](../backend/researchlens/ingest.py#L92), TF-IDF uses only that text at [retrieval.py](../backend/researchlens/retrieval.py#L53), and the CPU reranker does the same at [reranking.py](../backend/researchlens/reranking.py#L88). The metadata is available for citation but unavailable to relevance scoring.

For example, `pmc11768589:p24:w0` contains the Keras/TensorFlow, 8 GB RAM, and GeForce 930MX hardware answer, but does not name heaters or painted surfaces. The question explicitly asks for painted-surface training. This is a real absence of source context in the indexed representation. Its causal effect on ranking requires an experiment.

Start with deterministic `title + section path + passage` retrieval text. Compare it with an optional short, source-grounded study description. The heater article's title is generic, so title alone may not resolve every study reference. Maintain canonical passage text, IDs, and evidence offsets separately from retrieval text; record the new representation and hashes in a new artifact. Apply the chosen representation consistently to lexical search, dense search, and reranking. Adding context consumes tokens, so remeasure token visibility, especially for MiniLM.

### Test a different lexical component before rejecting hybrid retrieval

The current hybrid is **word/bigram TF-IDF cosine plus dense embeddings**, fused by RRF. It is not BM25, BGE-M3's learned sparse retrieval, or BGE-M3 multi-vector retrieval. `HybridRetriever` constructs `TfidfRetriever`; the BGE encoder returns the CLS embedding without computing the sparse or multi-vector heads. Thus the local table does not test all methods commonly described as BGE hybrid retrieval.

The BGE-M3 model card documents dense, sparse, and multi-vector capabilities. It recommends hybrid retrieval followed by reranking and provides a dense-plus-learned-sparse route [4]. BEIR's original cross-domain evaluation found BM25 a robust baseline, with reranking and late-interaction methods strongest on average at greater computation cost [5]. Neither source proves that BM25 or BGE sparse retrieval will beat the current baseline on these four articles.

A bounded comparison should include BM25 alone, BM25 plus the current dense model, and BGE-M3 dense plus its learned sparse scores. Keep the passage representation and evidence labels fixed while comparing lexical methods. Use the same candidate and context limits. Consider multi-vector late interaction after these simpler tests, since it changes storage and scoring more substantially.

### RRF is correct here, but its constant creates a strong overlap preference

Elastic's RRF reference specifies the rank-based formula and explains that a larger rank constant increases the influence of lower-ranked hits; it defaults to 60 [6]. The local implementation matches the weighted form. At equal weights and constant 60:

| Candidate | RRF score |
| --- | ---: |
| Rank 1 in dense, absent from lexical candidates | `1 / 61 = 0.01639` |
| Rank 20 in both lists | `2 / 80 = 0.02500` |
| Rank 40 in both lists | `2 / 100 = 0.02000` |

Consequently, agreement far down both lists can displace a strong dense-only passage. This arithmetic is not an implementation error and does not by itself identify the cause of an individual failure. It explains why adding weaker lexical rankings need not improve top-four results.

The existing grid varied weights and candidate counts while leaving the rank constant at 60. A small predefined comparison of constants such as 10, 20, and 60 is justified. Also consider a score-based convex combination with explicit normalization and development-only weight selection. Bruch, Gai, and Ingber found RRF sensitive to its parameters and found convex score combinations better on their experimental datasets [7]. That result motivates a local comparison; it does not establish a universal ranking of fusion methods.

### Chunk boundaries matter even when tokens fit

The current chunker makes nonoverlapping 180-word windows within paragraphs, retaining neither adjacent paragraph text nor section titles in the embedded input. A window may begin halfway through a sentence. The local visibility diagnostics found no truncation for BGE-M3, Qwen, or the tested reranker pairs, and only eight truncated MiniLM passages. Raising BGE/Qwen token limits therefore does not address the observed baseline inputs.

The absence of truncation does not mean chunks preserve all linguistic context. Anthropic explicitly identifies chunk boundaries, size, and overlap as parameters to evaluate [3]. Late Chunking research describes another way to retain document context by embedding the longer document first, then pooling chunk representations [8]. That procedure relies on contextual token representations and mean pooling. It should not be transplanted into these trained CLS- or last-token-pooled encoders by changing pooling rules without model-specific validation.

Metadata enrichment preserves the existing scoring contract and should come first. A later sentence-boundary or parent/child experiment can retrieve small units and supply relevant surrounding text, with a fixed total context budget. If canonical passage boundaries change, remap and review evidence spans and establish a new comparison protocol; old passage-level scores will no longer be directly comparable. Larger chunks are not automatically better because they dilute precise matches and consume more of the four-slot context budget.

## Recommended order of work

1. Use the existing per-question candidate and evidence diagnostics to identify missing support versus poor selection. For each apparent miss, inspect the retrieved text for valid but unlabeled alternatives. Record findings separately; do not silently revise approved labels to favor a model.
2. Use the completed stronger-reranker study as the comparison baseline. Keep Qwen3-4B dense and BGE-M3 dense as controls, and include the frozen BGE/BGE-reranker20 candidate. Broaden backend reference checks if a later decision depends on full ranking equivalence; the existing reference sample covers only five questions per reranker.
3. Run a small predefined representation study using title/section context, with unchanged canonical passages. Measure all five requested metrics, candidates at 20/40, query-type cohorts, latency, and token visibility.
4. Test query decomposition and coverage-aware four-passage selection on multi-part requests. Keep generation of subquestions separate from the evaluator and preserve the original query as a retrieval route.
5. Test BM25 or BGE learned sparse retrieval and a small RRF-constant/score-fusion comparison. Do not infer from the present TF-IDF results that hybrid retrieval as a whole is ineffective.
6. Freeze the resulting development choice before held-out evaluation. At 36 answerable development cases, the 80% completeness goal needs at least 29 complete cases, five more than Qwen dense or three more than the saved 26/36 reranker result. Fine-tuning should follow a larger, independently split collection of realistic queries and hard negatives, rather than train against this small repeatedly inspected development set.

These are research priorities, not a forecast that any particular change will reach 80%. The strongest local evidence points to passage selection and missing document context. No source establishes a universal complete-evidence@4 expectation for these embedding models.

## Sources

1. Sentence Transformers, official **Retrieve & Re-Rank** guide. [Documentation](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html), [fetched source](https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/examples/sentence_transformer/applications/retrieve_rerank/README.md).
2. Trivedi et al., ACL 2023, **Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions**. [Paper and abstract](https://aclanthology.org/2023.acl-long.557/), [authors' implementation](https://github.com/StonyBrookNLP/ircot).
3. Anthropic, 2024, **Introducing Contextual Retrieval**. [First-party methodology and reported experiments](https://www.anthropic.com/engineering/contextual-retrieval). The cited quality metric is failure at 20 retrieved chunks, not complete evidence at four.
4. BAAI, **BGE-M3 model card**. [Card](https://huggingface.co/BAAI/bge-m3), [fetched raw card](https://huggingface.co/BAAI/bge-m3/raw/main/README.md).
5. Thakur et al., NeurIPS 2021 Datasets and Benchmarks, **BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models**. [Authors' paper and abstract](https://arxiv.org/abs/2104.08663).
6. Elastic, official **Reciprocal rank fusion** reference. [Formula, rank constant, and rank window](https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html).
7. Bruch, Gai, and Ingber, **An Analysis of Fusion Functions for Hybrid Retrieval**, revised 2023. [Authors' paper and abstract](https://arxiv.org/abs/2210.11934), [published DOI](https://doi.org/10.1145/3596512).
8. Gunther et al., **Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models**, revised 2025. [Authors' paper and abstract](https://arxiv.org/abs/2409.04701).

Local evidence definitions and annotation limitations are documented in [evaluation/labels/README.md](../evaluation/labels/README.md). Source fetching used primary websites and official repository files. Paper-specific numerical statements above are limited to the fetched abstracts or first-party methodology reports; no independent replication of their experiments is claimed.
