# Retrieval evaluation audit, 2026-10-02

The supplied 41.7% to 66.7% figures are **complete evidence rates**, each measured
over 36 answerable development questions. They are not passage recall@4 or generic
embedding benchmark scores. Four papers produce 204 passages. The development set
contains 14 exact terminology, 13 paraphrase, nine cross-document and 14 negative
questions. Negatives are excluded from positive retrieval metrics.

This audit reads saved runs, replays their scores with the current implementation,
and reruns TF-IDF. It does not download or execute embedding models, run held-out
questions, change labels, or alter application code. No repository GLOSSARY.md, ADR
or on-disk AGENTS.md was found. The user-supplied AGENTS instructions apply. RTK
was unavailable, so diagnosis used raw commands under the supplied debugging exception.

## Verified metric interpretation

`backend/researchlens/evaluation_evidence.py:242` implements the scoring contract.
Its `passage_recall` denominator is the original question's reference passage list.
Its MRR and first-evidence hit use the union of passages in the separately approved
evidence groups. Complete evidence requires all groups, accepting OR alternatives
and requiring all spans of an AND alternative. These are different measures.

| Configuration | Reference passage recall@4 | Any annotated evidence passage /36 | Complete /36 | Both sources on cross-document /9 | MRR@4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| TF-IDF | 47.6% | 25, 69.4% | 15, 41.7% | 8, 88.9% | 0.558 |
| MiniLM dense | 50.1% | 27, 75.0% | 17, 47.2% | 7, 77.8% | 0.544 |
| MiniLM hybrid | 57.5% | 30, 83.3% | 18, 50.0% | 7, 77.8% | 0.653 |
| BGE-M3 dense | 61.4% | 30, 83.3% | 22, 61.1% | 7, 77.8% | 0.593 |
| BGE-M3 hybrid | 58.3% | 28, 77.8% | 21, 58.3% | 8, 88.9% | 0.632 |
| Qwen3-0.6B dense | 53.5% | 26, 72.2% | 18, 50.0% | 6, 66.7% | 0.542 |
| Qwen3-0.6B hybrid | 54.6% | 27, 75.0% | 18, 50.0% | 7, 77.8% | 0.630 |
| Qwen3-4B dense | 69.3% | 32, 88.9% | 24, 66.7% | 6, 66.7% | 0.715 |
| Qwen3-4B hybrid | 59.0% | 29, 80.6% | 21, 58.3% | 9, 100% | 0.678 |

Source: the nine actual limit-four runs under
`evaluation/runs/approved-models-2026-10-01-k4/`. The tracked archive is
[approved-model-comparison-results.json](approved-model-comparison-results.json).
All 450 per-question metrics were recomputed and matched exactly.

The first-hit definition can count a passage supplying only part of an AND
alternative. BGE-M3 dense has one such case, `tech-wafer-exact`. MiniLM hybrid has
one, `tech-changing-neighborhood`. Their counts of questions with at least one
fully satisfied evidence group are 29 rather than 30. Qwen3-4B dense has no such
difference. Define which interpretation the 90% first-evidence target intends.

For Qwen3-4B dense, reaching the targets means:

- Complete evidence needs 29/36, five more complete cases than the current 24.
- At least one evidence passage needs 33/36, one more than the current 32.
- Both source documents needs 9/9, three more than the current six. Eight of nine
  is 88.9%, below 90%. Mean source recall is a different measure.
- MRR already exceeds 0.65. MiniLM hybrid and Qwen3-4B hybrid also meet this target.

The reference-list recall convention can penalize successful retrieval. Qwen3-4B
has complete evidence for `tech-painted-exact` with only 40% reference recall, and
for `tech-imagenet-initialization` with 33.3%. Approved OR alternatives make this
possible. `tech-compare-fusion` lists 13 reference passages, so its reference
recall@4 cannot exceed 4/13, although two suitable passages can supply every
approved evidence group. Four questions have more than four listed references.
The aggregate best possible reference recall@4 is 96.04%, so an 80% mean target
is mathematically feasible. Do not interpret that metric as the fraction of facts
supported. This is a documented metric convention, not a verified implementation bug.

## Where the missing evidence occurs

The current `minimal_supports` and `analyze_run` functions replay the existing
label-only analysis without changing retrieval. See
`backend/researchlens/retrieval_analysis.py:21` and `:77`.

| Saved limit-40 run | Complete at four | Complete support in candidates, poor ordering | Missing candidate support |
| --- | ---: | ---: | ---: |
| Qwen3-4B dense | 24 | 10 | 2 |
| BGE-M3 dense | 22 | 11 | 3 |
| Qwen3-4B equal hybrid, 40 candidates per component | 21 | 14 | 1 |
| BGE-M3 equal hybrid, 40 candidates per component | 21 | 14 | 1 |

Every answerable question has a complete labeled support set of at most three
passages somewhere in the corpus: 18 need one, 16 need two, and two need three.
Qwen3-4B's top 40 therefore permit an oracle complete-evidence rate of 34/36,
94.4%. This is a diagnostic upper bound, not attainable performance established
for any deployed selector. Ten of its 12 incomplete results have enough evidence
among their candidates but do not place it in the four supplied slots.

Representative Qwen3-4B dense failures:

| Question | Observed ranking | Implication |
| --- | --- | --- |
| `tech-compare-network-roles` | All four results come from the ADMF-Net paper. The autoencoder explanation, `pmc11121878:p16:w0`, ranks 18. Two passages suffice. | Independent passage scores can emphasize one half of a comparison. Test per-part retrieval and joint evidence selection. |
| `tech-both-checks-clean` | Four generic heater passages precede the required structured-OK-to-bright-field transition at `pmc11768589:p29:w0`, rank 23. An alternative for the final both-modes-OK rule ranks seven. | A general topical match can outrank a precise procedural step. This is not a source-presence problem. |
| `tech-wafer-exact` | The headline SNR claim ranks two. Its approved efficiency-scope requirement needs `pmc10934137:p14:w180`, rank nine, and `pmc10934137:p16:w0`, rank 18. | Scientific qualifications require complementary passages. Topical relevance alone does not optimize completeness. |
| `tech-changing-neighborhood` | Paragraph 31 ranks 23, but required definition and scope paragraphs 29 and 30 are outside the top 40. The text contains repeated `[formula omitted]` placeholders. | Examine context representation, adjacent paragraphs and extraction quality before attributing the miss to model capacity. |

Question definitions are at
`evaluation/datasets/technical-development.json:178`, `:1078`, `:1286` and `:1722`.
Approved evidence requirements are at
`evaluation/labels/technical-development.json:204`, `:1324`, `:1571` and `:2036`.
Qualifications such as fixed line frequency and the fixed window footprint are
intentional approved requirements. Their difficulty does not establish that the
labels are wrong. This audit found no verified new semantic label defect.

## Improvements already measured

The [CPU study](retrieval-improvements.md) already tested 21 configurations,
including weighted RRF, 20/40 candidates, a MiniLM cross-encoder, and diversity.
None beat Qwen3-4B dense's 24/36 complete cases at four. Generic advice to add a
reranker, increase the pool, or enable diversity would repeat completed work.

Actual tokenizer measurements show no passage truncation for BGE-M3 or either
Qwen encoder at the configured 512 tokens. MiniLM truncates eight of 204 passages
at 256 tokens. All 14,000 recorded MiniLM reranker pairs fit below 512. Raising
token limits is therefore not supported as an explanation for the stronger
models' present misses. Larger contexts alone also failed to reach the target:
the best measured six/eight-passage previews achieved 27/36, or 75%.

The newer [Vulkan reranker comparison](vulkan-reranking.md) is now complete.
BGE-M3 plus BGE-reranker-v2-m3 over 20 candidates reached 26/36, 72.2%, at a reported
481 ms median. Qwen3-4B plus that reranker reached 25/36 over either 20 or 40
candidates. These results contradict a blanket claim that no reranker has helped.
All ten configurations completed all 50 development cases without errors. The
selected experimental Vulkan configuration is frozen separately; application
defaults and the prior CPU selection remain unchanged. Its mean group coverage
is 80.3%, which does not meet the separate 80% complete-evidence target.

CPU float32 reference checks covered five predetermined questions per reranker.
BGE's top-four set and order match on all five; Qwen's set matches on all five,
with order matching on four. This subset does not establish full numerical or
ranking equivalence across backends. Held-out retrieval and generated-answer
validation remain pending. Concurrent work completed and documented this study
during the audit; this audit preserves those files and did not rerun its models.

## Reproduction

The following PowerShell command reruns the current scorer on all nine original
limit-four runs, replays the four failure analyses, and performs actual TF-IDF
searches from the saved artifact. It loads no neural models. Run at repository root.

```powershell
@'
import json
import sys
from pathlib import Path
sys.path.insert(0, "backend")
from researchlens.evaluation_schema import Dataset
from researchlens.evaluation_evidence import EvidenceLabels, ranking_metrics
from researchlens.models import Passage
from researchlens.retrieval import TfidfRetriever
from researchlens.retrieval_analysis import analyze_run

base = Path("evaluation/runs/approved-models-2026-10-01-k4")
checked = 0
for path in sorted(base.glob("*/run.json")):
    run = json.loads(path.read_bytes())
    cases = {c.id: c for c in Dataset.model_validate(run["dataset"]).cases}
    labels = {c.case_id: c for c in EvidenceLabels.model_validate(run["evidence_labels"]).cases}
    for row in run["results"]:
        hits = [Passage.model_validate({k: v for k, v in p.items() if k != "score"})
                for p in row["retrieved_passages"][:4]]
        assert ranking_metrics(cases[row["case_id"]], hits, labels.get(row["case_id"])) == row["metrics_at_k"]["4"]
        checked += 1
print("Exact metric matches:", checked)

grid = Path("evaluation/runs/retrieval-improvements-2026-10-02")
for name in ("qwen3-4b-dense", "bge-m3-dense", "qwen3-4b-hybrid40-lex50", "bge-m3-hybrid40-lex50"):
    path = grid / name / "run.json"
    replay = analyze_run(json.loads(path.read_bytes()))
    saved = json.loads(path.with_name("analysis.json").read_bytes())
    assert replay["failure_counts"] == saved["failure_counts"]
    assert replay["cases"] == saved["cases"]
    print(name, replay["failure_counts"])

run = json.loads((base / "tfidf-tfidf/run.json").read_bytes())
dataset = Dataset.model_validate(run["dataset"])
labels = {c.case_id: c for c in EvidenceLabels.model_validate(run["evidence_labels"]).cases}
rows = {r["case_id"]: r for r in run["results"]}
retriever = TfidfRetriever.from_path(base / "indexes/tfidf.json", source=Path("data/technical/documents.json"))
complete = 0
for case in dataset.cases:
    hits = retriever.search(case.question, limit=4)
    assert [h.id for h in hits] == rows[case.id]["retrieved_passage_ids"]
    metrics = ranking_metrics(case, hits, labels.get(case.id))
    assert metrics == rows[case.id]["metrics_at_k"]["4"]
    complete += metrics["complete_evidence"] is True
assert complete == 15
print("Live TF-IDF: 50/50 exact ranking and metric matches; complete evidence 15/36")
'@ | .venv/Scripts/python.exe -
```

Observed outputs were 450 exact baseline metric matches, four identical per-case
failure analyses, and 50 exact TF-IDF ranking/metric matches with 15/36 complete.
Current analysis summaries add `evidence_labeled_cases`; the old summaries lacked
this metadata field. That difference does not alter any replayed score or diagnosis.
