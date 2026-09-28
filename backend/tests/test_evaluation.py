import json
import sys
from copy import deepcopy
from datetime import date
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from researchlens.answers import INSTRUCTIONS, LocalPreview, OpenAIProvider
from researchlens.evaluation import (
    comparison_report,
    digest,
    load_dataset,
    main,
    review_template,
    run_evaluation,
    summarize,
    validate_artifact,
    validate_splits,
)
from researchlens.evaluation_schema import Dataset, GenerationConfig, RetrievalConfig, Review
from researchlens.ingest import CORPUS, ROOT, build_index
from researchlens.models import Answer, AnswerSection
from researchlens.retrieval import Retriever


@pytest.fixture
def evaluation(tmp_path):
    path = tmp_path / "index.json"
    build_index(CORPUS, path)
    artifact = json.loads(path.read_bytes())
    dataset = load_dataset(ROOT / "evaluation/datasets/development.json")
    retriever = Retriever.from_path(path)
    config = RetrievalConfig(implementation="tfidf", version="test", limit=4)
    return dataset, artifact, retriever, config


def test_offline_run_ignores_environment_and_records_reproducibility(evaluation, monkeypatch):
    monkeypatch.setenv("ANSWER_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-do-not-record")
    monkeypatch.setattr(OpenAIProvider, "__init__", lambda *a, **k: pytest.fail("Paid client"))
    result = run_evaluation(*evaluation)
    assert result["corpus"]["source_sha256"] == evaluation[0].corpus_sha256
    assert result["code"]["commit"]
    assert result["runtime"]["packages"]["scikit-learn"]
    assert result["results"][0]["retrieved_passage_ids"]
    assert "test-secret" not in json.dumps(result)
    summary = summarize(result)
    assert summary["cases"] == 3
    assert summary["mean_source_recall_at_k"] == 1
    assert summary["comparison_full_coverage"] == 1
    assert summary["generated_answers"] == summary["human_reviews_complete"] == 0
    assert summary["estimated_cost_usd_known"] == summary["unknown_usage_cases"] == 0
    assert result["results"][2]["source_recall_at_k"] is None


def test_preview_no_match_does_not_count_as_generated_abstention(evaluation):
    class Empty:
        def search(self, question, limit=4):
            return []

    result = run_evaluation(
        evaluation[0],
        evaluation[1],
        Empty(),
        evaluation[3],
        provider=LocalPreview(),
        generation=GenerationConfig(provider="local-preview"),
    )
    summary = summarize(result)
    assert summary["no_match_cases"] == 3
    assert summary["automatic_full_abstentions"] == 0
    assert summary["mean_source_recall_at_k"] == 0


def test_generation_errors_keep_retrieval_and_do_not_leak_secrets(evaluation):
    class Broken:
        def answer(self, question, passages):
            raise RuntimeError("Authorization: Bearer test-secret")

    result = run_evaluation(
        *evaluation, provider=Broken(), generation=GenerationConfig(provider="mock")
    )
    assert summarize(result)["errors"] == 3
    assert all(r["retrieved_passage_ids"] for r in result["results"])
    assert all(r["error"]["stage"] == "generation" for r in result["results"])
    assert "test-secret" not in json.dumps(result)


def test_retrieval_failures_are_recorded_per_case(evaluation):
    class Broken:
        def search(self, question, limit=4):
            raise RuntimeError("private")

    result = run_evaluation(evaluation[0], evaluation[1], Broken(), evaluation[3])
    assert summarize(result)["errors"] == 3
    assert all(r["error"]["stage"] == "retrieval" for r in result["results"])
    assert all(r["latency_ms"] >= 0 for r in result["results"])


def test_mock_abstentions_are_separate_from_human_judgments(evaluation):
    class Abstain:
        def answer(self, question, passages):
            return Answer(
                status="insufficient_evidence",
                mode="openai",
                message="mock",
                passages=passages,
                latency_ms=0,
            )

    result = run_evaluation(
        *evaluation, provider=Abstain(), generation=GenerationConfig(provider="mock")
    )
    summary = summarize(result)
    assert summary["automatic_abstentions_unanswerable"] == 1
    assert summary["automatic_false_abstentions"] == 2
    assert summary["generated_unanswerable_cases"] == 1
    assert summary["generated_answerable_cases"] == 2
    assert summary["human_reviews_complete"] == 0


def test_factual_support_requires_human_judgment_even_with_valid_citations(evaluation):
    class Unsupported:
        def answer(self, question, passages):
            return Answer(
                status="answered",
                mode="openai",
                message="mock",
                passages=passages,
                latency_ms=0,
                sections=[
                    AnswerSection(
                        text="Invented 99 percent accuracy", citation_ids=[passages[0].id]
                    )
                ],
            )

    result = run_evaluation(
        *evaluation, provider=Unsupported(), generation=GenerationConfig(provider="mock")
    )
    review = review_template(result)
    assert summarize(result, review)["human_supported"] == 0
    draft = review.model_dump(mode="json")
    first = draft["cases"][0]
    first.update(
        status="complete",
        reviewer="Test reviewer",
        review_date=str(date.today()),
        correctness="incorrect",
        citation_support="unsupported",
        abstention="none",
        required_claims_met=False,
        qualifications_preserved=False,
        forbidden_claims_present=True,
    )
    first["claims"][0].update(correctness="incorrect", citation_support="unsupported")
    checked = Review.model_validate(draft)
    assert summarize(result, checked)["human_reviews_complete"] == 1
    assert summarize(result, checked)["human_supported"] == 0
    assert "support=unsupported" in comparison_report([result], [checked])
    draft["cases"][0]["claims"] = []
    with pytest.raises(ValueError, match="sections"):
        summarize(result, Review.model_validate(draft))


@pytest.mark.parametrize("change", ["hash", "reference", "source"])
def test_stale_corpus_and_references_rejected(evaluation, change):
    dataset, artifact, *_ = evaluation
    dataset = dataset.model_copy(deep=True)
    if change == "hash":
        dataset.corpus_sha256 = "0" * 64
    elif change == "reference":
        dataset.cases[0].references[0].passage_id = "unknown"
    else:
        dataset.cases[0].references[0].source_id = "wrong"
    with pytest.raises(ValueError):
        validate_artifact(dataset, artifact)


def test_pending_held_out_and_split_overlap_rejected(evaluation):
    development = evaluation[0]
    held_out = load_dataset(ROOT / "evaluation/datasets/held-out.json")
    validate_splits(development, held_out)
    with pytest.raises(ValueError, match="pending"):
        validate_artifact(held_out, evaluation[1])
    overlapping = held_out.model_copy(update={"cases": development.cases})
    with pytest.raises(ValueError, match="overlap"):
        validate_splits(development, overlapping)
    with pytest.raises(ValueError, match="frozen"):
        validate_artifact(overlapping.model_copy(update={"status": "draft"}), evaluation[1])


def test_schema_rejects_false_review_claims_and_invalid_comparisons(evaluation):
    data = evaluation[0].model_dump(mode="json")
    data["status"] = "frozen"
    with pytest.raises(ValidationError):
        Dataset.model_validate(data)
    data["status"] = "draft"
    data["cases"][0]["review_status"] = "approved"
    with pytest.raises(ValidationError):
        Dataset.model_validate(data)
    data["cases"][0]["review_status"] = "unreviewed"
    data["cases"][0]["category"] = "comparison"
    with pytest.raises(ValidationError):
        Dataset.model_validate(data)


def test_review_is_bound_to_run_and_comparison_requires_same_dataset(evaluation):
    run = run_evaluation(*evaluation)
    review = review_template(run)
    changed = deepcopy(run)
    changed["results"][0]["latency_ms"] += 1
    with pytest.raises(ValueError, match="match"):
        summarize(changed, review)
    changed["dataset_sha256"] = "different"
    with pytest.raises(ValueError, match="same dataset"):
        comparison_report([run, changed], [None, None])


def test_live_configuration_requires_luna_medium_and_bounded_output():
    with pytest.raises(ValidationError):
        GenerationConfig(provider="openai", model="other")
    with pytest.raises(ValidationError):
        GenerationConfig(provider="openai", model="gpt-6-luna", max_output_tokens=2001)


def test_retriever_adapter_rejects_modified_passages(evaluation):
    class Modified:
        def search(self, question, limit=4):
            hits = evaluation[2].search(question, limit)
            return [hits[0].model_copy(update={"text": "different version"})]

    result = run_evaluation(evaluation[0], evaluation[1], Modified(), evaluation[3])
    assert summarize(result)["errors"] == 3


def test_live_unreviewed_and_unpriced_runs_fail_before_calling_provider(evaluation):
    provider = object.__new__(OpenAIProvider)
    provider.model = "gpt-6-luna"
    provider.client = SimpleNamespace(max_retries=0)
    provider.answer = lambda *a: pytest.fail("Must not call a live provider")
    generation = GenerationConfig(
        provider="openai",
        model="gpt-6-luna",
        reasoning_effort="medium",
        max_output_tokens=2000,
        prompt_sha256=digest(INSTRUCTIONS.encode()),
    )
    with pytest.raises(ValueError, match="Review all"):
        run_evaluation(
            *evaluation,
            provider=provider,
            generation=generation,
            estimated_run_cost_usd=0.01,
            pricing_date="2026-09-28",
        )
    # Fake approval exists only in this isolated test; no dataset files are changed.
    reviewed = evaluation[0].model_copy(deep=True)
    for case in reviewed.cases:
        case.review_status = "approved"
        case.reviewer = "Test only"
        case.review_date = date.today()
    with pytest.raises(ValueError, match="dated cost estimate"):
        run_evaluation(reviewed, *evaluation[1:], provider=provider, generation=generation)


def test_cli_writes_offline_artifacts_and_refuses_overwrite(evaluation, tmp_path, monkeypatch):
    output = tmp_path / "run"
    index = tmp_path / "index.json"
    argv = [
        "evaluation",
        "run",
        "--dataset",
        str(ROOT / "evaluation/datasets/development.json"),
        "--other-split",
        str(ROOT / "evaluation/datasets/held-out.json"),
        "--index",
        str(index),
        "--output",
        str(output),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setenv("ANSWER_PROVIDER", "openai")
    main()
    original = (output / "run.json").read_bytes()
    assert (output / "review.json").exists()
    assert "Valid citation IDs" in (output / "report.md").read_text()
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert (output / "run.json").read_bytes() == original
    report = tmp_path / "comparison.md"
    monkeypatch.setattr(sys, "argv", ["evaluation", "report", str(output), "--output", str(report)])
    main()
    assert "human_reviews_complete" in report.read_text()
