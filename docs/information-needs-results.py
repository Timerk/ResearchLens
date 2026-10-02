"""Compact archive of shared-runner scores and immutable local inference measurements."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from researchlens.evaluation import summarize  # noqa: E402


def short_metrics(row):
    return {key: value for key, value in row.items() if key != "groups"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--studies", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    archive = {"studies": []}
    for root in args.studies:
        study = {
            "directory": root.name,
            "manifest": json.loads((root / "manifest.json").read_bytes()),
            "configurations": [],
        }
        for directory in sorted(
            p for p in root.iterdir() if p.is_dir() and (p / "run.json").exists()
        ):
            raw = (directory / "run.json").read_bytes()
            run = json.loads(raw)
            summary = summarize(run)
            item = {
                "name": directory.name,
                "run_sha256": hashlib.sha256(raw).hexdigest(),
                "code": run["code"],
                "retrieval": run["retrieval"],
                "summary": {
                    key: value
                    for key, value in summary.items()
                    if key.startswith(("query_", "primary_k4_"))
                    or key in ("unstable_ranking_cases", "process_peak_rss_bytes")
                },
                "cases": [
                    {
                        "case_id": r["case_id"],
                        "error": r["error"],
                        "selected_ids": r["retrieved_passage_ids"],
                        "metrics": short_metrics(r.get("metrics_at_k", {}).get("4", {})),
                    }
                    for r in run["results"]
                ],
            }
            # Keep all 36 positives in the denominator, including extraction failures.
            item["complete_count_all_36"] = sum(
                r["metrics"].get("complete_evidence") is True for r in item["cases"]
            )
            item["error_count_all_50"] = sum(bool(r["error"]) for r in item["cases"])
            styles = {c["id"]: c["query_style"] for c in run["dataset"]["cases"]}
            item["cohorts"] = {
                style: {
                    "cases": sum(styles[r["case_id"]] == style for r in item["cases"]),
                    "complete": sum(
                        styles[r["case_id"]] == style
                        and r["metrics"].get("complete_evidence") is True
                        for r in item["cases"]
                    ),
                    "both_sources": sum(
                        styles[r["case_id"]] == style and r["metrics"].get("all_sources") is True
                        for r in item["cases"]
                    ),
                }
                for style in sorted(set(styles.values()))
            }
            candidate_path = directory / "candidate-run.json"
            if candidate_path.exists():
                candidates = json.loads(candidate_path.read_bytes())
                item["candidate_metrics"] = [
                    {
                        "case_id": r["case_id"],
                        "candidate_ids": r["retrieved_passage_ids"],
                        "metrics": {k: short_metrics(v) for k, v in r["metrics_at_k"].items()},
                    }
                    for r in candidates["results"]
                ]
            measurement_path = directory / "input-measurements.json"
            if measurement_path.exists():
                measurements = json.loads(measurement_path.read_bytes())["passages"]
                item["actual_input_measurements"] = {
                    "max_tokens": max(r["input_tokens"] for r in measurements),
                    "truncated_inputs": sum(
                        r["input_tokens"] > r["encoded_tokens"] for r in measurements
                    ),
                    "passages": len(measurements),
                }
            study["configurations"].append(item)
        bundle_path = root / "measurements.json"
        if bundle_path.exists():
            bundle_raw = bundle_path.read_bytes()
            bundle = json.loads(bundle_raw)
            study["measurement_bundle_sha256"] = hashlib.sha256(bundle_raw).hexdigest()
            study["measurements"] = [
                {
                    k: v
                    for k, v in row.items()
                    if k != "pair_diagnostics" and k != "original_pair_diagnostics"
                }
                for row in bundle["cases"]
            ]
            pairs = [
                pair
                for row in bundle["cases"]
                for values in row["pair_diagnostics"].values()
                for pair in values
            ]
            study["pair_visibility"] = {
                "measured_pairs": len(pairs),
                "max_input_tokens": max(p["input_tokens"] for p in pairs),
                "truncated_pairs": sum(p["truncated"] for p in pairs),
            }
        memory_path = root / "server-memory.json"
        if memory_path.exists():
            memory = json.loads(memory_path.read_bytes())
            study["server_memory"] = {
                kind: {
                    "samples": len(memory[kind]),
                    "peak_private_bytes": max(s["peak_private_bytes"] for s in memory[kind]),
                    "peak_rss_bytes": max(s["peak_rss_bytes"] for s in memory[kind]),
                }
                for kind in ("needs", "reranker")
            }
        archive["studies"].append(study)
    args.output.write_text(json.dumps(archive, indent=2) + "\n", encoding="utf-8")
    print(f"Archived {len(archive['studies'])} studies")


if __name__ == "__main__":
    main()
