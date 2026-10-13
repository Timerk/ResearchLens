"""Development-only local corpus comparison through the existing evaluation CLI."""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from time import perf_counter

import numpy as np

from researchlens.artifacts import canonical_hash, load_artifact
from researchlens.embedding_models import create_encoder, model_for_encoding
from researchlens.embeddings import validate_vectors
from researchlens.evaluation import encoded, load_dataset
from researchlens.ingest import ROOT, TECHNICAL_CORPUS


def candidate_index(candidate: Path, canonical_index: Path, model: str) -> dict:
    """Reuse vectors only for byte-identical encoder inputs under identical settings."""
    baseline, old_passages = load_artifact(canonical_index, source=TECHNICAL_CORPUS)
    artifact, passages = load_artifact(
        candidate / "index.json", source=candidate / "documents.json"
    )
    metadata = baseline["embeddings"]["encoding"]
    if model_for_encoding(metadata) != model:
        raise ValueError("Canonical index encoding differs from selected model/runtime")
    old_vectors = np.asarray(baseline["embeddings"]["vectors"], dtype=np.float32)
    cache = {p.text: old_vectors[i] for i, p in enumerate(old_passages)}
    changed = [p for p in passages if p.text not in cache]
    encoder = create_encoder(
        model,
        download=False,
        max_tokens=metadata["max_tokens"],
        batch_size=metadata["batch_size"],
        threads=metadata["intra_op_threads"],
        precision=metadata["precision"],
    )
    if encoder.encoding != metadata:
        raise ValueError("Candidate encoder settings differ from canonical index")
    print(f"Encoding {len(changed)} changed passages for {model}", flush=True)
    vectors = encoder.encode([p.text for p in changed])
    cache.update({p.text: vectors[i] for i, p in enumerate(changed)})
    vectors = validate_vectors(
        np.asarray([cache[p.text] for p in passages]), len(passages), metadata["dimensions"]
    )
    artifact["embeddings"] = {
        "encoding": metadata,
        "passage_ids": [p.id for p in passages],
        "vectors": vectors.tolist(),
        "vectors_sha256": hashlib.sha256(vectors.astype("<f4").tobytes()).hexdigest(),
    }
    path = candidate / f"{model}-index.json"
    path.write_bytes(encoded(artifact))
    load_artifact(path, source=candidate / "documents.json")
    return {
        "model": model,
        "freshly_encoded_passages": len(changed),
        "reused_exact_text_vectors": len(passages) - len(changed),
        "canonical_index_sha256": hashlib.sha256(canonical_index.read_bytes()).hexdigest(),
        "candidate_index_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "encoding_sha256": canonical_hash(metadata),
    }


def experiment(candidate: Path, indexes: Path, output: Path):
    if load_dataset(candidate / "development-dataset.json").split != "development":
        raise ValueError("Only development retrieval is authorized")
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema_version": 1,
        "candidate": str(candidate.relative_to(ROOT)),
        "context_budgets": [4, 12000, 16000],
        "limit": 40,
        "repeats": 1,
        "warmups": 0,
        "api_calls": 0,
        "held_out_searches": 0,
        "generation": "none",
        "stages": [],
        "timing_scope": "single local retrieval per question; no latency comparison claimed",
        "index_reuse": "unchanged passage text under identical pinned encoder settings only",
    }

    def stage(name, module, args):
        print(f"Starting {name}", flush=True)
        started = perf_counter()
        result = subprocess.run(
            [sys.executable, "-m", module, *map(str, args)],
            cwd=ROOT / "backend",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        (output / f"{name}.log").write_bytes(result.stdout)
        manifest["stages"].append(
            {
                "name": name,
                "returncode": result.returncode,
                "duration_seconds": round(perf_counter() - started, 3),
            }
        )
        (output / "manifest.json").write_bytes(encoded(manifest))
        print(f"{name}: exit {result.returncode}", flush=True)
        if result.returncode:
            raise ValueError(f"Stage failed: {name}; inspect its local log")

    for model in ("tfidf", "bge-m3", "qwen3-4b"):
        if model != "tfidf":
            stage(
                f"{model}-index",
                "researchlens.formula_experiments",
                [
                    "--candidate",
                    candidate,
                    "--indexes",
                    indexes,
                    "--output",
                    output,
                    "--build-index",
                    model,
                ],
            )
        for variant in ("canonical", "candidate"):
            source = TECHNICAL_CORPUS if variant == "canonical" else candidate / "documents.json"
            index = (
                indexes / f"{model}.json"
                if variant == "canonical"
                else candidate / ("index.json" if model == "tfidf" else f"{model}-index.json")
            )
            dataset = (
                ROOT / "evaluation/datasets/technical-development.json"
                if variant == "canonical"
                else candidate / "development-dataset.json"
            )
            labels = (
                ROOT / "evaluation/labels/technical-development.json"
                if variant == "canonical"
                else candidate / "development-labels.json"
            )
            stage(
                f"{model}-{variant}",
                "researchlens.evaluation",
                [
                    "run",
                    "--dataset",
                    dataset,
                    "--other-split",
                    ROOT / "evaluation/datasets/held-out.json",
                    "--source",
                    source,
                    "--index",
                    index,
                    "--retriever",
                    "tfidf" if model == "tfidf" else "embeddings",
                    "--evidence-labels",
                    labels,
                    "--output",
                    output / f"{model}-{variant}",
                    "--limit",
                    40,
                    "--context-budgets",
                    4,
                    12000,
                    16000,
                    "--repeats",
                    1,
                    "--warmups",
                    0,
                    "--measure-memory",
                ],
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--indexes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-index", choices=("bge-m3", "qwen3-4b"))
    args = parser.parse_args()
    candidate, indexes, output = (p.resolve() for p in (args.candidate, args.indexes, args.output))
    if not candidate.is_relative_to(ROOT / "evaluation/runs") or not output.is_relative_to(
        ROOT / "evaluation/runs"
    ):
        raise ValueError("Candidate and outputs must remain in ignored evaluation/runs")
    if args.build_index:
        metadata = candidate_index(
            candidate, indexes / f"{args.build_index}.json", args.build_index
        )
        (output / f"{args.build_index}-index-provenance.json").write_bytes(encoded(metadata))
    else:
        experiment(candidate, indexes, output)


if __name__ == "__main__":
    main()
