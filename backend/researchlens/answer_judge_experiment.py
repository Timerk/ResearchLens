"""Guarded calibration/validation judging of existing answers, without generation."""

import hashlib
import json

from openai import OpenAI

from researchlens.answer_evaluation import (
    CostGuard,
    Judgment,
    Prices,
    all_decided,
    judge_input,
    save,
    score,
    visible_context,
)
from researchlens.answer_grading import load_verified
from researchlens.answer_judge_review import REVIEW, agreement, load_grades
from researchlens.answer_judge_v2 import MODEL, OUTPUT_TOKENS, PROMPT, REASONING, citation_value
from researchlens.answer_study_budget import BudgetClient, StudyBudget
from researchlens.artifacts import canonical_hash
from researchlens.config import Settings
from researchlens.evaluation_evidence import EvidenceLabels
from researchlens.evaluation_schema import Dataset


def review_inputs(archive, half):
    bundle, manifest = load_verified(archive)
    key = json.loads((REVIEW / "scoring-key.json").read_bytes())
    items = [item for item in key["items"] if item["half"] == half]
    requests = []
    indexed = {}
    for run, expected in zip(bundle["runs"], manifest["runs"], strict=True):
        dataset = Dataset.model_validate(run["dataset"])
        cases = {case.id: case for case in dataset.cases}
        entries = {
            entry.case_id: entry
            for entry in EvidenceLabels.model_validate(run["evidence_labels"]).cases
        }
        for row in run["results"]:
            selected = [
                item
                for item in items
                if item["configuration"] == expected["configuration"]
                and item["case_id"] == row["case_id"]
            ]
            if not selected:
                continue
            identity = f"{expected['configuration']}:{row['case_id']}"
            prepared = visible_context(row, run["answer_evaluation"]["budget"])
            indexed[identity] = (row, prepared, cases[row["case_id"]])
            if row["answer"]["sections"]:
                payload = judge_input(
                    cases[row["case_id"]], row["answer"], prepared, entries.get(row["case_id"])
                )
                requests.append({"id": identity, "payload": json.dumps(payload)})
    return items, requests, indexed


def review_plan(archive, half, prices):
    items, requests, _ = review_inputs(archive, half)
    import tiktoken

    tokenizer = tiktoken.get_encoding("o200k_base")
    return {
        "schema_version": 1,
        "mode": "judge-review",
        "half": half,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "key_sha256": hashlib.sha256((REVIEW / "scoring-key.json").read_bytes()).hexdigest(),
        "model": MODEL,
        "reasoning": REASONING,
        "max_output_tokens": OUTPUT_TOKENS,
        "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
        "schema_sha256": canonical_hash(Judgment.model_json_schema()),
        "prices": prices.model_dump(),
        "items": [item["id"] for item in items],
        "requests": [
            {
                "id": request["id"],
                "payload_sha256": hashlib.sha256(request["payload"].encode()).hexdigest(),
            }
            for request in requests
        ],
        "paid_judge_calls": len(requests),
        "generation_calls": 0,
        "total_reserved_usd": sum(
            prices.cost(len((PROMPT + request["payload"]).encode()) + 8192, OUTPUT_TOKENS)
            for request in requests
        ),
        "estimated_usd_at_output_cap": sum(
            prices.cost(
                len(tokenizer.encode(PROMPT + request["payload"], disallowed_special=())),
                OUTPUT_TOKENS,
            )
            for request in requests
        ),
    }


def item_prediction(item, row, prepared, judgment):
    if item["type"] == "abstention":
        return item["prediction"]  # The unchanged deterministic status check, pinned by #16.
    if judgment is None:
        return None
    if item["type"] != "citation":
        field = {
            "required_claim": "required_claims",
            "qualification": "qualifications",
            "forbidden_claim": "forbidden_claims",
        }[item["type"]]
        value = getattr(judgment, field)[item["target"]].value
        return not value if item["type"] == "forbidden_claim" and value is not None else value
    target = item["target"]
    if target[0] == "set":
        return judgment.sections_fully_supported[target[1]].value
    visible = {passage["id"]: passage["text"] for passage in prepared.items}
    values = [
        citation_value(decision, row["answer"]["sections"][target[1]], visible)
        for decision in judgment.citations
        if [decision.section_index, decision.citation_id] == target[1:]
    ]
    return all_decided(values) if values else None


def run_review(args, plan, prices):
    if canonical_hash(plan) != args.approve_plan_sha256:
        raise ValueError("Owner approval must match the printed plan SHA-256")
    guard = CostGuard(args.max_cost_usd)
    if plan["total_reserved_usd"] > guard.maximum:
        raise ValueError("Full review reservation exceeds --max-cost-usd")
    if not args.study_ledger:
        raise ValueError("Judge review requires a shared --study-ledger")
    items, requests, indexed = review_inputs(args.review_archive, args.review_half)
    resuming = args.resume
    if resuming and canonical_hash(
        json.loads((args.output / "plan.json").read_bytes())
    ) != canonical_hash(plan):
        raise ValueError("Resume requires the same plan")
    settings = Settings.from_env(args.env_file)
    if not settings.api_key:
        raise ValueError("Missing API key")
    budget = StudyBudget(args.study_ledger, args.max_cost_usd, prices)
    args.output.mkdir(parents=True, exist_ok=resuming)
    save(args.output / "plan.json", plan)
    client = OpenAI(
        api_key=settings.api_key, base_url="https://api.openai.com/v1", timeout=90, max_retries=0
    )
    judgments = {}
    try:
        for request in requests:
            checkpoint = args.output / (request["id"].replace(":", "__") + ".json")
            if checkpoint.exists():
                saved = json.loads(checkpoint.read_bytes())
                if saved.get("error") or not saved.get("judgment"):
                    raise ValueError("Unresolved review checkpoint; do not repeat a paid call")
                judgments[request["id"]] = Judgment.model_validate(saved["judgment"])
                continue
            identity = canonical_hash(plan) + ":" + request["id"]
            wrapped = BudgetClient(client, budget, prices, identity)
            print(f"Judge review: {request['id']}", flush=True)
            try:
                response = wrapped.responses.parse(
                    model=MODEL,
                    reasoning={"effort": REASONING},
                    instructions=PROMPT,
                    input=request["payload"],
                    text_format=Judgment,
                    max_output_tokens=OUTPUT_TOKENS,
                    store=False,
                )
                save(
                    checkpoint,
                    {
                        "raw_judgment": response.model_dump(mode="json", warnings=False),
                        "judgment": response.output_parsed.model_dump(mode="json")
                        if response.output_parsed
                        else None,
                    },
                )
                if response.status != "completed" or response.output_parsed is None:
                    raise ValueError("Incomplete review judgment")
                judgments[request["id"]] = response.output_parsed
            except Exception:
                if not checkpoint.exists():
                    save(checkpoint, {"error": "judge_request_failed"})
                raise ValueError(
                    "Review stopped; inspect saved checkpoint, no automatic retries"
                ) from None
    finally:
        client.close()
    predictions = {}
    for item in items:
        identity = f"{item['configuration']}:{item['case_id']}"
        row, prepared, case = indexed[identity]
        if identity in judgments:
            score(case, row["answer"], prepared, judgments[identity], judge_version=2)
        predictions[item["id"]] = item_prediction(item, row, prepared, judgments.get(identity))
    save(args.output / "predictions.json", predictions)
    if args.review_half == "calibration":
        key = json.loads((REVIEW / "scoring-key.json").read_bytes())
        grades = load_grades(REVIEW / "calibration-grades.csv", key, "calibration")
        result = {
            "half": "calibration",
            "plan_sha256": canonical_hash(plan),
            "metrics": agreement(items, grades, predictions),
        }
        save(args.output / "agreement.json", result)
        print(json.dumps(result, indent=2))


def review_command(args):
    if args.review_half == "validation":
        from researchlens.answer_judge_freeze import assert_frozen

        assert_frozen()
    prices = Prices.model_validate_json(args.prices.read_bytes())
    plan = review_plan(args.review_archive, args.review_half, prices)
    print(json.dumps(plan, indent=2), flush=True)
    print(f"Approval plan SHA-256: {canonical_hash(plan)}", flush=True)
    if args.command == "answer-plan":
        save(args.output, plan)
    else:
        run_review(args, plan, prices)
