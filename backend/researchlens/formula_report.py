"""Summarize an explicitly authorized corpus intervention, not a same-corpus model trial."""

import argparse
import json
from pathlib import Path
from statistics import mean

from researchlens.artifacts import canonical_hash
from researchlens.context_evaluation import context_paired
from researchlens.evaluation import encoded
from researchlens.evaluation_evidence import CaseEvidence, ranking_metrics
from researchlens.evaluation_metrics import exact_mcnemar
from researchlens.evaluation_schema import Case
from researchlens.formula_prototype import digest
from researchlens.ingest import ROOT
from researchlens.models import SearchHit


def scored_context(run: dict, budget: int) -> dict:
    labels = {e["case_id"]: CaseEvidence.model_validate(e) for e in run["evidence_labels"]["cases"]}
    cases = {c["id"]: Case.model_validate(c) for c in run["dataset"]["cases"]}
    rows = {}
    for row in run["results"]:
        case = cases[row["case_id"]]
        if case.expected_abstention:
            continue
        if row["error"]:
            raise ValueError("Case error prevents a complete corpus comparison")
        profile = row["context_profiles"][str(budget)]
        hits_by_id = {p["id"]: SearchHit.model_validate(p) for p in row["retrieved_passages"]}
        hits = [hits_by_id[pid] for pid in profile["context"]["passage_ids"]]
        metrics = ranking_metrics(case, hits, labels[case.id])
        rows[case.id] = {
            "reference_recall": metrics["passage_recall"],
            "evidence_hit": metrics["first_relevant_rank"] is not None,
            "first_relevant_rank": metrics["first_relevant_rank"],
            "reciprocal_rank": metrics["reciprocal_rank"],
            "both_sources": metrics["all_sources"] if len(case.expected_source_ids) > 1 else None,
            "complete": profile["all_groups"]["complete_evidence"],
            "group_coverage": profile["all_groups"]["group_coverage"],
            "missing_groups": [
                g["group_id"] for g in profile["all_groups"]["groups"] if not g["covered"]
            ],
            "passage_ids": profile["context"]["passage_ids"],
            "serialized_chars": profile["context"]["serialized_chars"],
            "neighborhood_ranks_top40": {
                p["id"]: i
                for i, p in enumerate(row["retrieved_passages"], 1)
                if p["document_id"] == "pmc11121878" and p["paragraph"] in (29, 30, 31, 32)
            }
            if case.id == "tech-changing-neighborhood"
            else None,
        }
    return rows


def targets(rows):
    values = list(rows.values())
    sources = [r["both_sources"] for r in values if r["both_sources"] is not None]
    result = {
        "answerable_cases": len(values),
        "reference_recall": mean(r["reference_recall"] for r in values),
        "evidence_hit_cases": sum(r["evidence_hit"] for r in values),
        "evidence_hit_rate": mean(r["evidence_hit"] for r in values),
        "complete_cases": sum(r["complete"] for r in values),
        "complete_rate": mean(r["complete"] for r in values),
        "both_sources_cases": sum(sources),
        "cross_document_cases": len(sources),
        "both_sources_rate": mean(sources),
        "mrr": mean(r["reciprocal_rank"] for r in values),
    }
    result["targets_met"] = {
        name: result[name] >= threshold
        for name, threshold in {
            "reference_recall": 0.8,
            "evidence_hit_rate": 0.9,
            "complete_rate": 0.8,
            "both_sources_rate": 0.9,
            "mrr": 0.65,
        }.items()
    }
    return result


def report(candidate: Path, output: Path, publish: bool = False):
    remapping = json.loads((candidate / "remapping.json").read_bytes())
    if any(r["status"] == "cannot map" for r in remapping["records"]):
        raise ValueError("Cannot score unresolved candidate labels")
    compact = {
        "schema_version": 1,
        "api_calls": 0,
        "held_out_searches": 0,
        "status": "candidate_labels_unreviewed_owner_approval_required",
        "comparison": (
            "paired development corpus intervention; original evidence requirements retained"
        ),
        "scoring": (
            "Reference recall is mean legacy reference-ID recall; hit and MRR use "
            "evidence passage IDs "
            "within supplied context, as in the existing study. Complete uses visible quote spans, "
            "all groups and every AND fragment. Character budgets use exact "
            "provider serialization. "
            "Candidate reference IDs are retained, validated at the same source locations; "
            "legacy reference recall does not establish unchanged window content."
        ),
        "candidate_summary": json.loads((candidate / "summary.json").read_bytes()),
        "manifest": json.loads((output / "manifest.json").read_bytes()),
        "models": {},
    }
    lines = [
        "# Readable formulas development results",
        "",
        "These are provisional results on unreviewed candidate span mappings. "
        "All 36 answerable development cases and 14 unscored negatives ran locally. "
        "No generation, paid API call or held-out retrieval ran.",
        "",
        compact["scoring"],
        "",
        "## Five retrieval targets",
        "",
        "Thresholds are reference recall 80%, evidence hit 90%, complete evidence 80%, "
        "both sources 90% of nine cross-document cases, and MRR 0.65.",
        "",
        "| Model | Context | Corpus | Reference recall | Evidence hit /36 | "
        "Complete /36 | Both sources /9 | MRR | Targets met |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    paired_lines = [
        "",
        "## Paired exact McNemar tests",
        "",
        "Two-sided exact binomial tests. Gain/loss counts are paired question changes. "
        "Complete and hit use 36 cases, both-source tests use nine. "
        "Reference recall and MRR are continuous and have no McNemar test. "
        "No multiple-comparison correction; these are development diagnostics.",
        "",
        "| Model | Context | Outcome | Gains | Losses | p |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    case_lines = [
        "",
        "## Per-question changes",
        "",
        "Only changes in recall, hit, complete, source coverage, MRR or group coverage "
        "are listed below. The JSON summary retains all answerable question pairs. "
        "Neighborhood is listed even when scores do not change.",
        "",
        "| Model | Context | Question | Recall old/new | Hit old/new | Complete old/new | "
        "Groups old/new | MRR old/new | Missing groups old/new |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for model in ("tfidf", "bge-m3", "qwen3-4b"):
        runs = {
            v: json.loads((output / f"{model}-{v}/run.json").read_bytes())
            for v in ("canonical", "candidate")
        }
        before, after = runs["canonical"], runs["candidate"]
        # Generic comparison_report correctly rejects different corpus/label hashes.
        # This intervention instead verifies unchanged questions and evidence grouping.
        for old_case, new_case in zip(
            before["dataset"]["cases"], after["dataset"]["cases"], strict=True
        ):
            fields = set(old_case) - {"review_status", "reviewer", "review_date"}
            if any(old_case[f] != new_case[f] for f in fields):
                raise ValueError("Candidate changed the approved question contract")
        if before["retrieval"] != {
            **after["retrieval"],
            "artifact_sha256": before["retrieval"]["artifact_sha256"],
        }:
            raise ValueError("Retriever settings differ across corpora")
        if (
            after["dataset_sha256"]
            != remapping["outputs"]["development"]["candidate_dataset_sha256"]
        ):
            raise ValueError("Candidate dataset does not match offline remapping")
        if canonical_hash(after["evidence_labels"]) != canonical_hash(
            json.loads((candidate / "development-labels.json").read_bytes())
        ):
            raise ValueError("Candidate run labels differ from migration output")
        entry = {"runs": {}, "budgets": {}}
        for variant, run in runs.items():
            path = output / f"{model}-{variant}/run.json"
            entry["runs"][variant] = {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": digest(path),
                "run_id": run["run_id"],
                "retrieval": run["retrieval"],
                "dataset_sha256": run["dataset_sha256"],
                "corpus": run["corpus"],
                "runtime": run["runtime"],
                "evaluation_contract": run["evaluation_contract"],
            }
        if model != "tfidf":
            entry["index_provenance"] = json.loads(
                (output / f"{model}-index-provenance.json").read_bytes()
            )
        for budget in (4, 12000, 16000):
            rows = {v: scored_context(run, budget) for v, run in runs.items()}
            totals = {v: targets(r) for v, r in rows.items()}
            tests = {
                field: exact_mcnemar(
                    {cid: r[field] for cid, r in rows["canonical"].items()},
                    {cid: r[field] for cid, r in rows["candidate"].items()},
                )
                for field in ("complete", "evidence_hit", "both_sources")
            }
            tests["complete_asked_groups"] = context_paired(
                before, after, budget, budget, "asked_groups"
            )
            for v, total in totals.items():
                lines.append(
                    f"| {model} | {budget} | {v} | {total['reference_recall']:.1%} | "
                    f"{total['evidence_hit_cases']} | {total['complete_cases']} | "
                    f"{total['both_sources_cases']} | {total['mrr']:.3f} | "
                    f"{sum(total['targets_met'].values())}/5 |"
                )
            for field, test in tests.items():
                paired_lines.append(
                    f"| {model} | {budget} | {field} | {test['gains']} | "
                    f"{test['losses']} | {test['p_two_sided']:.6g} |"
                )
            paired_cases = []
            for cid, old in rows["canonical"].items():
                new = rows["candidate"][cid]
                changed = [
                    k
                    for k in (
                        "reference_recall",
                        "evidence_hit",
                        "complete",
                        "both_sources",
                        "reciprocal_rank",
                        "group_coverage",
                    )
                    if old[k] != new[k]
                ]
                paired_cases.append(
                    {"case_id": cid, "changed_metrics": changed, "canonical": old, "candidate": new}
                )
                if changed or cid == "tech-changing-neighborhood":
                    case_lines.append(
                        f"| {model} | {budget} | {cid} | "
                        f"{old['reference_recall']:.3f}/{new['reference_recall']:.3f} | "
                        f"{old['evidence_hit']}/{new['evidence_hit']} | "
                        f"{old['complete']}/{new['complete']} | "
                        f"{old['group_coverage']:.3f}/{new['group_coverage']:.3f} | "
                        f"{old['reciprocal_rank']:.3f}/{new['reciprocal_rank']:.3f} | "
                        f"{', '.join(old['missing_groups']) or 'none'} / "
                        f"{', '.join(new['missing_groups']) or 'none'} |"
                    )
            entry["budgets"][str(budget)] = {
                "totals": totals,
                "paired_mcnemar": tests,
                "cases": paired_cases,
            }
        compact["models"][model] = entry
    lines.extend(paired_lines)
    lines.extend(case_lines)
    lines.extend(["", "## Neighborhood ranks in the top 40", ""])
    for model, entry in compact["models"].items():
        row = next(
            r
            for r in entry["budgets"]["4"]["cases"]
            if r["case_id"] == "tech-changing-neighborhood"
        )
        lines.append(
            f"- {model}: canonical {row['canonical']['neighborhood_ranks_top40']}; "
            f"candidate {row['candidate']['neighborhood_ranks_top40']}."
        )
    lines.extend(
        [
            "",
            "## Approval boundary",
            "",
            "Canonical documents, manifest, hashes, approved labels and frozen held-out "
            "dataset remain unchanged. Corpus adoption, label approval and a new held-out "
            "dataset version are owner decisions. Retrieval coverage does not establish "
            "scientific fidelity, generated-answer quality or held-out performance.",
            "",
        ]
    )
    (output / "summary.json").write_bytes(encoded(compact))
    (output / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    if publish:
        # Commit summaries, never generated corpora, indexes, rankings or full runs.
        docs = ROOT / "docs"
        (docs / "formula-rendering-results.md").write_text("\n".join(lines), encoding="utf-8")
        (docs / "formula-remapping-review.md").write_bytes(
            (candidate / "remapping-review.md").read_bytes()
        )
        small = {k: v for k, v in compact.items() if k not in {"models", "candidate_summary"}}
        small["models"] = {}
        for name, entry in compact["models"].items():
            small["models"][name] = {k: v for k, v in entry.items() if k != "budgets"}
            small["models"][name]["budgets"] = {}
            for budget, values in entry["budgets"].items():
                small["models"][name]["budgets"][budget] = {
                    "totals": values["totals"],
                    "paired_mcnemar": values["paired_mcnemar"],
                    "changes": [
                        {
                            **row,
                            **{
                                variant: {
                                    k: v for k, v in row[variant].items() if k != "passage_ids"
                                }
                                for variant in ("canonical", "candidate")
                            },
                        }
                        for row in values["cases"]
                        if row["changed_metrics"] or row["case_id"] == "tech-changing-neighborhood"
                    ],
                }
        small["implementation_sha256"] = {
            name: digest(Path(__file__).with_name(name))
            for name in ("formula_experiments.py", "formula_report.py")
        }
        (docs / "formula-rendering-results.json").write_bytes(encoded(small))
        corpus_summary = compact["candidate_summary"]
        corpus_summary["label_remapping"]["held_out_inventory"].pop("references", None)
        corpus_summary["candidate_artifacts"] = {
            "directory": candidate.relative_to(ROOT).as_posix(),
            "proposed_labels": (candidate / "development-labels.json").relative_to(ROOT).as_posix(),
            "exact_remapping": (candidate / "remapping.json").relative_to(ROOT).as_posix(),
            "exact_remapping_sha256": digest(candidate / "remapping.json"),
        }
        directory = ROOT / "data/technical/prototypes/mathml-readable-v2"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "summary.json").write_bytes(encoded(corpus_summary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--publish-summaries", action="store_true")
    args = parser.parse_args()
    report(args.candidate.resolve(), args.output.resolve(), args.publish_summaries)
