"""Evaluation-only enriched vectors with unchanged canonical passages and measured visibility."""

import argparse
import copy
import hashlib
from pathlib import Path

import numpy as np

from researchlens.artifacts import canonical_hash, load_artifact
from researchlens.embedding_models import create_encoder, model_for_encoding
from researchlens.encoding_diagnostics import diagnostic_artifact
from researchlens.evaluation import (
    comparison_report,
    default_retrieval_config,
    encoded,
    review_template,
    run_evaluation,
)
from researchlens.evaluation_schema import ExecutionConfig
from researchlens.ingest import ROOT, TECHNICAL_CORPUS
from researchlens.retrieval import EmbeddingRetriever
from researchlens.vulkan_experiments import inputs

REPRESENTATIONS = ("title-section-text-v1", "title-section-current-neighbors60-v1")


def representation_inputs(passages, representation):
    if representation not in REPRESENTATIONS:
        raise ValueError("Unsupported enriched representation")
    texts, ranges = [], []
    for index, passage in enumerate(passages):
        prefix = f"Title: {passage.title}\nSection: {passage.source_section or ''}\n\n"
        text = prefix + passage.text
        ranges.append({"start": len(prefix), "end": len(text)})
        if representation.endswith("neighbors60-v1"):
            for position, label in ((index - 1, "Previous"), (index + 1, "Next")):
                if (
                    0 <= position < len(passages)
                    and passages[position].document_id == passage.document_id
                ):
                    text += f"\n{label}: " + " ".join(passages[position].text.split()[:60])
        texts.append(text)
    return texts, ranges


def enriched_artifact(artifact, passages, encoder, representation):
    texts, ranges = representation_inputs(passages, representation)
    measured = encoder.measure_documents(texts)
    vectors = encoder.encode(texts).astype(np.float32)
    result = copy.deepcopy(artifact)
    result["embeddings"]["encoding"].update(text=representation, encoding_version=3)
    result["embeddings"].update(
        vectors=vectors.tolist(),
        vectors_sha256=hashlib.sha256(vectors.astype("<f4").tobytes()).hexdigest(),
    )
    result["representation"] = {
        "version": representation,
        "inputs_sha256": canonical_hash(texts),
        "core_input_ranges": ranges,
        "neighbor_words": 60 if "neighbors" in representation else 0,
    }
    rows = []
    for passage, core, row in zip(passages, ranges, measured, strict=True):
        end = max((r["end"] for r in row["retained_ranges"]), default=0)
        retained = min(len(passage.text), max(0, end - core["start"]))
        rows.append(
            {
                **row,
                "text_sha256": hashlib.sha256(passage.text.encode()).hexdigest(),
                "truncated": retained < len(passage.text),
                "retained_ranges": [{"start": 0, "end": retained}] if retained else [],
            }
        )
    return result, diagnostic_artifact(result, rows), measured


class RepresentedRetriever(EmbeddingRetriever):
    def __init__(self, artifact, passages, encoder, diagnostics):
        plain_encoding = {
            **artifact["embeddings"]["encoding"],
            "text": "passage-text-only",
            "encoding_version": 2,
        }
        if encoder.encoding != plain_encoding:
            raise ValueError("Enriched vectors differ from the query encoder's pinned conventions")
        texts, ranges = representation_inputs(passages, artifact["representation"]["version"])
        if (
            artifact["representation"]["inputs_sha256"] != canonical_hash(texts)
            or artifact["representation"]["core_input_ranges"] != ranges
            or artifact["embeddings"]["encoding"]["text"] != artifact["representation"]["version"]
            or artifact["embeddings"]["encoding"]["encoding_version"] != 3
            or diagnostics["artifact_sha256"] != canonical_hash(artifact)
        ):
            raise ValueError("Stale enriched representation; rebuild this experiment")
        super().__init__(
            passages, artifact["embeddings"]["vectors"], encoder, artifact["embeddings"]["encoding"]
        )
        self._diagnostics = diagnostics

    def get_encoding_diagnostics(self):
        return self._diagnostics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--indexes",
        type=Path,
        default=ROOT / "evaluation/runs/approved-models-2026-10-01-k4/indexes",
    )
    parser.add_argument(
        "--dataset", type=Path, default=ROOT / "evaluation/datasets/technical-development.json"
    )
    parser.add_argument(
        "--other-split", type=Path, default=ROOT / "evaluation/datasets/held-out.json"
    )
    parser.add_argument(
        "--evidence-labels",
        type=Path,
        default=ROOT / "evaluation/labels/technical-development.json",
    )
    args = parser.parse_args()
    dataset, labels, _ = inputs(args)
    artifact, passages = load_artifact(args.indexes / "qwen3-4b.json", source=TECHNICAL_CORPUS)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "manifest.json").write_bytes(
        encoded(
            {
                "plan": list(REPRESENTATIONS),
                "model": artifact["embeddings"]["encoding"],
                "artifact_sha256": canonical_hash(artifact),
                "dataset_sha256": canonical_hash(dataset.model_dump(mode="json")),
                "evidence_labels_sha256": canonical_hash(labels.model_dump(mode="json")),
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "api_calls": 0,
                "held_out_searches": False,
                "canonical_chunk_changes": False,
                "limit": 4,
                "candidate_cutoffs": [20, 40],
                "repeats": 3,
                "warmups": 1,
            }
        )
    )
    encoding = artifact["embeddings"]["encoding"]
    encoder = create_encoder(
        model_for_encoding(encoding),
        max_tokens=encoding["max_tokens"],
        batch_size=encoding["batch_size"],
        threads=encoding["intra_op_threads"],
        precision=encoding["precision"],
    )
    for representation in REPRESENTATIONS:
        directory = args.output / representation
        directory.mkdir()
        print(f"Building enriched vectors: {representation}", flush=True)
        enriched, diagnostics, measured = enriched_artifact(
            artifact, passages, encoder, representation
        )
        (directory / "index.json").write_bytes(encoded(enriched))
        (directory / "encoding-diagnostics.json").write_bytes(encoded(diagnostics))
        (directory / "input-measurements.json").write_bytes(encoded({"passages": measured}))
        # Revalidate on-disk canonical identity and vector checksums before searching.
        enriched, canonical = load_artifact(directory / "index.json", source=TECHNICAL_CORPUS)
        retriever = RepresentedRetriever(enriched, canonical, encoder, diagnostics)
        config = default_retrieval_config(
            "embeddings", enriched, "researchlens.representation_experiments.RepresentedRetriever"
        )
        result = run_evaluation(
            dataset,
            enriched,
            retriever,
            config,
            evidence_labels=labels,
            execution=ExecutionConfig(repeats=3, warmups=1, measure_memory=True),
            cutoffs=[1, 4],
        )
        (directory / "run.json").write_bytes(encoded(result))
        (directory / "review.json").write_bytes(
            encoded(review_template(result).model_dump(mode="json"))
        )
        (directory / "report.md").write_text(comparison_report([result], [None]), encoding="utf-8")
        candidate_run = run_evaluation(
            dataset,
            enriched,
            retriever,
            config.model_copy(update={"limit": 40}),
            evidence_labels=labels,
            execution=ExecutionConfig(repeats=1, warmups=0),
            cutoffs=[4, 20, 40],
        )
        (directory / "candidate-run.json").write_bytes(encoded(candidate_run))
        print(f"Evaluated enriched representation: {representation}", flush=True)


if __name__ == "__main__":
    main()
