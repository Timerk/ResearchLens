"""Small cached Qwen4B parity check against documented left-padding reference pooling.

No model download, held-out questions, GPU server or paid API. From repo root:
uv run --extra embedding-models python evaluation/scripts/embedding-parity-check.py
    --output <new-json-path>
"""

import argparse
import gc
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from researchlens.artifacts import canonical_hash  # noqa: E402
from researchlens.embedding_models import TorchEncoder  # noqa: E402


def main(output):
    dataset_path = Path("evaluation/datasets/technical-development.json")
    dataset = json.loads(dataset_path.read_bytes())
    if dataset["split"] != "development" or any(
        c["review_status"] != "approved" for c in dataset["cases"]
    ):
        raise ValueError("Use approved development questions only")
    artifact = json.loads(
        Path("evaluation/runs/approved-models-2026-10-01-k4/indexes/qwen3-4b.json").read_bytes()
    )
    cohorts = {}
    for case in dataset["cases"]:
        if not case["expected_abstention"]:
            cohorts.setdefault(case["query_style"], case)
    cases = list(cohorts.values())
    ids = []
    for case in cases:
        ids.append(next(r["passage_id"] for r in case["references"] if r["passage_id"] not in ids))
    by_id = {p["id"]: i for i, p in enumerate(artifact["passages"])}
    documents = [artifact["passages"][by_id[pid]]["text"] for pid in ids]
    encoding = artifact["embeddings"]["encoding"]
    queries = [encoding["query_prefix"] + c["question"] for c in cases]
    encoder = TorchEncoder(encoding)
    torch = encoder.torch
    ours = encoder.encode(queries + documents)
    encoder.tokenizer.padding_side = "left"
    tokens = encoder.tokenizer(
        queries + documents,
        padding=True,
        truncation=True,
        max_length=encoding["max_tokens"],
        return_tensors="pt",
    )
    # Official Qwen helper takes the final hidden state when the batch is left padded.
    with torch.inference_mode():
        hidden = encoder.model(**tokens, use_cache=False).last_hidden_state
        reference = torch.nn.functional.normalize(hidden[:, -1, :].float(), p=2, dim=1)
    reference = reference.numpy()
    vectors = np.asarray(artifact["embeddings"]["vectors"])[[by_id[pid] for pid in ids]]
    ours_rank = np.argsort(-(ours[:3] @ vectors.T), axis=1).tolist()
    reference_rank = np.argsort(-(reference[:3] @ vectors.T), axis=1).tolist()
    result = {
        "model": encoding,
        "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "artifact_sha256": canonical_hash(artifact),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "case_selection": "first answerable development question per query-style cohort",
        "case_ids": [c["id"] for c in cases],
        "passage_ids": ids,
        "reference": "documented Qwen left-padding, final-token pooling, L2 normalization",
        "instruction": "same task-specific research-question instruction in both paths",
        "same_loaded_model": True,
        "ours_batch_size": encoding["batch_size"],
        "reference_batch_size": len(queries + documents),
        "cosines_ours_vs_reference": (ours * reference).sum(axis=1).tolist(),
        "cosines_reencoded_documents_vs_saved": (ours[3:] * vectors).sum(axis=1).tolist(),
        "our_document_rankings": ours_rank,
        "reference_document_rankings": reference_rank,
        "rankings_identical": ours_rank == reference_rank,
        "held_out_searches": False,
        "api_calls": 0,
        "limitation": "small same-precision sample, not general equivalence or quality evaluation",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))
    del encoder
    gc.collect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args().output)
