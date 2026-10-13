# Readable formulas development results

These are provisional results on unreviewed candidate span mappings. All 36 answerable development cases and 14 unscored negatives ran locally. No generation, paid API call or held-out retrieval ran.

Reference recall is mean legacy reference-ID recall; hit and MRR use evidence passage IDs within supplied context, as in the existing study. Complete uses visible quote spans, all groups and every AND fragment. Character budgets use exact provider serialization. Candidate reference IDs are retained, validated at the same source locations; legacy reference recall does not establish unchanged window content.

## Five retrieval targets

Thresholds are reference recall 80%, evidence hit 90%, complete evidence 80%, both sources 90% of nine cross-document cases, and MRR 0.65.

| Model | Context | Corpus | Reference recall | Evidence hit /36 | Complete /36 | Both sources /9 | MRR | Targets met |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| tfidf | 4 | canonical | 47.6% | 25 | 15 | 8 | 0.558 | 0/5 |
| tfidf | 4 | candidate | 48.8% | 25 | 15 | 8 | 0.562 | 0/5 |
| tfidf | 12000 | canonical | 70.3% | 30 | 26 | 9 | 0.583 | 1/5 |
| tfidf | 12000 | candidate | 70.3% | 30 | 26 | 9 | 0.587 | 1/5 |
| tfidf | 16000 | canonical | 73.9% | 31 | 26 | 9 | 0.585 | 1/5 |
| tfidf | 16000 | candidate | 73.9% | 31 | 26 | 9 | 0.588 | 1/5 |
| bge-m3 | 4 | canonical | 61.4% | 30 | 22 | 7 | 0.593 | 0/5 |
| bge-m3 | 4 | candidate | 61.2% | 29 | 21 | 7 | 0.588 | 0/5 |
| bge-m3 | 12000 | canonical | 82.1% | 34 | 29 | 9 | 0.609 | 4/5 |
| bge-m3 | 12000 | candidate | 82.1% | 34 | 28 | 9 | 0.610 | 3/5 |
| bge-m3 | 16000 | canonical | 85.2% | 36 | 30 | 9 | 0.614 | 4/5 |
| bge-m3 | 16000 | candidate | 85.8% | 36 | 30 | 9 | 0.614 | 4/5 |
| qwen3-4b | 4 | canonical | 69.3% | 32 | 24 | 6 | 0.715 | 1/5 |
| qwen3-4b | 4 | candidate | 69.9% | 32 | 24 | 6 | 0.731 | 1/5 |
| qwen3-4b | 12000 | canonical | 85.2% | 35 | 30 | 9 | 0.725 | 5/5 |
| qwen3-4b | 12000 | candidate | 85.2% | 35 | 29 | 9 | 0.741 | 5/5 |
| qwen3-4b | 16000 | canonical | 88.6% | 35 | 33 | 9 | 0.725 | 5/5 |
| qwen3-4b | 16000 | candidate | 88.6% | 35 | 33 | 9 | 0.741 | 5/5 |

## Paired exact McNemar tests

Two-sided exact binomial tests. Gain/loss counts are paired question changes. Complete and hit use 36 cases, both-source tests use nine. Reference recall and MRR are continuous and have no McNemar test. No multiple-comparison correction; these are development diagnostics.

| Model | Context | Outcome | Gains | Losses | p |
| --- | --- | --- | ---: | ---: | ---: |
| tfidf | 4 | complete | 0 | 0 | 1 |
| tfidf | 4 | evidence_hit | 0 | 0 | 1 |
| tfidf | 4 | both_sources | 0 | 0 | 1 |
| tfidf | 4 | complete_asked_groups | 1 | 0 | 1 |
| tfidf | 12000 | complete | 0 | 0 | 1 |
| tfidf | 12000 | evidence_hit | 0 | 0 | 1 |
| tfidf | 12000 | both_sources | 0 | 0 | 1 |
| tfidf | 12000 | complete_asked_groups | 0 | 0 | 1 |
| tfidf | 16000 | complete | 0 | 0 | 1 |
| tfidf | 16000 | evidence_hit | 0 | 0 | 1 |
| tfidf | 16000 | both_sources | 0 | 0 | 1 |
| tfidf | 16000 | complete_asked_groups | 0 | 0 | 1 |
| bge-m3 | 4 | complete | 0 | 1 | 1 |
| bge-m3 | 4 | evidence_hit | 0 | 1 | 1 |
| bge-m3 | 4 | both_sources | 0 | 0 | 1 |
| bge-m3 | 4 | complete_asked_groups | 0 | 1 | 1 |
| bge-m3 | 12000 | complete | 0 | 1 | 1 |
| bge-m3 | 12000 | evidence_hit | 0 | 0 | 1 |
| bge-m3 | 12000 | both_sources | 0 | 0 | 1 |
| bge-m3 | 12000 | complete_asked_groups | 0 | 0 | 1 |
| bge-m3 | 16000 | complete | 0 | 0 | 1 |
| bge-m3 | 16000 | evidence_hit | 0 | 0 | 1 |
| bge-m3 | 16000 | both_sources | 0 | 0 | 1 |
| bge-m3 | 16000 | complete_asked_groups | 0 | 0 | 1 |
| qwen3-4b | 4 | complete | 0 | 0 | 1 |
| qwen3-4b | 4 | evidence_hit | 0 | 0 | 1 |
| qwen3-4b | 4 | both_sources | 0 | 0 | 1 |
| qwen3-4b | 4 | complete_asked_groups | 0 | 0 | 1 |
| qwen3-4b | 12000 | complete | 0 | 1 | 1 |
| qwen3-4b | 12000 | evidence_hit | 0 | 0 | 1 |
| qwen3-4b | 12000 | both_sources | 0 | 0 | 1 |
| qwen3-4b | 12000 | complete_asked_groups | 0 | 0 | 1 |
| qwen3-4b | 16000 | complete | 0 | 0 | 1 |
| qwen3-4b | 16000 | evidence_hit | 0 | 0 | 1 |
| qwen3-4b | 16000 | both_sources | 0 | 0 | 1 |
| qwen3-4b | 16000 | complete_asked_groups | 0 | 0 | 1 |

## Per-question changes

Only changes in recall, hit, complete, source coverage, MRR or group coverage are listed below. The JSON summary retains all answerable question pairs. Neighborhood is listed even when scores do not change.

| Model | Context | Question | Recall old/new | Hit old/new | Complete old/new | Groups old/new | MRR old/new | Missing groups old/new |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf | 4 | tech-aw-ssim-combination | 0.500/0.750 | True/True | True/True | 1.000/1.000 | 1.000/1.000 | none / none |
| tfidf | 4 | tech-adga-shapes | 0.667/0.667 | True/True | True/True | 1.000/1.000 | 0.500/1.000 | none / none |
| tfidf | 4 | tech-changing-neighborhood | 0.500/0.667 | True/True | False/False | 0.200/0.800 | 0.500/0.500 | part-1, part-2, part-3, fixed-footprint / fixed-footprint |
| tfidf | 4 | tech-compare-data-expansion | 0.500/0.500 | True/True | False/False | 0.500/0.500 | 0.500/0.333 | part-1 / part-1 |
| tfidf | 4 | tech-compare-network-inputs | 0.250/0.250 | True/True | False/False | 0.500/0.500 | 0.500/0.333 | part-1 / part-1 |
| tfidf | 12000 | tech-glass-exact | 1.000/1.000 | True/True | True/True | 1.000/1.000 | 0.200/0.167 | none / none |
| tfidf | 12000 | tech-adga-shapes | 1.000/1.000 | True/True | True/True | 1.000/1.000 | 0.500/1.000 | none / none |
| tfidf | 12000 | tech-changing-neighborhood | 0.833/0.833 | True/True | False/False | 0.800/0.800 | 0.500/0.500 | fixed-footprint / fixed-footprint |
| tfidf | 12000 | tech-compare-data-expansion | 1.000/1.000 | True/True | True/True | 1.000/1.000 | 0.500/0.333 | none / none |
| tfidf | 12000 | tech-compare-network-inputs | 0.500/0.500 | True/True | True/True | 1.000/1.000 | 0.500/0.333 | none / none |
| tfidf | 16000 | tech-glass-exact | 1.000/1.000 | True/True | True/True | 1.000/1.000 | 0.200/0.167 | none / none |
| tfidf | 16000 | tech-adga-shapes | 1.000/1.000 | True/True | True/True | 1.000/1.000 | 0.500/1.000 | none / none |
| tfidf | 16000 | tech-changing-neighborhood | 0.833/0.833 | True/True | False/False | 0.800/0.800 | 0.500/0.500 | fixed-footprint / fixed-footprint |
| tfidf | 16000 | tech-compare-data-expansion | 1.000/1.000 | True/True | True/True | 1.000/1.000 | 0.500/0.333 | none / none |
| tfidf | 16000 | tech-compare-network-inputs | 0.500/0.500 | True/True | True/True | 1.000/1.000 | 0.500/0.333 | none / none |
| bge-m3 | 4 | tech-wafer-exact | 0.500/0.500 | True/True | False/False | 0.000/0.000 | 0.250/0.500 | part-1, efficiency-scope / part-1, efficiency-scope |
| bge-m3 | 4 | tech-aw-ssim-combination | 0.500/0.750 | True/True | True/True | 1.000/1.000 | 1.000/1.000 | none / none |
| bge-m3 | 4 | tech-adga-shapes | 0.667/0.333 | True/False | True/False | 1.000/0.000 | 0.500/0.000 | none / part-1, part-2, part-3, part-4 |
| bge-m3 | 4 | tech-stable-camera | 1.000/1.000 | True/True | True/True | 1.000/1.000 | 0.250/0.333 | none / none |
| bge-m3 | 4 | tech-changing-neighborhood | 0.167/0.167 | False/False | False/False | 0.000/0.000 | 0.000/0.000 | part-1, part-2, part-3, gaussian-spread, fixed-footprint / part-1, part-2, part-3, gaussian-spread, fixed-footprint |
| bge-m3 | 12000 | tech-wafer-exact | 1.000/1.000 | True/True | True/False | 1.000/0.500 | 0.250/0.500 | none / efficiency-scope |
| bge-m3 | 12000 | tech-adga-shapes | 0.667/0.667 | True/True | True/True | 1.000/1.000 | 0.500/0.200 | none / none |
| bge-m3 | 12000 | tech-stable-camera | 1.000/1.000 | True/True | True/True | 1.000/1.000 | 0.250/0.333 | none / none |
| bge-m3 | 12000 | tech-moving-signal-addition | 0.333/0.333 | True/True | False/False | 0.500/0.500 | 0.167/0.143 | part-1 / part-1 |
| bge-m3 | 12000 | tech-changing-neighborhood | 0.333/0.333 | False/False | False/False | 0.000/0.000 | 0.000/0.000 | part-1, part-2, part-3, gaussian-spread, fixed-footprint / part-1, part-2, part-3, gaussian-spread, fixed-footprint |
| bge-m3 | 16000 | tech-wafer-exact | 1.000/1.000 | True/True | True/True | 1.000/1.000 | 0.250/0.500 | none / none |
| bge-m3 | 16000 | tech-autoencoder-exact | 0.800/1.000 | True/True | True/True | 1.000/1.000 | 1.000/1.000 | none / none |
| bge-m3 | 16000 | tech-adga-shapes | 0.667/0.667 | True/True | True/True | 1.000/1.000 | 0.500/0.200 | none / none |
| bge-m3 | 16000 | tech-stable-camera | 1.000/1.000 | True/True | True/True | 1.000/1.000 | 0.250/0.333 | none / none |
| bge-m3 | 16000 | tech-moving-signal-addition | 0.333/0.333 | True/True | False/False | 0.500/0.500 | 0.167/0.143 | part-1 / part-1 |
| bge-m3 | 16000 | tech-changing-neighborhood | 0.667/0.667 | True/True | False/False | 0.000/0.000 | 0.091/0.083 | part-1, part-2, part-3, gaussian-spread, fixed-footprint / part-1, part-2, part-3, gaussian-spread, fixed-footprint |
| qwen3-4b | 4 | tech-wafer-exact | 0.500/0.500 | True/True | False/False | 0.500/0.500 | 0.500/1.000 | efficiency-scope / efficiency-scope |
| qwen3-4b | 4 | tech-aw-ssim-combination | 0.500/0.750 | True/True | True/True | 1.000/1.000 | 1.000/1.000 | none / none |
| qwen3-4b | 4 | tech-adga-shapes | 0.667/0.667 | True/True | True/True | 1.000/1.000 | 0.250/0.333 | none / none |
| qwen3-4b | 4 | tech-changing-neighborhood | 0.167/0.167 | False/False | False/False | 0.000/0.000 | 0.000/0.000 | part-1, part-2, part-3, gaussian-spread, fixed-footprint / part-1, part-2, part-3, gaussian-spread, fixed-footprint |
| qwen3-4b | 12000 | tech-wafer-exact | 1.000/1.000 | True/True | False/False | 0.500/0.500 | 0.500/1.000 | efficiency-scope / efficiency-scope |
| qwen3-4b | 12000 | tech-adga-shapes | 0.667/0.667 | True/True | True/True | 1.000/1.000 | 0.250/0.333 | none / none |
| qwen3-4b | 12000 | tech-too-many-shortcuts | 1.000/1.000 | True/True | True/False | 1.000/0.500 | 0.250/0.250 | none / residual-purpose |
| qwen3-4b | 12000 | tech-changing-neighborhood | 0.500/0.500 | False/False | False/False | 0.000/0.000 | 0.000/0.000 | part-1, part-2, part-3, gaussian-spread, fixed-footprint / part-1, part-2, part-3, gaussian-spread, fixed-footprint |
| qwen3-4b | 16000 | tech-wafer-exact | 1.000/1.000 | True/True | False/False | 0.500/0.500 | 0.500/1.000 | efficiency-scope / efficiency-scope |
| qwen3-4b | 16000 | tech-adga-shapes | 0.667/0.667 | True/True | True/True | 1.000/1.000 | 0.250/0.333 | none / none |
| qwen3-4b | 16000 | tech-changing-neighborhood | 0.500/0.500 | False/False | False/False | 0.000/0.000 | 0.000/0.000 | part-1, part-2, part-3, gaussian-spread, fixed-footprint / part-1, part-2, part-3, gaussian-spread, fixed-footprint |

## Neighborhood ranks in the top 40

- tfidf: canonical {'pmc11121878:p30:w0': 2, 'pmc11121878:p31:w0': 5, 'pmc11121878:p29:w0': 22}; candidate {'pmc11121878:p30:w0': 2, 'pmc11121878:p31:w0': 3, 'pmc11121878:p29:w0': 21, 'pmc11121878:p32:w0': 38}.
- bge-m3: canonical {'pmc11121878:p31:w0': 11}; candidate {'pmc11121878:p31:w0': 12}.
- qwen3-4b: canonical {'pmc11121878:p31:w0': 23}; candidate {'pmc11121878:p31:w0': 20}.

## Approval boundary

Canonical documents, manifest, hashes, approved labels and frozen held-out dataset remain unchanged. Corpus adoption, label approval and a new held-out dataset version are owner decisions. Retrieval coverage does not establish scientific fidelity, generated-answer quality or held-out performance.
