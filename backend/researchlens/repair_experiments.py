"""Bounded development pilot of model support and one evidence-repair pass."""

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

import httpx
import numpy as np

from researchlens.artifacts import canonical_hash, load_artifact
from researchlens.evaluation_evidence import ranking_metrics
from researchlens.ingest import ROOT, TECHNICAL_CORPUS
from researchlens.local_needs import LocalNeeds
from researchlens.selection_diagnostics import load_run
from researchlens.support_assessment import PROMPT, assess, exact_support_set
from researchlens.vulkan_experiments import inputs


def select_pilot(dataset, diagnostics):
    """All recoverable BGE20 failures, first incumbent success per cohort, two negatives."""
    by_id = {r["case_id"]: r for r in diagnostics["cases"]}
    failures = {
        r["case_id"]
        for r in diagnostics["cases"]
        if not r["incumbent_complete"] and r["pools"]["bge20"]["complete"]
    }
    chosen, cohorts, negatives = [], set(), 0
    for case in dataset.cases:
        if case.id in failures:
            chosen.append(case)
        elif case.expected_abstention and negatives < 2:
            chosen.append(case)
            negatives += 1
        elif not case.expected_abstention and by_id[case.id]["incumbent_complete"]:
            if case.query_style not in cohorts:
                chosen.append(case)
                cohorts.add(case.query_style)
    return chosen


def evaluate_pilot(args):
    dataset, labels, artifacts = inputs(args)
    _, passages = load_artifact(args.indexes / "bge-m3.json", source=TECHNICAL_CORPUS)
    _, rows = load_run(args.bge, dataset, artifacts["bge-m3"], passages)
    diagnostics = json.loads(args.diagnostics.read_bytes())
    bundle = json.loads(args.measurements.read_bytes())
    if (
        diagnostics["manifest"]["dataset_sha256"] != canonical_hash(dataset.model_dump(mode="json"))
        or diagnostics["manifest"]["labels_sha256"]
        != canonical_hash(labels.model_dump(mode="json"))
        or bundle["manifest"]["dataset_sha256"] != canonical_hash(dataset.model_dump(mode="json"))
        or bundle["manifest"]["artifact_sha256"] != canonical_hash(artifacts["qwen3-4b"])
    ):
        raise ValueError("Pilot inputs have stale provenance")
    measurements = {r["case_id"]: r for r in bundle["cases"]}
    evidence = {e.case_id: e for e in labels.cases}
    by_id = {p.id: p for p in passages}
    pilot = select_pilot(dataset, diagnostics)
    args.output.mkdir(parents=True, exist_ok=False)
    result = {
        "manifest": {
            "plan": "one repair within BGE20, generated needs, exact predicted support selection",
            "pilot_rule": "recoverable failures, first success per cohort, first two negatives",
            "case_ids": [c.id for c in pilot],
            "selection_uses_labels": False,
            "pilot_sampling_uses_development_labels": True,
            "requirements": "unchanged copied question phrases from prior local needs run",
            "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
            "source_sha256": {
                name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                for name in ("repair_experiments.py", "support_assessment.py")
            },
            "input_sha256": {
                str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (args.bge, args.diagnostics, args.measurements)
            },
            "dataset_sha256": canonical_hash(dataset.model_dump(mode="json")),
            "labels_sha256": canonical_hash(labels.model_dump(mode="json")),
            "api_calls": 0,
            "held_out_searches": False,
            "max_output_tokens": 768,
            "retries": 0,
            "output_limit": 4,
            "secondary_objective": "retain incumbent passages, then dense pool order",
            "timing_scope": "single support/verification/selection stages, excludes retrieval",
        },
        "cases": [],
    }
    output = args.output / "results.json"

    def save():
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    save()
    with LocalNeeds(args.runtime, args.assets, args.output / "support-server.log") as model:
        result["manifest"]["model"] = model.metadata
        for case in pilot:
            original = rows[case.id]["retrieved_passage_ids"]
            ids = [r["passage_id"] for r in rows[case.id]["reranker_passage_diagnostics"]]
            needs = measurements[case.id]["need_queries"]
            if measurements[case.id]["error"] or not needs or len(ids) != 20:
                raise ValueError("Expected successful question-only needs and BGE20 pool")
            row = {
                "case_id": case.id,
                "question": case.question,
                "cohort": case.query_style,
                "expected_abstention": case.expected_abstention,
                "candidate_ids": ids,
                "requirements": needs,
                "original_ids": original,
                "pairs": [],
                "error": None,
            }
            result["cases"].append(row)

            def measure(source, question=case.question, requirements=needs):
                started = perf_counter()
                try:
                    judged = assess(model, question, requirements, source)
                except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
                    judged = {"error": type(error).__name__}
                return {**judged, "latency_ms": 1000 * (perf_counter() - started)}

            def context(selected):
                # Same four canonical passage texts; no neighbor text or inferred facts.
                return "\n\n".join(by_id[pid].text for pid in selected)

            row["before_verification"] = measure(context(original))
            before = row["before_verification"]
            if before["error"]:
                row["error"] = "failed_initial_verification"
                save()
                continue
            predicted_complete = all(j["status"] == "full" for j in before["judgments"])
            row["initial_predicted_complete"] = predicted_complete
            missing = [j["id"] for j in before["judgments"] if j["status"] != "full"]
            row["missing_requirement_ids"] = missing
            row["repair_attempted"] = bool(missing)
            selected = original
            if missing:
                # Cache all requirements once per candidate; unused candidates are searched
                # for missing support. Rescore original passages to preserve established facts.
                for number, pid in enumerate(ids, 1):
                    row["pairs"].append({"passage_id": pid, **measure(by_id[pid].text)})
                    save()
                    print(f"Support {case.id}: {number}/20", flush=True)
                if any(p["error"] for p in row["pairs"]):
                    row["error"] = "failed_candidate_support_no_fallback"
                    save()
                    continue
                utilities = np.array(
                    [
                        [
                            {"full": 1, "partial": 0.5, "absent": 0}[p["judgments"][i]["status"]]
                            for p in row["pairs"]
                        ]
                        for i in range(len(needs))
                    ]
                )
                # A utility tie keeps already supplied evidence before unrelated new passages.
                relevance = [
                    100 + (4 - original.index(pid)) if pid in original else 1 / (1 + i)
                    for i, pid in enumerate(ids)
                ]
                chosen = exact_support_set(utilities, relevance)
                selected = [ids[i] for i in chosen]
                row["after_verification"] = measure(context(selected))
                if row["after_verification"]["error"]:
                    row["error"] = "failed_repair_verification"
            row["selected_ids"] = selected
            row["before_metrics"] = ranking_metrics(
                case, [by_id[p] for p in original], evidence.get(case.id)
            )
            row["after_metrics"] = ranking_metrics(
                case, [by_id[p] for p in selected], evidence.get(case.id)
            )
            verified = row.get("after_verification", before)
            row["final_predicted_complete"] = (
                None
                if verified["error"]
                else all(j["status"] == "full" for j in verified["judgments"])
            )
            save()
            print(f"Saved repair case {case.id}, error={row['error']}", flush=True)
        result["server_memory"] = model.memory_samples
    result["summary"] = {
        "cases": len(result["cases"]),
        "errors": [r["case_id"] for r in result["cases"] if r["error"]],
        "wins": [
            r["case_id"]
            for r in result["cases"]
            if not r["error"]
            and r["after_metrics"]["complete_evidence"] is True
            and r["before_metrics"]["complete_evidence"] is False
        ],
        "regressions": [
            r["case_id"]
            for r in result["cases"]
            if not r["error"]
            and r["after_metrics"]["complete_evidence"] is False
            and r["before_metrics"]["complete_evidence"] is True
        ],
        "false_complete": [
            r["case_id"]
            for r in result["cases"]
            if not r["error"]
            and r["final_predicted_complete"]
            and (r["expected_abstention"] or not r["after_metrics"]["complete_evidence"])
        ],
    }
    save()
    print(json.dumps(result["summary"], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    defaults = {
        "indexes": "evaluation/runs/approved-models-2026-10-01-k4/indexes",
        "dataset": "evaluation/datasets/technical-development.json",
        "other-split": "evaluation/datasets/held-out.json",
        "evidence-labels": "evaluation/labels/technical-development.json",
        "measurements": "evaluation/runs/information-needs-schema-v2-2026-10-02/measurements.json",
        "bge": "evaluation/runs/vulkan-rerankers-cache-off-2026-10-02/bge-m3-bge-rerank20/run.json",
        "diagnostics": "evaluation/runs/selection-diagnostics-2026-10-05/oracles.json",
        "runtime": ".venv/vulkan",
        "assets": ".venv/needs-model",
    }
    for key, path in defaults.items():
        parser.add_argument("--" + key, type=Path, default=ROOT / path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for key, value in vars(args).items():
        if isinstance(value, Path):
            setattr(args, key, value.resolve())
    evaluate_pilot(args)


if __name__ == "__main__":
    main()
