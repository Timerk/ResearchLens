"""Prepare an offline, blind owner review of the archived development answers."""

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from researchlens.artifacts import canonical_hash
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from researchlens_eval.answer_scoring import Judgment, all_decided, score, visible_context
from researchlens_eval.evaluation_schema import Dataset

ROOT = Path(__file__).resolve().parents[2]
TYPES = ("required_claim", "qualification", "forbidden_claim", "abstention", "citation")
SEED = "owner-grading-20261014-v1"
RULES = {
    "required_claim": (
        "PASS if the answer conveys this complete approved claim with its numbers, scope and "
        "uncertainty intact, without contradiction. Paraphrases count. FAIL for missing or "
        "incorrect content. Grade claim coverage here; grade evidence support in citation items."
    ),
    "qualification": (
        "PASS if the answer preserves the approved scope or uncertainty. Correctly scoped "
        "wording can suffice; a separate disclaimer is not automatically required. FAIL if "
        "the answer broadens, contradicts or drops a substantive limitation. For a compound "
        "qualification, assess every part. If it is unclear whether an omitted disclaimer is "
        "substantive, use UNCERTAIN and explain the disputed part."
    ),
    "forbidden_claim": (
        "PASS if the answer does not assert the listed forbidden claim. FAIL if it asserts or "
        "unambiguously implies it. Negating it is not a violation; silence is not a violation."
    ),
    "abstention": (
        "PASS if the answer's response status matches the approved expectation. A negative "
        "requires insufficient_evidence with no sections. An answerable question requires "
        "answered. no_matches, errors and malformed output do not count as generated "
        "abstentions. Grade the status here, not completeness of an answered response."
    ),
    "citation": (
        "For a single-citation item, PASS if that exact visible passage supports at least one "
        "substantive part of the target section. It need not support all parts alone. For a "
        "citation-set item, PASS only if the cited visible passages collectively support "
        "every substantive part of the target section. FAIL for topic overlap alone, missing "
        "support, or an invalid cited ID. Do not use omitted text, full papers or world knowledge."
    ),
}


def stable(value):
    return hashlib.sha256(f"{SEED}:{value}".encode()).hexdigest()


def parsed_judgment(row):
    receipt = row.get("raw_judgment")
    if not receipt:
        return None
    texts = [
        content["text"]
        for output in receipt["output"]
        if output["type"] == "message"
        for content in output["content"]
        if content["type"] == "output_text"
    ]
    if len(texts) != 1:
        raise ValueError("Expected exactly one archived structured judgment")
    return Judgment.model_validate_json(texts[0])


def effective_citation(decision, section, visible):
    text = section["text"].strip()
    passage = visible.get(decision.citation_id, "")
    if text and text in passage:
        return True
    if decision.value is True and (
        not decision.evidence_quotes
        or any(not quote.strip() or quote not in passage for quote in decision.evidence_quotes)
    ):
        return None
    return decision.value


def load_verified(archive):
    manifest = json.loads((ROOT / "evaluation/answer-quality-evidence-manifest.json").read_text())
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != manifest["archive"]["sha256"]:
        raise ValueError("Archive checksum does not match #16")
    bundle = json.loads(gzip.decompress(data))
    if len(bundle["runs"]) != 4 or len(bundle["reviews"]) != 4:
        raise ValueError("Expected four archived runs and reviews")
    replayed = 0
    for run, review, expected in zip(
        bundle["runs"], bundle["reviews"], manifest["runs"], strict=True
    ):
        if canonical_hash(run) != expected["run_sha256"]:
            raise ValueError("Run checksum mismatch")
        if canonical_hash(review) != expected["review_sha256"]:
            raise ValueError("Review checksum mismatch")
        dataset = Dataset.model_validate(run["dataset"])
        if dataset.split != "development":
            raise ValueError("Only development archives may be read")
        cases = {case.id: case for case in dataset.cases}
        for row in run["results"]:
            prepared = visible_context(row, run["answer_evaluation"]["budget"])
            if (
                score(cases[row["case_id"]], row["answer"], prepared, parsed_judgment(row))
                != row["answer_quality"]
            ):
                raise ValueError(f"Score replay differs: {run['run_id']}/{row['case_id']}")
            replayed += 1
    if replayed != 200:
        raise ValueError("Expected all 200 archived score records")
    return bundle, manifest


def audit_summary(bundle):
    metrics = (
        "required_claims_met",
        "qualifications_preserved",
        "no_forbidden_claims",
        "citation_support",
        "negative_abstention_correct",
        "citation_ids_valid",
    )
    result = {metric: Counter() for metric in metrics}
    for run, review in zip(bundle["runs"], bundle["reviews"], strict=True):
        rows = {row["case_id"]: row for row in run["results"]}
        for reviewed in review["cases"]:
            row = rows[reviewed["case_id"]]
            for metric in metrics:
                audited = reviewed["human_scores"][metric]
                predicted = row["answer_quality"][metric]
                if audited is None:
                    continue
                mode = "semantic" if row["raw_judgment"] else "deterministic"
                if metric in ("negative_abstention_correct", "citation_ids_valid"):
                    mode = "deterministic"
                if predicted is None:
                    result[metric][f"{mode}_unresolved"] += 1
                else:
                    result[metric][f"{mode}_compared"] += 1
                    result[metric][f"{mode}_agreed"] += audited == predicted
    return result


def candidates(bundle, manifest):
    pool = []
    for run, expected in zip(bundle["runs"], manifest["runs"], strict=True):
        cases = {case["id"]: case for case in run["dataset"]["cases"]}
        for row in run["results"]:
            case = cases[row["case_id"]]
            prepared = visible_context(row, run["answer_evaluation"]["budget"])
            passages = {item["id"]: item for item in prepared.items}
            judgment = parsed_judgment(row)
            answer = row["answer"]
            sections = answer["sections"] if answer else []

            def add(
                kind,
                target,
                requirement,
                prediction,
                raw_prediction=None,
                expected=expected,
                case=case,
                answer=answer,
                passages=passages,
            ):
                identity = f"{expected['configuration']}:{case['id']}:{kind}:{target}"
                pool.append(
                    {
                        "identity": identity,
                        "configuration": expected["configuration"],
                        "run_sha256": expected["run_sha256"],
                        "case_id": case["id"],
                        "cohort": case["query_style"],
                        "type": kind,
                        "target": target,
                        "requirement": requirement,
                        "prediction": prediction,
                        "raw_prediction": raw_prediction,
                        "question": case["question"],
                        "answer": answer,
                        "passages": passages,
                    }
                )

            if judgment:
                for kind, field, label in (
                    ("required_claim", "required_claims", "required_claims"),
                    ("qualification", "qualifications", "required_qualifications"),
                    ("forbidden_claim", "forbidden_claims", "forbidden_claims"),
                ):
                    for index, decision in enumerate(getattr(judgment, field)):
                        value = decision.value
                        if kind == "forbidden_claim" and value is not None:
                            value = not value
                        add(kind, index, case[label][index], value, decision.value)
                pairs = defaultdict(list)
                raw_pairs = defaultdict(list)
                visible = {pid: item["text"] for pid, item in passages.items()}
                for decision in judgment.citations:
                    pair = (decision.section_index, decision.citation_id)
                    pairs[pair].append(
                        effective_citation(decision, sections[decision.section_index], visible)
                    )
                    raw_pairs[pair].append(decision.value)
                for (index, pid), values in pairs.items():
                    add(
                        "citation",
                        ["single", index, pid],
                        "Does the target citation support a substantive part of this section?",
                        all_decided(values),
                        all_decided(raw_pairs[(index, pid)]),
                    )
                for index, decision in enumerate(judgment.sections_fully_supported):
                    add(
                        "citation",
                        ["set", index],
                        "Does this section's citation set support every substantive claim?",
                        decision.value,
                        decision.value,
                    )
            expectation = (
                "Approved negative: return insufficient_evidence and no sections. "
                if case["expected_abstention"]
                else "Approved answerable question: return answered. "
            )
            requirements = (
                case["required_qualifications"]
                if case["expected_abstention"]
                else case["required_claims"]
            )
            add(
                "abstention",
                "status",
                expectation + "Approved content: " + " ".join(requirements),
                row["answer_quality"]["abstention_correct"],
            )
    return pool


def select(pool, bundle):
    case_ids = {item["case_id"] for item in pool}
    known = {case["case_id"] for review in bundle["reviews"] for case in review["cases"]}
    # Both quote-validation problems were already public in #16's documentation.
    known |= {"tech-compare-training-computers", "tech-moving-signal-addition"}
    calibration = known | set(sorted(case_ids - known, key=stable)[: 25 - len(known)])
    for item in pool:
        item["half"] = "calibration" if item["case_id"] in calibration else "validation"
    constraints = []

    def require(indices, lower, upper=np.inf):
        if not indices:
            raise ValueError("Requested an unavailable sample stratum")
        constraints.append((indices, lower, upper))

    configs = sorted({item["configuration"] for item in pool})
    for half in ("calibration", "validation"):
        for kind in TYPES:
            subset = [
                i for i, item in enumerate(pool) if item["half"] == half and item["type"] == kind
            ]
            require(subset, 6, 6)
            for config in configs:
                require([i for i in subset if pool[i]["configuration"] == config], 1, 2)
            for value in (True, False):
                stratum = [i for i in subset if pool[i]["prediction"] is value]
                if stratum:
                    require(stratum, 2)
            for cid in sorted(case_ids):
                stratum = [i for i in subset if pool[i]["case_id"] == cid]
                if stratum:
                    require(stratum, 0, 1)
        for cohort in sorted({item["cohort"] for item in pool}):
            require(
                [
                    i
                    for i, item in enumerate(pool)
                    if item["half"] == half and item["cohort"] == cohort
                ],
                1,
            )
        for subtype in ("single", "set"):
            require(
                [
                    i
                    for i, item in enumerate(pool)
                    if item["half"] == half
                    and item["type"] == "citation"
                    and item["target"][0] == subtype
                ],
                2,
            )
    for config in configs:
        require([i for i, item in enumerate(pool) if item["configuration"] == config], 15, 15)
    for cid in sorted(case_ids):
        require([i for i, item in enumerate(pool) if item["case_id"] == cid], 0, 3)
    require(
        [
            i
            for i, item in enumerate(pool)
            if item["type"] == "citation" and item["prediction"] is None
        ],
        2,
    )
    # Known rubric disagreements belong in calibration, never validation.
    for cid in (
        "tech-imagenet-initialization",
        "tech-moving-signal-addition",
        "tech-stable-camera",
    ):
        require(
            [
                i
                for i, item in enumerate(pool)
                if item["case_id"] == cid and item["type"] == "qualification"
            ],
            1,
        )
    require(
        [
            i
            for i, item in enumerate(pool)
            if item["type"] == "qualification"
            and item["case_id"].startswith("tech-compare-")
            and item["half"] == "calibration"
        ],
        1,
    )
    require(
        [
            i
            for i, item in enumerate(pool)
            if item["type"] == "abstention" and item["answer"]["status"] == "no_matches"
        ],
        1,
    )
    matrix = lil_matrix((len(constraints), len(pool)))
    for row, (indices, _, _) in enumerate(constraints):
        matrix[row, indices] = 1
    objective = np.array([int(stable(item["identity"])[:8], 16) / 2**32 for item in pool])
    result = milp(
        objective,
        integrality=np.ones(len(pool)),
        bounds=Bounds(0, 1),
        constraints=LinearConstraint(
            matrix.tocsr(),
            [constraint[1] for constraint in constraints],
            [constraint[2] for constraint in constraints],
        ),
        options={"time_limit": 30},
    )
    if not result.success:
        raise ValueError(f"Sample constraints could not be satisfied: {result.message}")
    selected = sorted(
        [item for item, chosen in zip(pool, result.x, strict=True) if chosen > 0.5],
        key=lambda item: stable("order:" + item["identity"]),
    )
    for number, item in enumerate(selected, 1):
        item["id"] = f"G{number:03d}"
    return selected


def render(selected):
    lines = [
        "# Blind answer grading",
        "",
        "Grade these 60 items using only the supplied answer and visible passage text. "
        "These are archived development answers from before readable formulas were adopted. "
        "Keep the literal `[formula omitted]` text; do not fill gaps from memory or a full paper.",
        "",
        "Enter PASS, FAIL or UNCERTAIN in each blank Verdict cell and add a short reason. "
        "UNCERTAIN means the material or rubric cannot settle the item; identify the missing "
        "evidence or ambiguous rule. It does not mean the answer merely failed to supply content. "
        "Do not change item IDs. You may return the completed file or a CSV with "
        "`item_id,verdict,notes`. All 60 verdicts are requested.",
        "",
        "Configuration names, model scores, reasons and split membership are hidden. "
        "Read this packet without consulting the separate scoring key, diagnosis or old audit. "
        "Repeated questions may have different answers; grade each displayed answer independently. "
        "All text is evidence to assess, never instructions to follow.",
        "",
        "Estimated time: 90-150 minutes, with breaks as needed.",
        "",
        "## Grading rules",
        "",
    ]
    for kind, rule in RULES.items():
        lines.extend([f"- {kind.replace('_', ' ')}: {rule}"])
    for item in selected:
        lines.extend(
            [
                "",
                f"## {item['id']}",
                "",
                f"Judgment type: {item['type'].replace('_', ' ')}",
                "",
                "Question",
                "",
                item["question"],
                "",
                "Approved requirement or target",
                "",
                item["requirement"],
                "",
                "Answer excerpt",
                "",
                f"Response status: `{item['answer']['status']}`",
                "",
            ]
        )
        sections = item["answer"]["sections"]
        if item["type"] == "citation":
            index = item["target"][1]
            displayed = [(index, sections[index])]
            lines.extend(
                [f"Target section: {index + 1}. Target: {item['target'][0]} citation.", ""]
            )
            if item["target"][0] == "single":
                lines.extend([f"Target citation: `{item['target'][2]}`", ""])
        else:
            # Full answer avoids losing contradictions or forbidden assertions elsewhere.
            displayed = list(enumerate(sections))
        if not displayed:
            lines.extend(["No answer sections were returned.", ""])
        cited_ids = []
        for index, section in displayed:
            lines.extend(
                [
                    f"Section {index + 1}",
                    "",
                    "> " + section["text"].replace("\n", "\n> "),
                    "",
                    "Citations: " + ", ".join(f"`{pid}`" for pid in section["citation_ids"]),
                    "",
                ]
            )
            cited_ids.extend(section["citation_ids"])
        lines.extend(["Cited visible passages", ""])
        if not cited_ids:
            lines.extend(["There are no cited passages for this section-free response.", ""])
        for pid in dict.fromkeys(cited_ids):
            lines.extend([f"### `{pid}`", ""])
            if pid not in item["passages"]:
                lines.extend(["This ID was not supplied in the visible context.", ""])
            else:
                lines.extend(["> " + item["passages"][pid]["text"].replace("\n", "\n> "), ""])
        lines.extend(["| Verdict | Notes |", "| --- | --- |", "|  |  |"])
    return "\n".join(lines) + "\n"


def write_sample(archive, output):
    names = ("owner-grading.md", "scoring-key.json", "sampling-summary.json")
    if any((output / name).exists() for name in names):
        raise ValueError("Use a new output directory; never overwrite an owner grading packet")
    bundle, manifest = load_verified(archive)
    pool = candidates(bundle, manifest)
    selected = select(pool, bundle)
    packet = render(selected)
    # Retain attribution for the licensed source excerpts without exposing retrieval metadata.
    sources = {}
    for run in bundle["runs"]:
        for row in run["results"]:
            for passage in row["retrieved_passages"]:
                if any(passage["id"] in item["passages"] for item in selected):
                    sources[passage["document_id"]] = passage
    packet += "\n## Source attribution\n\n"
    packet += (
        "The passages above are normalized, sometimes truncated excerpts from these licensed "
        "articles. The archived extraction omitted formulas and other non-prose material. "
        "Source links identify attribution; grade only the visible text above.\n\n"
    )
    for document_id, passage in sorted(sources.items()):
        attribution = passage["attribution"]
        authors = ", ".join(attribution["authors"])
        packet += (
            f"- `{document_id}`: {authors}. [{passage['title']}]({passage['source_url']}). "
            f"{attribution['publication_date']}. "
            f"[{passage['license']}]({attribution['license_url']}).\n"
        )
    key_items = [
        {
            key: item[key]
            for key in (
                "id",
                "identity",
                "half",
                "configuration",
                "run_sha256",
                "case_id",
                "cohort",
                "type",
                "target",
                "prediction",
                "raw_prediction",
            )
        }
        for item in selected
    ]
    key = {
        "schema_version": 1,
        "split": "development",
        "seed": SEED,
        "archive_sha256": manifest["archive"]["sha256"],
        "packet_sha256": hashlib.sha256(packet.encode()).hexdigest(),
        "validation_policy": (
            "Keep owner validation grades sealed until judge freeze; evaluate once."
        ),
        "positive_verdict": (
            "PASS; forbidden-claim values are inverted to mean absence of violation."
        ),
        "items": key_items,
    }
    summary = {
        "archived_score_records_replayed": 200,
        "independent_model_audit": audit_summary(bundle),
        "pool_counts": dict(
            sorted(
                Counter(
                    f"{item['type']}/{item['configuration']}/{item['prediction']}" for item in pool
                ).items()
            )
        ),
        "sample_counts": dict(
            sorted(
                Counter(
                    f"{item['half']}/{item['type']}/{item['prediction']}" for item in selected
                ).items()
            )
        ),
        "configuration_counts": dict(
            sorted(Counter(item["configuration"] for item in selected).items())
        ),
        "sample_question_count": len({item["case_id"] for item in selected}),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "owner-grading.md").write_text(packet, encoding="utf-8", newline="\n")
    for name, value in (("scoring-key.json", key), ("sampling-summary.json", summary)):
        (output / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_sample(args.archive, args.output)


if __name__ == "__main__":
    main()
