"""Archive constrained development diagnostics without vectors or repeated token rows."""

import argparse
import copy
import hashlib
import json
import statistics
from pathlib import Path


def archive(root, output):
    paths = {
        "oracles": root / "selection-diagnostics-2026-10-05/oracles.json",
        "reviewed_scoring": root
        / "selection-diagnostics-2026-10-05/reviewed-scoring/measurements.json",
        "embedding_parity": root
        / "selection-diagnostics-2026-10-05/embedding-parity-distinct.json",
        "initial_repair": root / "support-repair-pilot-2026-10-05/results.json",
        "corrected_repair": root / "support-repair-schema-v2-2026-10-05/results.json",
    }
    result = {
        "archive_schema": 1,
        "input_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()
        },
    }
    for name, path in paths.items():
        data = copy.deepcopy(json.loads(path.read_bytes()))
        if "server_memory" in data:
            data["native_memory_summary"] = {
                "peak_private_bytes": max(
                    row["peak_private_bytes"] for row in data["server_memory"]
                ),
                "scope": "owned local server; excludes Python and VRAM",
            }
            del data["server_memory"]
        if name == "reviewed_scoring":
            counts = [p for r in data["cases"] for q in r["requirements"] for p in q["pairs"]]
            data["pair_summary"] = {
                "requirements": sum(len(r["requirements"]) for r in data["cases"]),
                "pairs": len(counts),
                "max_input_tokens": max(p["input_tokens"] for p in counts),
                "truncated": sum(p["truncated"] for p in counts),
            }
            for row in data["cases"]:
                del row["pools"]  # Identical to the oracles archive.
                for requirement in row["requirements"]:
                    del requirement["pairs"]
        if name.endswith("repair"):
            data["measurement_summary"] = {
                "requests": sum(
                    len(r["pairs"]) + 1 + bool(r.get("after_verification")) for r in data["cases"]
                ),
                "staged_ms_median": statistics.median(
                    sum(p["latency_ms"] for p in r["pairs"])
                    + r["before_verification"]["latency_ms"]
                    + r.get("after_verification", {}).get("latency_ms", 0)
                    for r in data["cases"]
                ),
                "scope": "single staged requests, excludes baseline retrieval; not throughput",
            }
        result[name] = data
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=Path("evaluation/runs"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    archive(args.runs, args.output)
