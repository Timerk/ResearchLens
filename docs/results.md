# Results

This page tells the evaluation story in order. Each step links to the document that
holds the full tables, intervals and provenance. All numbers come from those committed
documents. Development results use 50 owner-approved questions, of which 36 are
answerable and 14 are negatives. The held-out set has 36 questions, 26 of them
answerable.

The retrieval studies use five targets. Reference recall must reach 80%, evidence hit
90%, complete evidence 80%, both sources 90% of the nine cross-document questions,
and MRR 0.65.

## 1. The problem

At the application default of four passages, retrieval missed the targets. Across
nine CPU model and hybrid configurations, the best was Qwen3-4B dense. It supplied
complete evidence for 24 of 36 answerable development questions.
Details: [approved CPU comparison](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/approved-model-comparison.md) (archived).

## 2. Root cause: the passage cap

Retrieval was not the binding constraint. The candidate rankings already contained
complete approved evidence for 31 to 34 of the 36 answerable questions. The answer
provider received only four short passages, about 3,000 of its 16,000 allowed
characters. Weighted fusion, reranking, diversity and query splitting did not fix this.
Details: [retrieval research index](retrieval-research.md) and
[selection diagnostics](https://github.com/Timerk/ResearchLens/blob/research/retrieval-2026-10/docs/selection-diagnostics.md) (archived).

## 3. A character budget instead of a passage count

Filling a character budget in ranked order closed the gap. On the corpus at the time,
Qwen3-4B dense at 12,000 characters supplied complete evidence for 30 of 36 questions
and met all five targets at 12k and 16k. TF-IDF reached 26 of 36 even at 16,000
characters. These are context evidence scores. They do not measure answer quality.
Details: [context budget study](context-budget.md).

## 4. Hardware tiers

Qwen3-4B peaked at 8.1 GiB of RAM on the CPU, which many machines cannot spare. The
backend can pick a tier from the available RAM: full uses Qwen3-4B with 12,000
characters and needs 10 GiB, standard uses BGE-M3 and needs 5 GiB, light uses
Qwen3-0.6B and needs 2.5 GiB, and minimal uses TF-IDF and needs 0.25 GiB. If a tier
fails to load, auto mode falls back to the next one.
Details: [hardware tiers](embeddings.md#hardware-retrieval-tiers).

## 5. Readable formulas

The original extraction replaced every MathML formula with `[formula omitted]`. The
new renderer restores 122 formulas as readable text and keeps four unsupported ones
as placeholders. Because passage text changed, the owner reviewed and approved the
remapped evidence spans and held-out references before adoption. After all tier
indexes were rebuilt, Qwen3-4B still met all five development targets, with complete
evidence for 29 of 36 questions at 12k and 33 of 36 at 16k, and MRR 0.741.
Details: [proposal](formula-rendering-proposal.md),
[remapping review](formula-remapping-review.md) and
[adopted results](formula-adoption-results.md).

## 6. Held-out confirmation

The held-out protocol was committed in `227fea2` before any held-out search, and the
retrieval ran once. Qwen3-4B at 12k and 16k passed four of the five strict targets.
Its passage recall@4 was 77.6%, below the 80% target, and complete evidence was 21 of
26. Under the whole-context convention used in development, Qwen recall was 91.0% at
12k and 92.0% at 16k, and both contexts reached all five thresholds. After Holm
adjustment, no paired comparison against TF-IDF was significant at 5%.
Details: [pre-registration](held-out-preregistration.md) and
[held-out results](held-out-results.md).

## 7. Answer quality

The last step measured generated answers on the development questions. The owner and
Codex independently graded 60 blind judge items, split into a calibration half and a
sealed validation half. The judge was frozen before anyone opened the validation half.
On validation, it passed the reliability bar for required claims and abstention only.
Qualification, citation and forbidden-claim judgments stay uncertified.

| Configuration | Complete required claims /36 | False abstentions /36 |
| --- | ---: | ---: |
| TF-IDF, four passages | 19 | 14 |
| Qwen3-4B, four passages | 26 | 7 |
| Qwen3-4B, 12k characters | 27 | 3 |
| Qwen3-4B, 16k characters | 32 | 1 |
| BGE-M3, 16k characters | 32 | 0 |

The registered primary comparison, Qwen 12k against Qwen four passages, had four gains
and three losses, with exact McNemar p=1.0. It failed the decision rule, so the
application defaults stay unchanged. Qwen 16k against four passages had six gains and
no losses, with nominal p=0.03125. That comparison is secondary and descriptive. All
449 paid calls in this phase cost $0.2469 at the supplied rates, under a shared $3 cap.
Details: [answer-quality report](answer-quality.md).

## What did not change

Without a tier, the application still uses TF-IDF with four passages. The opt-in tiers
keep their existing character budgets. None of the steps above edited the approved
datasets, the evidence labels or the corpus outside the owner-approved formula
adoption.

## Limits

- The samples are small. Intervals in the linked documents are wide, and 36 answerable
  development questions cannot establish a population success rate.
- Most tuning used the development set. The held-out set ran once and missed one
  strict target.
- The judge is unreliable for qualifications, citation support and forbidden claims.
- The corpus has four papers. Results may not transfer to larger or different
  collections.
