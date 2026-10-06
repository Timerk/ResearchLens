"""Archive existing evaluation metrics and selection diagnostics, without model calls."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from researchlens.evaluation import summarize  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.run_directory / "manifest.json").read_bytes())
    archive = {"protocol": manifest, "configurations": []}
    for entry in manifest["plan"]:
        directory = args.run_directory / entry["name"]
        raw = (directory / "run.json").read_bytes()
        run = json.loads(raw)
        item = {
            "name": entry["name"],
            "run_sha256": hashlib.sha256(raw).hexdigest(),
            "run_id": run["run_id"],
            "code": run["code"],
            "retrieval": run["retrieval"],
            "summary": summarize(run),
            "cases": [
                {
                    key: row[key]
                    for key in (
                        "case_id",
                        "retrieved_passage_ids",
                        "metrics_at_k",
                        "error",
                        "retrieval_latency_ms",
                        "ranking_stable_across_repeats",
                    )
                    if key in row
                }
                for row in run["results"]
            ],
        }
        styles = {case["id"]: case["query_style"] for case in run["dataset"]["cases"]}
        item["cohorts"] = {
            style: {
                "cases": sum(styles[r["case_id"]] == style for r in run["results"]),
                "complete": sum(
                    styles[r["case_id"]] == style
                    and r["metrics_at_k"]["4"]["complete_evidence"] is True
                    for r in run["results"]
                ),
                "all_expected_sources": sum(
                    styles[r["case_id"]] == style and r["metrics_at_k"]["4"]["all_sources"] is True
                    for r in run["results"]
                ),
            }
            for style in sorted(set(styles.values()))
        }
        selection_path = directory / "selection.json"
        if selection_path.exists():
            selection = json.loads(selection_path.read_bytes())
            item["selection"] = [
                {k: v for k, v in row.items() if k != "query_pair_diagnostics"}
                for row in selection["cases"]
            ]
            measurements = [
                pair
                for row in selection["cases"]
                for query in row.get("query_pair_diagnostics", [])
                for pair in query
            ]
            item["pair_visibility"] = {
                "measured_pairs_last_attempt": len(measurements),
                "max_input_tokens": max((p["input_tokens"] for p in measurements), default=None),
                "truncated_pairs": sum(p["truncated"] for p in measurements),
                "scope": "last attempt per case; enriched input where configured",
            }
        memory_path = directory / "server-memory.json"
        if memory_path.exists():
            memory = json.loads(memory_path.read_bytes())
            item["server_memory"] = {
                "scope": memory["scope"],
                "sampling": memory["sampling"],
                "sample_count": len(memory["samples"]),
                "maxima": {
                    key: max(sample[key] for sample in memory["samples"])
                    for key in (
                        "rss_bytes",
                        "private_bytes",
                        "peak_rss_bytes",
                        "peak_private_bytes",
                    )
                },
            }
        archive["configurations"].append(item)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(archive, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"Archived {len(archive['configurations'])} configurations")


if __name__ == "__main__":
    main()
