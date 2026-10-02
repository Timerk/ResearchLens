"""Reproduce this study's CPU float32 reference check from saved development runs.

Run from the repository root after the GPU comparison, with cached pinned assets.
This diagnostic compares rankings, not answerability or controlled CPU/GPU speed.
"""

import json
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoModelForSequenceClassification, AutoTokenizer

sys.path.insert(0, "backend")
from researchlens.vulkan_reranking import MODELS, QWEN_TEMPLATE

root = Path(".venv/vulkan")
runs = Path("evaluation/runs/vulkan-rerankers-cache-off-2026-10-02")
dataset = json.loads(Path("evaluation/datasets/technical-development.json").read_bytes())
assert dataset["split"] == "development"
assert all(case["review_status"] == "approved" for case in dataset["cases"])
selected = {}
for case in dataset["cases"]:
    selected.setdefault(case["query_style"], case)
cases = list(selected.values())
specs = json.loads((root / "models.json").read_bytes())
artifact = json.loads(
    Path("evaluation/runs/approved-models-2026-10-01-k4/indexes/qwen3-4b.json").read_bytes()
)
passages = {p["id"]: p for p in artifact["passages"]}
positions = {p["id"]: i for i, p in enumerate(artifact["passages"])}
torch.set_num_threads(8)
torch.set_num_interop_threads(1)
archive = {
    "case_selection": "First development case in each query-style cohort, independent of scores",
    "case_ids": [c["id"] for c in cases],
    "reference_precision": "float32",
    "batch_size": 4,
    "results": {},
}
for alias, spec in specs.items():
    assert (spec["model"], spec["revision"]) == MODELS[alias]
    tokenizer = AutoTokenizer.from_pretrained(
        spec["source"],
        local_files_only=True,
        trust_remote_code=False,
        padding_side="left" if alias == "qwen" else "right",
    )
    factory = AutoModelForCausalLM if alias == "qwen" else AutoModelForSequenceClassification
    model = factory.from_pretrained(
        spec["source"],
        local_files_only=True,
        trust_remote_code=False,
        dtype=torch.float32,
        attn_implementation="sdpa",
    ).eval()
    if alias == "qwen":
        tokenizer.pad_token = tokenizer.eos_token
    run = json.loads((runs / f"qwen3-4b-{alias}-rerank20" / "run.json").read_bytes())
    by_id = {r["case_id"]: r for r in run["results"]}
    records = []
    for case in cases:
        row = by_id[case["id"]]
        ids = [p["passage_id"] for p in row["reranker_passage_diagnostics"]]
        docs = [passages[p]["text"] for p in ids]
        scores = []
        token_counts = []
        started = time.perf_counter()
        for start in range(0, len(docs), 4):
            batch = docs[start : start + 4]
            if alias == "qwen":
                texts = [
                    QWEN_TEMPLATE.format(query=case["question"], document=doc) for doc in batch
                ]
                inputs = tokenizer(
                    texts,
                    add_special_tokens=False,
                    padding=True,
                    truncation=False,
                    return_tensors="pt",
                )
                with torch.inference_mode():
                    logits = model(**inputs, use_cache=False, logits_to_keep=1).logits[:, -1, :]
                    labels = [
                        tokenizer.convert_tokens_to_ids("no"),
                        tokenizer.convert_tokens_to_ids("yes"),
                    ]
                    values = torch.softmax(logits[:, labels].float(), dim=1)[:, 1]
            else:
                inputs = tokenizer(
                    [(case["question"], doc) for doc in batch],
                    padding=True,
                    truncation=False,
                    return_tensors="pt",
                )
                with torch.inference_mode():
                    values = model(**inputs).logits.view(-1).float()
            scores.extend(values.tolist())
            token_counts.extend(inputs["attention_mask"].sum(1).tolist())
        cpu_ms = 1000 * (time.perf_counter() - started)
        assert token_counts == [p["input_tokens"] for p in row["reranker_passage_diagnostics"]]
        ordered = sorted(range(len(ids)), key=lambda i: (-scores[i], positions[ids[i]]))
        cpu_top = [ids[i] for i in ordered[:4]]
        gpu_top = row["retrieved_passage_ids"]
        differences = [
            abs(hit["score"] - scores[ids.index(hit["id"])]) for hit in row["retrieved_passages"]
        ]
        records.append(
            {
                "case_id": case["id"],
                "cohort": case["query_style"],
                "candidate_ids": ids,
                "cpu_scores": scores,
                "cpu_top4": cpu_top,
                "gpu_top4": gpu_top,
                "top4_order_identical": cpu_top == gpu_top,
                "top4_set_identical": set(cpu_top) == set(gpu_top),
                "max_abs_difference_on_gpu_top4": max(differences),
                "cpu_reranking_ms_single_sample": cpu_ms,
            }
        )
        print(alias, case["id"], cpu_top == gpu_top, max(differences), round(cpu_ms, 1), flush=True)
    archive["results"][alias] = records
    (root / "reference-development.json").write_text(
        json.dumps(archive, indent=2) + "\n", encoding="utf-8"
    )
    del model
