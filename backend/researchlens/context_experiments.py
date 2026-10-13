"""Development-only context study, replaying pinned rankings through the existing runner."""

import argparse
import hashlib
from pathlib import Path

from researchlens.artifacts import canonical_hash, load_artifact
from researchlens.context_evaluation import STANDARD_BUDGETS, context_paired, context_summary
from researchlens.evaluation import (
    code_state,
    comparison_report,
    default_retrieval_config,
    encoded,
    load_dataset,
    review_template,
    run_evaluation,
    validate_artifact,
)
from researchlens.evaluation_evidence import EvidenceLabels, validate_labels
from researchlens.evaluation_schema import RetrievalConfig
from researchlens.ingest import ROOT, TECHNICAL_CORPUS
from researchlens.models import SearchHit
from researchlens.reranking import RerankedRetriever
from researchlens.selection_diagnostics import load_run
from researchlens.vulkan_reranking import VulkanReranker


class ArchivedRetriever:
    """Replay only validated question/ranking pairs; no model or held-out search."""

    def __init__(self, run: dict, passages):
        self.passages = passages
        self.limit = run["retrieval"]["limit"]
        questions = {c["id"]: c["question"] for c in run["dataset"]["cases"]}
        self.rows = {questions[r["case_id"]]: r for r in run["results"]}
        self.encoding_diagnostics = run.get("encoding_diagnostics")

    def search(self, question: str, limit: int = 4) -> list[SearchHit]:
        row = self.rows[question]
        if self.limit < limit:
            raise ValueError("Archive cannot supply requested candidate depth")
        return [SearchHit.model_validate(p) for p in row["retrieved_passages"][:limit]]

    def get_encoding_diagnostics(self):
        return self.encoding_diagnostics

    def get_reranking_diagnostics(self, question):
        return self.rows[question].get("reranker_passage_diagnostics") or []


def study(args):
    args.output = args.output.resolve()
    dataset = load_dataset(args.dataset)
    labels = EvidenceLabels.model_validate_json(args.evidence_labels.read_bytes())
    if (
        dataset.split != "development"
        or any(c.review_status != "approved" for c in dataset.cases)
        or labels.review_status != "approved"
    ):
        raise ValueError("Use approved development questions and labels only")
    paths = {
        "tfidf": args.archives / "retrieval-improvements-2026-10-02/tfidf/run.json",
        "qwen3-4b-dense": args.archives
        / "retrieval-improvements-2026-10-02/qwen3-4b-dense/run.json",
        "bge-m3-dense": args.archives / "retrieval-improvements-2026-10-02/bge-m3-dense/run.json",
        "bge-m3-bge-rerank20": args.archives
        / "vulkan-rerankers-cache-off-2026-10-02/bge-m3-bge-rerank20/run.json",
    }
    models = {
        "tfidf": "tfidf",
        "qwen3-4b-dense": "qwen3-4b",
        "bge-m3-dense": "bge-m3",
        "bge-m3-bge-rerank20": "bge-m3",
    }
    if args.rerank40_archive:
        paths["bge-m3-bge-rerank40"] = args.rerank40_archive.resolve()
        models["bge-m3-bge-rerank40"] = "bge-m3"
    artifacts, passages, runs = {}, {}, {}
    for name, path in paths.items():
        model = models[name]
        if model not in artifacts:
            artifact, shared = load_artifact(
                args.indexes / f"{model}.json", source=TECHNICAL_CORPUS
            )
            validate_artifact(dataset, artifact)
            validate_labels(labels, dataset, artifact, shared)
            artifacts[model], passages[model] = artifact, shared
        run, _ = load_run(path, dataset, artifacts[model], passages[model])
        if run["evaluation_contract"]["evidence_labels_sha256"] != canonical_hash(
            labels.model_dump(mode="json")
        ):
            raise ValueError("Archived labels differ from approved labels")
        expected = 4 if name.endswith("rerank20") else 40
        if run["retrieval"]["limit"] != expected or any(
            len(r["retrieved_passages"]) > expected for r in run["results"]
        ):
            raise ValueError("Archive lacks the predefined ranking depth")
        if name.endswith("rerank40") and (
            (run["retrieval"].get("reranker") or {}).get("candidates") != 40
            or any(len(r["retrieved_passages"]) != 40 for r in run["results"])
        ):
            raise ValueError("Larger context requires all 40 reranked candidates")
        runs[name] = run
    plan = {
        "configurations": list(dict.fromkeys([*paths, "bge-m3-bge-rerank40"])),
        "context_budgets": STANDARD_BUDGETS,
        "rerank20_budgets": [4],
        "larger_reranking_budgets_candidates": 40,
        "selection_rule": (
            "smallest serialized budget reaching 29/36 all-group complete evidence; "
            "report all configurations"
        ),
        "per_passage_chars": 3000,
        "scoring_views": {
            "all_groups": "approved labels unchanged",
            "asked_groups": "only group IDs starting part-",
        },
    }
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema_version": 1,
        "plan": plan,
        "plan_sha256": canonical_hash(plan),
        "dataset_sha256": labels.dataset_sha256,
        "evidence_labels_sha256": canonical_hash(labels.model_dump(mode="json")),
        "input_archives": {
            name: {
                "path": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "run_id": runs[name]["run_id"],
            }
            for name, path in paths.items()
        },
        "code": code_state(),
        "source_sha256": {
            name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in (
                "answers.py",
                "context_evaluation.py",
                "context_experiments.py",
                "evaluation.py",
                "evaluation_evidence.py",
                "evaluation_metrics.py",
            )
        },
        "api_calls": 0,
        "held_out_searches": False,
        "generation": "none",
        "timing_scope": "archive replay and context preparation; not retrieval/model latency",
    }
    (args.output / "manifest.json").write_bytes(encoded(manifest))
    results = {}

    def execute(name, retriever, config, model, budgets):
        print(f"Scoring {name}", flush=True)
        result = run_evaluation(
            dataset,
            artifacts[model],
            retriever,
            config,
            evidence_labels=labels,
            context_budgets=budgets,
            cutoffs=[1, 4, config.limit],
        )
        result["context_study_provenance"] = manifest
        directory = args.output / name
        directory.mkdir()
        (directory / "run.json").write_bytes(encoded(result))
        (directory / "review.json").write_bytes(
            encoded(review_template(result).model_dump(mode="json"))
        )
        if any(r["error"] for r in result["results"]):
            raise ValueError("Study contains case errors")
        results[name] = result

    for name, run in runs.items():
        config = RetrievalConfig.model_validate(
            {
                **run["retrieval"],
                "implementation": "researchlens.context_experiments.ArchivedRetriever",
            }
        )
        execute(
            name,
            ArchivedRetriever(run, passages[models[name]]),
            config,
            models[name],
            [4] if name.endswith("rerank20") else STANDARD_BUDGETS,
        )
    # Larger budgets rerank all 40 candidates locally. No new dense queries or remote calls.
    if not args.rerank40_archive:
        base = ArchivedRetriever(runs["bge-m3-dense"], passages["bge-m3"])
        with VulkanReranker(args.runtime, "bge", args.output / "bge40-server.log") as reranker:
            retriever = RerankedRetriever(base, reranker, candidates=40)
            config = default_retrieval_config(
                "embeddings",
                artifacts["bge-m3"],
                "researchlens.reranking.RerankedRetriever",
                retriever,
            ).model_copy(update={"limit": 40})
            execute("bge-m3-bge-rerank40", retriever, config, "bge-m3", STANDARD_BUDGETS)
            (args.output / "server-memory.json").write_bytes(
                encoded({"samples": reranker.memory_samples})
            )
    (args.output / "comparison.md").write_text(
        comparison_report(list(results.values()), [None] * len(results)), encoding="utf-8"
    )
    compact = {
        "schema_version": 1,
        "manifest": manifest,
        "runs": {},
        "paired": [],
        "qualification_differences": [
            {
                "case_id": e.case_id,
                "excluded_group_ids": [g.id for g in e.groups if not g.id.startswith("part-")],
            }
            for e in labels.cases
            if any(not g.id.startswith("part-") for g in e.groups)
        ],
    }
    for name, run in results.items():
        path = args.output / name / "run.json"
        compact["runs"][name] = {
            "archive_provenance": {
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "run_id": run["run_id"],
            },
            "corpus": run["corpus"],
            "retrieval": run["retrieval"],
            "runtime": run["runtime"],
            "summaries": {
                str(b): {
                    view: context_summary(run, b, view) for view in ("all_groups", "asked_groups")
                }
                for b in run["context_budgets"]
            },
            "cases": [
                {
                    "case_id": r["case_id"],
                    "budgets": {
                        b: {
                            "passage_ids": p["context"]["passage_ids"],
                            "serialized_chars": p["context"]["serialized_chars"],
                            "input_tokens_estimate": p["input_tokens_estimate"],
                            "views": {
                                v: {
                                    "complete_evidence": p[v]["complete_evidence"],
                                    "group_coverage": p[v]["group_coverage"],
                                    "missing_group_ids": [
                                        g["group_id"]
                                        for g in p[v]["groups"]
                                        if g["covered"] is False
                                    ],
                                }
                                for v in ("all_groups", "asked_groups")
                            },
                        }
                        for b, p in r["context_profiles"].items()
                    },
                }
                for r in run["results"]
            ],
        }
        for b in run["context_budgets"]:
            if b != 4:
                compact["paired"].append(
                    {
                        "baseline": name,
                        "candidate": name,
                        "before_budget": 4,
                        "after_budget": b,
                        "views": {
                            v: context_paired(run, run, 4, b, v)
                            for v in ("all_groups", "asked_groups")
                        },
                    }
                )
    names = list(results)
    for i, before in enumerate(names):
        for after in names[i + 1 :]:
            for b in set(results[before]["context_budgets"]) & set(
                results[after]["context_budgets"]
            ):
                compact["paired"].append(
                    {
                        "baseline": before,
                        "candidate": after,
                        "before_budget": b,
                        "after_budget": b,
                        "views": {
                            v: context_paired(results[before], results[after], b, b, v)
                            for v in ("all_groups", "asked_groups")
                        },
                    }
                )
    (args.output / "summary.json").write_bytes(encoded(compact))
    return compact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archives", type=Path, required=True)
    parser.add_argument("--indexes", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument(
        "--rerank40-archive",
        type=Path,
        help="Replay a validated, complete 40-candidate reranking run",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--dataset", type=Path, default=ROOT / "evaluation/datasets/technical-development.json"
    )
    parser.add_argument(
        "--evidence-labels",
        type=Path,
        default=ROOT / "evaluation/labels/technical-development.json",
    )
    args = parser.parse_args()
    study(args)


if __name__ == "__main__":
    main()
