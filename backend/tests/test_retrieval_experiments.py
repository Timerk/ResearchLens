import json
from datetime import date
from unittest.mock import Mock

import pytest
from researchlens.artifacts import passage_identity
from researchlens.embedding_models import encoding_metadata
from researchlens.evaluation import run_evaluation
from researchlens.evaluation_evidence import EvidenceLabels, dataset_digest
from researchlens.evaluation_schema import Case, Dataset, RetrievalConfig
from researchlens.ingest import ROOT, build_index
from researchlens.models import Document, Passage, SearchHit
from researchlens.retrieval_analysis import analyze_run, minimal_supports
from researchlens.retrieval_experiments import compare, experiment_plan

DATASET = ROOT / "evaluation/datasets/technical-development.json"
OTHER = ROOT / "evaluation/datasets/held-out.json"
LABELS = ROOT / "evaluation/labels/technical-development.json"


def test_predefined_plan_uses_existing_runner_and_records_every_setting(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "researchlens.retrieval_experiments.load_artifact",
        lambda path, **kwargs: (
            {}
            if path.stem == "tfidf"
            else {"embeddings": {"encoding": encoding_metadata(path.stem)}},
            [],
        ),
    )
    monkeypatch.setattr("researchlens.retrieval_experiments.validate_artifact", Mock())
    monkeypatch.setattr("researchlens.retrieval_experiments.validate_labels", Mock())
    process = Mock(return_value=Mock(returncode=0, stdout=b"secret", stderr=b"private"))
    monkeypatch.setattr("researchlens.retrieval_experiments.subprocess.run", process)
    manifest = compare(
        tmp_path / "runs",
        tmp_path / "indexes",
        dataset=DATASET,
        other_split=OTHER,
        evidence_labels=LABELS,
    )
    plan = experiment_plan()
    assert len(plan) == len({entry["name"] for entry in plan}) == 21
    assert process.call_count == 43
    commands = [call.args[0] for call in process.call_args_list]
    assert all(
        command[2] in ("researchlens.evaluation", "researchlens.retrieval_analysis")
        for command in commands
    )
    assert all(
        "--retrieval-config" in command and "--evidence-labels" in command
        for command in commands[:-1:2]
    )
    assert "report" in commands[-1] and "--paired-output" in commands[-1]
    assert all("--mode" not in command for command in commands)
    assert all(stage["status"] == "completed" for stage in manifest["stages"])
    assert manifest["api_calls"] == 0
    assert manifest["context_budgets"] == [4, 6, 8]
    saved = (tmp_path / "runs/manifest.json").read_text()
    assert "secret" not in saved and "private" not in saved
    config = json.loads(
        (tmp_path / "runs/configs/bge-m3-hybrid40-lex25-rerank40.json").read_bytes()
    )
    assert config["lexical_weight"] == 0.25 and config["embedding_weight"] == 0.75
    assert config["reranker"]["candidates"] == 40


def test_unapproved_or_stale_inputs_fail_before_process_or_output(tmp_path, monkeypatch):
    process = Mock()
    monkeypatch.setattr("researchlens.retrieval_experiments.subprocess.run", process)
    with pytest.raises(ValueError, match="development"):
        compare(
            tmp_path / "held-out",
            tmp_path,
            dataset=OTHER,
            other_split=DATASET,
            evidence_labels=LABELS,
        )
    labels = json.loads(LABELS.read_bytes())
    labels.update(review_status="unreviewed", reviewer=None, review_date=None)
    path = tmp_path / "unreviewed.json"
    path.write_text(json.dumps(labels), encoding="utf-8")
    with pytest.raises(ValueError, match="approved evidence"):
        compare(
            tmp_path / "runs", tmp_path, dataset=DATASET, other_split=OTHER, evidence_labels=path
        )
    process.assert_not_called()
    assert not (tmp_path / "runs").exists()


def labeled_run(tmp_path, alternatives):
    document = Document(
        id="doc",
        title="Document",
        source_url=None,
        license="CC0",
        kind="synthetic",
        text="\n\n".join(f"Evidence paragraph {i}." for i in range(7)),
    )
    source = tmp_path / "source.json"
    source.write_text(json.dumps([document.model_dump()]), encoding="utf-8")
    index = tmp_path / "index.json"
    build_index(source, index)
    artifact = json.loads(index.read_bytes())
    passages = [Passage.model_validate(row) for row in artifact["passages"]]
    case = Case(
        id="case",
        question="Which evidence supports the claim?",
        category="factual",
        query_style="paraphrase",
        expected_source_ids=["doc"],
        references=[dict(source_id="doc", passage_id=passages[0].id, paragraph=1)],
        required_claims=["Claim"],
        required_qualifications=[],
        forbidden_claims=[],
        expected_abstention=False,
        review_status="approved",
        reviewer="Test",
        review_date=date(2026, 10, 1),
    )
    dataset = Dataset(
        schema_version=1,
        id="test",
        version="1",
        split="development",
        material="synthetic",
        status="draft",
        corpus_sha256=artifact["source_sha256"],
        notes="Test",
        cases=[case],
    )
    labels = EvidenceLabels(
        dataset_sha256=dataset_digest(dataset),
        corpus_sha256=artifact["source_sha256"],
        shared_passage_sha256=passage_identity(artifact, passages),
        review_status="approved",
        reviewer="Test",
        review_date=date(2026, 10, 1),
        notes="Test",
        cases=[
            dict(
                case_id="case",
                groups=[
                    dict(
                        id="claim",
                        claim_index=0,
                        description="Claim support",
                        alternatives=[
                            [
                                dict(
                                    passage_id=passages[i].id,
                                    start=0,
                                    end=len(passages[i].text),
                                    quote=passages[i].text,
                                )
                                for i in option
                            ]
                            for option in alternatives
                        ],
                    )
                ],
            )
        ],
    )
    hits = [SearchHit(**p.model_dump(), score=1) for p in passages]
    return dataset, artifact, labels, hits


def test_failure_oracle_respects_or_and_and_never_selects_query_passages(tmp_path):
    dataset, artifact, labels, hits = labeled_run(tmp_path, [[5], [0, 4]])
    entry = labels.cases[0]
    assert set(minimal_supports(entry)) == {
        frozenset([hits[5].id]),
        frozenset([hits[0].id, hits[4].id]),
    }
    retriever = Mock()
    retriever.search.return_value = hits
    run = run_evaluation(
        dataset,
        artifact,
        retriever,
        RetrievalConfig(implementation="mock", version="1", limit=7),
        evidence_labels=labels,
    )
    result = analyze_run(run)
    assert result["failure_counts"] == {"ranking-or-selection": 1}
    assert result["cases"][0]["minimum_labeled_passages"] == 1
    assert [result["context_summary"][str(k)]["complete_evidence_cases"] for k in (4, 6, 8)] == [
        0,
        1,
        1,
    ]
    retriever.search.assert_called_once()
    retriever.search.return_value = hits[:4]
    run = run_evaluation(
        dataset,
        artifact,
        retriever,
        RetrievalConfig(implementation="mock", version="1"),
        evidence_labels=labels,
    )
    assert analyze_run(run)["failure_counts"] == {"candidate-pool-missing-evidence": 1}


def test_failure_oracle_detects_four_passage_budget_impossibility(tmp_path):
    dataset, artifact, labels, hits = labeled_run(tmp_path, [[0, 1, 2, 3, 4]])
    retriever = Mock()
    retriever.search.return_value = hits
    run = run_evaluation(
        dataset,
        artifact,
        retriever,
        RetrievalConfig(implementation="mock", version="1", limit=7),
        evidence_labels=labels,
    )
    assert analyze_run(run)["failure_counts"] == {"labels-require-more-than-four-passages": 1}
    run["dataset"]["split"] = "held-out"
    with pytest.raises(ValueError, match="development"):
        analyze_run(run)
