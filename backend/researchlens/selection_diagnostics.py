"""Development-only constrained oracles and cached selection substitutions.

Reviewed annotations enter only this diagnostic module, never the application.
"""

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np

from researchlens.artifacts import canonical_hash
from researchlens.evaluation_evidence import ranking_metrics
from researchlens.evidence_selection import select_complementary
from researchlens.ingest import ROOT
from researchlens.models import SearchHit
from researchlens.set_selection import exact_max_utility, rank_utilities
from researchlens.vulkan_experiments import inputs
from researchlens.vulkan_reranking import VulkanReranker


def covered_groups(entry, selected):
    selected = set(selected)
    return [
        any({span.passage_id for span in option} <= selected for option in group.alternatives)
        for group in entry.groups
    ]


def constrained_oracle(entry, candidates, limit=4):
    """Maximize whole AND/OR groups under a slot budget; return a smallest witness.

    Only labeled IDs can improve the objective, so excluding unlabeled candidates
    is exact. Joint alternatives remain joint; individual partial spans cannot
    compensate for an uncovered fact. Ties prefer fewer passages then pool order.
    """
    if len(set(candidates)) != len(candidates) or not 1 <= limit <= 4:
        raise ValueError("Use unique candidates and 1 to 4 slots")
    relevant = {
        span.passage_id
        for group in entry.groups
        for option in group.alternatives
        for span in option
    }
    ids = [p for p in candidates if p in relevant]
    best, count = (), 0
    for size in range(1, min(limit, len(ids)) + 1):
        for chosen in combinations(ids, size):
            score = sum(covered_groups(entry, chosen))
            if score > count:
                best, count = chosen, score
                if count == len(entry.groups):
                    return {"complete": True, "covered": count, "witness": list(best)}
    return {"complete": False, "covered": count, "witness": list(best)}


def label_utilities(entry, ids, original):
    """Diagnostic per-passage substitution; joint support is explicitly partial.

    This changes the utility scale to reviewed support. It retains the greedy
    engine but cannot make a max-per-passage objective represent joint support.
    """
    scores = [rank_utilities([original])[0]]
    for group in entry.groups:
        options = [{s.passage_id for s in option} for option in group.alternatives]
        scores.append([max((1 / len(o) if pid in o else 0) for o in options) for pid in ids])
    return np.asarray(scores)


def load_run(path, dataset, artifact, passages):
    run = json.loads(path.read_bytes())
    if run["dataset"] != dataset.model_dump(mode="json") or run["corpus"][
        "artifact_sha256"
    ] != canonical_hash(artifact):
        raise ValueError("Saved run has stale dataset or artifact provenance")
    canonical = {p.id: p.model_dump() for p in passages}
    rows = {row["case_id"]: row for row in run["results"]}
    if len(rows) != len(dataset.cases) or set(rows) != {c.id for c in dataset.cases}:
        raise ValueError("Saved run cases do not match development dataset")
    for row in rows.values():
        if row["error"] or row["ranking_stable_across_repeats"] is not True:
            raise ValueError("Saved run must have successful stable rankings")
        for hit in row["retrieved_passages"]:
            if SearchHit.model_validate(hit).model_dump(exclude={"score"}) != canonical[hit["id"]]:
                raise ValueError("Saved passage differs from canonical source")
    return run, rows


def analyze(args):
    dataset, labels, artifacts = inputs(args)
    from researchlens.artifacts import load_artifact
    from researchlens.ingest import TECHNICAL_CORPUS

    _, passages = load_artifact(args.indexes / "qwen3-4b.json", source=TECHNICAL_CORPUS)
    by_id = {p.id: p for p in passages}
    bundle = json.loads(args.measurements.read_bytes())
    manifest = bundle["manifest"]
    if (
        manifest["artifact_sha256"] != canonical_hash(artifacts["qwen3-4b"])
        or manifest["dataset_sha256"] != canonical_hash(dataset.model_dump(mode="json"))
        or manifest["evidence_labels_sha256"] != canonical_hash(labels.model_dump(mode="json"))
    ):
        raise ValueError("Frozen score matrices have stale input provenance")
    measurements = {r["case_id"]: r for r in bundle["cases"]}
    qrun, qrows = load_run(args.qwen, dataset, artifacts["qwen3-4b"], passages)
    brun, brows = load_run(args.bge, dataset, artifacts["bge-m3"], passages)
    b40run, b40rows = load_run(args.bge40, dataset, artifacts["bge-m3"], passages)
    evidence = {e.case_id: e for e in labels.cases}
    result = {
        "manifest": {
            "dataset_sha256": canonical_hash(dataset.model_dump(mode="json")),
            "labels_sha256": canonical_hash(labels.model_dump(mode="json")),
            "input_sha256": {
                str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (args.measurements, args.qwen, args.bge, args.bge40)
            },
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "slot_budget": 4,
            "plan": [
                "pool-oracles-bge20-qwen40-union-matched-bge40-qwen40",
                "generated-needs-greedy-vs-exact-identical-utility",
                "approved-group-label-utilities-greedy-vs-exact",
                "joint-support-oracle",
                "reference-recall-ceilings",
            ],
            "label_assisted": True,
            "held_out_searches": False,
            "api_calls": 0,
        },
        "cases": [],
    }
    for case in dataset.cases:
        if case.expected_abstention:
            continue  # Negatives have no completeness labels; never count them as oracle successes.
        entry, measured = evidence[case.id], measurements[case.id]
        qids = [p["id"] for p in qrows[case.id]["retrieved_passages"]]
        if qids != measured["candidate_ids"] or len(qids) != 40 or measured["error"]:
            raise ValueError("Expected unchanged successful Qwen top-40 measurements")
        bdiagnostics = brows[case.id]["reranker_passage_diagnostics"]
        bids = [d["passage_id"] for d in bdiagnostics]
        b40ids = [d["passage_id"] for d in b40rows[case.id]["reranker_passage_diagnostics"]]
        if len(bids) != 20 or len(b40ids) != 40 or len(set(qids)) != 40:
            raise ValueError("Unexpected pool size")
        pools = {
            "bge20": bids,
            "qwen40": qids,
            "bge40": b40ids,
            "bge20-qwen40-union": list(dict.fromkeys(bids + qids)),
            "bge20-qwen20-union": list(dict.fromkeys(bids + qids[:20])),
        }
        originals = measured["original_scores"]
        utilities = rank_utilities([originals, *measured["need_scores"]])
        reviewed = label_utilities(entry, qids, originals)
        selections = {
            "qwen40-whole-rerank": sorted(range(40), key=lambda i: (-originals[i], i))[:4],
            "generated-greedy": select_complementary(utilities, 4),
            "generated-exact": exact_max_utility(utilities),
            "reviewed-support-greedy": select_complementary(reviewed, 4),
            "reviewed-support-exact-max": exact_max_utility(reviewed),
        }
        row = {
            "case_id": case.id,
            "question": case.question,
            "cohort": case.query_style,
            "generated_needs": measured["need_queries"],
            "approved_group_descriptions": [g.description for g in entry.groups],
            "pools": {
                name: {"ids": ids, **constrained_oracle(entry, ids)} for name, ids in pools.items()
            },
            "selections": {},
            "incumbent_ids": brows[case.id]["retrieved_passage_ids"],
            "incumbent_complete": brows[case.id]["metrics_at_k"]["4"]["complete_evidence"],
        }
        for name, chosen in selections.items():
            hits = [by_id[qids[i]] for i in chosen]
            row["selections"][name] = {
                "ids": [h.id for h in hits],
                "metrics": ranking_metrics(case, hits, entry),
            }
        references = {r.passage_id for r in case.references}
        row["reference_count"] = len(references)
        row["reference_recall_ceiling_corpus"] = min(4, len(references)) / len(references)
        row["reference_recall_ceiling_pools"] = {
            name: min(4, len(references & set(ids))) / len(references)
            for name, ids in pools.items()
        }
        result["cases"].append(row)
    summarize(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps(result["summary"], indent=2))


def summarize(result):
    rows = result["cases"]
    result["summary"] = {
        "answerable_cases": len(rows),
        "oracles": {
            name: {
                "complete": sum(r["pools"][name]["complete"] for r in rows),
                "misses": [r["case_id"] for r in rows if not r["pools"][name]["complete"]],
                "actual_complete": sum(r["incumbent_complete"] for r in rows)
                if name == "bge20"
                else None,
            }
            for name in rows[0]["pools"]
        },
        "selections": {
            name: {
                "complete": sum(
                    r["selections"][name]["metrics"]["complete_evidence"] for r in rows
                ),
                "wins_vs_incumbent": [
                    r["case_id"]
                    for r in rows
                    if r["selections"][name]["metrics"]["complete_evidence"]
                    and not r["incumbent_complete"]
                ],
                "regressions_vs_incumbent": [
                    r["case_id"]
                    for r in rows
                    if not r["selections"][name]["metrics"]["complete_evidence"]
                    and r["incumbent_complete"]
                ],
            }
            for name in rows[0]["selections"]
        },
        "reference_recall_ceiling_corpus": float(
            np.mean([r["reference_recall_ceiling_corpus"] for r in rows])
        ),
    }


def reviewed_scoring(args):
    """Replace extracted needs with approved descriptions, retaining BGE and selection.

    Descriptions may contain answer facts. This is deliberately label-assisted,
    not a deployable decomposition or an independent human semantic review.
    """
    dataset, labels, artifacts = inputs(args)
    from researchlens.artifacts import load_artifact
    from researchlens.ingest import TECHNICAL_CORPUS

    _, passages = load_artifact(args.indexes / "qwen3-4b.json", source=TECHNICAL_CORPUS)
    _, rows = load_run(args.qwen, dataset, artifacts["qwen3-4b"], passages)
    diagnostics = json.loads(args.diagnostics.read_bytes())
    if diagnostics["manifest"]["dataset_sha256"] != canonical_hash(
        dataset.model_dump(mode="json")
    ) or diagnostics["manifest"]["labels_sha256"] != canonical_hash(labels.model_dump(mode="json")):
        raise ValueError("Diagnostic inputs are stale")
    by_case = {r["case_id"]: r for r in diagnostics["cases"]}
    evidence = {e.case_id: e for e in labels.cases}
    args.output.mkdir(parents=True, exist_ok=False)
    result = {
        "manifest": {
            "dataset_sha256": canonical_hash(dataset.model_dump(mode="json")),
            "labels_sha256": canonical_hash(labels.model_dump(mode="json")),
            "diagnostics_sha256": hashlib.sha256(args.diagnostics.read_bytes()).hexdigest(),
            "qwen_run_sha256": hashlib.sha256(args.qwen.read_bytes()).hexdigest(),
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "plan": ["approved-descriptions-greedy", "approved-descriptions-exact"],
            "query_convention": "original question + Evidence requirement: approved description",
            "label_assisted": True,
            "held_out_searches": False,
            "api_calls": 0,
            "timing_scope": "single staged requirement scoring; excludes encoding and selection",
        },
        "cases": [],
    }
    from time import perf_counter

    bundle = json.loads(args.measurements.read_bytes())
    measured = {r["case_id"]: r for r in bundle["cases"]}
    if (
        diagnostics["manifest"]["input_sha256"][str(args.measurements.relative_to(ROOT))]
        != hashlib.sha256(args.measurements.read_bytes()).hexdigest()
    ):
        raise ValueError("Diagnostic measurements changed")
    with VulkanReranker(args.runtime, "bge", args.output / "server.log") as reranker:
        result["manifest"]["reranker"] = reranker.metadata
        (args.output / "measurements.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        for case in dataset.cases:
            if case.expected_abstention:
                continue
            hits = [SearchHit.model_validate(p) for p in rows[case.id]["retrieved_passages"]]
            if [h.id for h in hits] != measured[case.id]["candidate_ids"]:
                raise ValueError("Reviewed and generated scores must share identical candidates")
            scores, records = [measured[case.id]["original_scores"]], []
            for group in evidence[case.id].groups:
                query = case.question + "\nEvidence requirement: " + group.description
                if len(query) > 2000:
                    raise ValueError("Diagnostic query exceeds question limit")
                started = perf_counter()
                scores.append(reranker.score(query, hits).tolist())
                records.append(
                    {
                        "group_id": group.id,
                        "query": query,
                        "scoring_ms": 1000 * (perf_counter() - started),
                        "pairs": reranker.last_diagnostics,
                    }
                )
            utilities = rank_utilities(scores)
            selections = {}
            for name, chosen in (
                ("approved-descriptions-greedy", select_complementary(utilities, 4)),
                ("approved-descriptions-exact", exact_max_utility(utilities)),
            ):
                selected = [hits[i] for i in chosen]
                selections[name] = {
                    "ids": [h.id for h in selected],
                    "metrics": ranking_metrics(case, selected, evidence[case.id]),
                }
            result["cases"].append(
                {
                    **by_case[case.id],
                    "selections": selections,
                    "scores": scores,
                    "requirements": records,
                }
            )
            summarize(result)
            (args.output / "measurements.json").write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            print(f"Scored approved descriptions {len(result['cases'])}/36: {case.id}", flush=True)
        result["server_memory"] = reranker.memory_samples
    (args.output / "measurements.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["summary"], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    defaults = {
        "indexes": "evaluation/runs/approved-models-2026-10-01-k4/indexes",
        "dataset": "evaluation/datasets/technical-development.json",
        "other-split": "evaluation/datasets/held-out.json",
        "evidence-labels": "evaluation/labels/technical-development.json",
        "measurements": "evaluation/runs/information-needs-schema-v2-2026-10-02/measurements.json",
        "qwen": "evaluation/runs/retrieval-improvements-2026-10-02/qwen3-4b-dense/run.json",
        "bge": "evaluation/runs/vulkan-rerankers-cache-off-2026-10-02/bge-m3-bge-rerank20/run.json",
        "bge40": (
            "evaluation/runs/vulkan-rerankers-cache-off-2026-10-02/bge-m3-bge-rerank40/run.json"
        ),
    }
    for key, path in defaults.items():
        parser.add_argument("--" + key, type=Path, default=ROOT / path)
    parser.add_argument("--stage", choices=("oracle", "reviewed-scoring"), default="oracle")
    parser.add_argument("--runtime", type=Path, default=ROOT / ".venv/vulkan")
    parser.add_argument("--diagnostics", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Normalize once because provenance keys are workspace-relative.
    for key, value in vars(args).items():
        if isinstance(value, Path):
            setattr(args, key, value.resolve())
    reviewed_scoring(args) if args.stage == "reviewed-scoring" else analyze(args)


if __name__ == "__main__":
    main()
