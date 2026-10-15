# One-time held-out retrieval results

Qwen3-4B at both 12k and 16k passes four of the five literal targets. Its passage recall@4 is 77.6%, below 80%. Complete evidence is 21/26, or 80.8%; context evidence hit is 26/26; both documents are present for 7/7 cross-document cases; MRR@4 is 0.798. BGE-M3 at 16k passes three targets and misses recall@4 and complete evidence. TF-IDF passes MRR@4 alone. No configuration passes all five literal targets.

The predeclared whole-context diagnostic gives Qwen recall of 91.0% at 12k and 92.0% at 16k. With the historical development convention of whole-context recall and MRR, both Qwen contexts reach all five point thresholds. This does not change the recall@4 miss.

## Protocol and execution

The [pre-registration](held-out-preregistration.md) was committed as `227fea2` before any held-out search. The general offline reference scorer and synthetic tests were committed as `9a176c5` before retrieval. All runs record that commit with `dirty=false`. Main base was `e57ffb2`, after PR #15.

The frozen adopted dataset version is `4-readable-formulas-frozen`. Only metadata was inspected before registration. There were 36 cases, 26 answerable and 10 unanswerable. The 26 positives contain 54 distinct within-case reference IDs and seven cross-document cases. All ten negatives, including five with related references, are excluded from every quality metric. Their records remain in the archives; no abstention performance was evaluated.

TF-IDF retrieved four candidates. BGE-M3 and Qwen each retrieved 40. The two Qwen contexts share its single ranking, as registered. This was 108 searches across three backend runs and four frozen context configurations. Every case had one retrieval attempt, no warmups and no repeats. There were zero technical failures, zero retries and zero paid API calls. No answers were generated. Datasets, labels and corpus were unchanged. Local adopted artifacts were copied and validated against the canonical 207 passages. Encoder and runtime settings match the adopted development runs; there was no automatic fallback.

## Literal target results and uncertainty

Recall@4 is the mean of per-case reference fractions in the first four ranked passages. MRR@4 uses the first referenced ID at rank 1-4, otherwise zero. Context hit requires at least one referenced ID with nonempty supplied text. Complete evidence requires every referenced ID with nonempty supplied text. Both-document success requires all expected documents in the supplied context, without requiring a referenced passage from each. Duplicate references count once.

All intervals are 95%. Binary rates use exact Clopper-Pearson intervals. Macro recall and MRR use the pre-registered distribution-free Hoeffding interval for bounded means; Clopper-Pearson is inapplicable to fractional case scores. Decisions compare unrounded point estimates with thresholds.

| Configuration | Metric | Estimate | Denominator | 95% interval | Target | Result |
| --- | --- | ---: | ---: | --- | ---: | --- |
| tfidf-4 | Passage recall@4 | 62.0% | 26 | 35.4%-88.6% | 80.0% | MISS |
| tfidf-4 | Context evidence hit | 76.9% (20/26) | 26 | 56.4%-91.0% | 90.0% | MISS |
| tfidf-4 | Complete evidence | 50.0% (13/26) | 26 | 29.9%-70.1% | 80.0% | MISS |
| tfidf-4 | Both documents | 85.7% (6/7) | 7 | 42.1%-99.6% | 90.0% | MISS |
| tfidf-4 | MRR@4 | 0.679 | 26 | 0.413-0.946 | 0.65 | PASS |
| bge-m3-16k | Passage recall@4 | 73.8% | 26 | 47.2%-100.0% | 80.0% | MISS |
| bge-m3-16k | Context evidence hit | 100.0% (26/26) | 26 | 86.8%-100.0% | 90.0% | PASS |
| bge-m3-16k | Complete evidence | 73.1% (19/26) | 26 | 52.2%-88.4% | 80.0% | MISS |
| bge-m3-16k | Both documents | 100.0% (7/7) | 7 | 59.0%-100.0% | 90.0% | PASS |
| bge-m3-16k | MRR@4 | 0.824 | 26 | 0.557-1.000 | 0.65 | PASS |
| qwen3-4b-12k | Passage recall@4 | 77.6% | 26 | 51.0%-100.0% | 80.0% | MISS |
| qwen3-4b-12k | Context evidence hit | 100.0% (26/26) | 26 | 86.8%-100.0% | 90.0% | PASS |
| qwen3-4b-12k | Complete evidence | 80.8% (21/26) | 26 | 60.6%-93.4% | 80.0% | PASS |
| qwen3-4b-12k | Both documents | 100.0% (7/7) | 7 | 59.0%-100.0% | 90.0% | PASS |
| qwen3-4b-12k | MRR@4 | 0.798 | 26 | 0.532-1.000 | 0.65 | PASS |
| qwen3-4b-16k | Passage recall@4 | 77.6% | 26 | 51.0%-100.0% | 80.0% | MISS |
| qwen3-4b-16k | Context evidence hit | 100.0% (26/26) | 26 | 86.8%-100.0% | 90.0% | PASS |
| qwen3-4b-16k | Complete evidence | 80.8% (21/26) | 26 | 60.6%-93.4% | 80.0% | PASS |
| qwen3-4b-16k | Both documents | 100.0% (7/7) | 7 | 59.0%-100.0% | 90.0% | PASS |
| qwen3-4b-16k | MRR@4 | 0.798 | 26 | 0.532-1.000 | 0.65 | PASS |

The intervals are wide. A point-target pass does not establish the same population success rate. Passage presence cannot verify visible supporting spans, claim correctness, preserved qualifications or answer quality.

## Predeclared context and micro diagnostics

| Configuration | Whole-context recall | 95% Hoeffding interval | Whole-context MRR | 95% Hoeffding interval | Micro recall@4 | 95% Clopper-Pearson interval |
| --- | ---: | --- | ---: | --- | ---: | --- |
| tfidf-4 | 62.0% | 35.4%-88.6% | 0.679 | 0.413-0.946 | 28/54 (51.9%) | 37.8%-65.7% |
| bge-m3-16k | 90.7% | 64.1%-100.0% | 0.824 | 0.557-1.000 | 33/54 (61.1%) | 46.9%-74.1% |
| qwen3-4b-12k | 91.0% | 64.4%-100.0% | 0.806 | 0.539-1.000 | 36/54 (66.7%) | 52.5%-78.9% |
| qwen3-4b-16k | 92.0% | 65.4%-100.0% | 0.806 | 0.539-1.000 | 36/54 (66.7%) | 52.5%-78.9% |

Micro recall treats the 54 reference occurrences as trials. References within a question are dependent, so its nominal binomial interval is a diagnostic, not an interval for the macro target.

## Paired comparisons against TF-IDF

Complete evidence is the primary paired endpoint. Context hit and both documents are additional predeclared binary endpoints. Two-sided exact McNemar uses gain/loss discordances; Holm adjustment covers all nine tests.

| Candidate | Metric | Paired cases | Gains | Losses | Exact p | Holm p |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| bge-m3-16k | Complete evidence | 26 | 7 | 1 | 0.070312 | 0.281250 |
| bge-m3-16k | Context evidence hit | 26 | 6 | 0 | 0.031250 | 0.218750 |
| bge-m3-16k | Both documents | 7 | 1 | 0 | 1.000000 | 1.000000 |
| qwen3-4b-12k | Complete evidence | 26 | 9 | 1 | 0.021484 | 0.193359 |
| qwen3-4b-12k | Context evidence hit | 26 | 6 | 0 | 0.031250 | 0.218750 |
| qwen3-4b-12k | Both documents | 7 | 1 | 0 | 1.000000 | 1.000000 |
| qwen3-4b-16k | Complete evidence | 26 | 9 | 1 | 0.021484 | 0.193359 |
| qwen3-4b-16k | Context evidence hit | 26 | 6 | 0 | 0.031250 | 0.218750 |
| qwen3-4b-16k | Both documents | 7 | 1 | 0 | 1.000000 | 1.000000 |

No paired comparison is significant at 5% after the planned Holm adjustment. The measured differences do not establish model superiority.

## Adopted development versus held-out

Development used 36 answerable cases and nine cross-document cases. The following comparison preserves the adopted report's whole-context recall and MRR convention; it is separate from the literal target table.

| Configuration | Split | Context reference recall | Context hit | Complete evidence | Both documents | Context MRR |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| tfidf-4 | Development | 48.8% | 25/36 | 15/36 | 8/9 | 0.562 |
| tfidf-4 | Held-out | 62.0% | 20/26 | 13/26 | 6/7 | 0.679 |
| bge-m3-16k | Development | 85.8% | 36/36 | 30/36 | 9/9 | 0.614 |
| bge-m3-16k | Held-out | 90.7% | 26/26 | 19/26 | 7/7 | 0.824 |
| qwen3-4b-12k | Development | 85.2% | 35/36 | 29/36 | 9/9 | 0.741 |
| qwen3-4b-12k | Held-out | 91.0% | 26/26 | 21/26 | 7/7 | 0.806 |
| qwen3-4b-16k | Development | 88.6% | 35/36 | 33/36 | 9/9 | 0.741 |
| qwen3-4b-16k | Held-out | 92.0% | 26/26 | 21/26 | 7/7 | 0.806 |

Development completeness checked every approved OR/AND evidence group against visible quote spans. Held-out has passage references only and requires all referenced IDs, with no span or group labels. Its evidence hit and MRR also use reference IDs rather than labeled evidence relevance. These completeness, hit and MRR comparisons are approximate. Context reference recall and document presence use matching passage/source definitions and context budgets, but the populations differ. Development's 12k/16k recall and MRR include ranks beyond four, so they cannot serve as direct recall@4 or MRR@4 comparisons. No additional development or held-out retrieval was performed to harmonize metrics.

## Artifacts and validation

The [summary JSON](https://github.com/Timerk/ResearchLens/blob/archive/evaluation-2026-10/docs/held-out-results.json) (archived) contains all metric estimates, intervals, target decisions, paired counts, p-values, development values and provenance. Full rankings, question-bearing run outputs and per-case context selections remain in ignored `evaluation/runs/held-out-confirmation-2026-10-14/`.

| Backend | Run ID | Archived run |
| --- | --- | --- |
| tfidf-4 | `0c801b97-684a-4722-998d-6a17954bac5f` | `evaluation/runs/held-out-confirmation-2026-10-14/tfidf/run.json` |
| bge-m3-16k | `1ac93d53-a05f-4b56-9193-8bd1465318ae` | `evaluation/runs/held-out-confirmation-2026-10-14/bge-m3/run.json` |
| qwen3-4b-12k | `d10231d6-51ed-43d2-8a28-ed1453a0b47b` | `evaluation/runs/held-out-confirmation-2026-10-14/qwen3-4b/run.json` |

The Qwen16k profile refers to the same Qwen run. Archive hashes, dataset/corpus pins, installed versions, execution parameters and scorer source hash are in the summary. The dataset LF hash is `920f1415d14d974ce489e91386227d3f306837f22944958763d8235495ea9312`; the corpus hash is `f293a02c7afaf38f06ec17d6443f7289fd3a7d3091cf11cf0d4f865ee0e3a675`.

Ruff passed and all 280 backend tests passed, including the general reference scorer tests. No dataset, label, corpus or application setting changed. This one-time evaluation is complete; do not rerun held-out retrieval. `researchlens.reference_evaluation` can score existing archived outputs offline without any search.
