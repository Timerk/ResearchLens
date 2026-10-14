# Adopted readable formulas retrieval, 2026-10-14

The owner approved and adopted the corpus, development spans and held-out reference migration on 2026-10-14. All four application tier indexes were rebuilt with fresh vectors against this corpus. TF-IDF, BGE-M3 dense and Qwen3-4B dense ran on all 50 development questions through the existing runner at 40 candidates and `--context-budgets 4 12000 16000`. The 14 negatives are unscored. No held-out retrieval, answer generation or paid API call ran.

Five thresholds: mean reference-ID recall ≥80%, evidence hit ≥90%, all-group complete evidence ≥80%, both sources ≥90% of nine cross-document questions, and MRR ≥0.65. Complete evidence uses visible quote spans, including every required AND fragment. Reference recall retains the legacy passage-ID definition.

| Model | Context | Reference recall | Hit /36 | Complete /36 | Both sources /9 | MRR | Targets met |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| tfidf | 4 | 48.8% | 25 | 15 | 8 | 0.562 | 0/5 |
| tfidf | 12000 | 70.3% | 30 | 26 | 9 | 0.587 | 1/5 |
| tfidf | 16000 | 73.9% | 31 | 26 | 9 | 0.588 | 1/5 |
| bge-m3 | 4 | 61.2% | 29 | 21 | 7 | 0.588 | 0/5 |
| bge-m3 | 12000 | 82.1% | 34 | 28 | 9 | 0.610 | 3/5 |
| bge-m3 | 16000 | 85.8% | 36 | 30 | 9 | 0.614 | 4/5 |
| qwen3-4b | 4 | 69.9% | 32 | 24 | 6 | 0.731 | 1/5 |
| qwen3-4b | 12000 | 85.2% | 35 | 29 | 9 | 0.741 | 5/5 |
| qwen3-4b | 16000 | 88.6% | 35 | 33 | 9 | 0.741 | 5/5 |

## Tier artifacts

| Tier | Model | Passages | Corpus pin valid |
| --- | --- | ---: | --- |
| minimal | TF-IDF | 207 | yes |
| light | Qwen/Qwen3-Embedding-0.6B | 207 | yes |
| standard | BAAI/bge-m3 | 207 | yes |
| full | Qwen/Qwen3-Embedding-4B | 207 | yes |

Qwen retains all five targets at 12k and 16k. Scores reproduce the phase-1 candidate totals with approved labels and newly encoded canonical indexes. `tech-changing-neighborhood` remains incomplete at every tested context. TF-IDF has 80% group coverage but misses the split fixed-footprint evidence; BGE and Qwen miss other required groups.

The full per-question records and validated tier manifests remain in ignored `evaluation/runs/readable-formulas-adopted-2026-10-14`. The JSON summary includes all answerable question scores, current pins and artifact/run hashes. The light tier was rebuilt and validated but its retrieval quality was not remeasured.

The pre-rendering paid answer-quality study remains historical evidence with its original pins. These retrieval-only measurements do not update answer correctness, citation support or held-out performance claims.
