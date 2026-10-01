import hashlib
import json
import sys
from copy import deepcopy

import numpy as np
import pytest
from researchlens.artifacts import canonical_hash, passage_identity, validate_passage_artifact
from researchlens.evaluation import (
    comparison_report,
    default_retrieval_config,
    load_dataset,
    main,
    run_evaluation,
    summarize,
)
from researchlens.evaluation_evidence import (
    CaseEvidence,
    EncodingDiagnostics,
    EvidenceLabels,
    TextRange,
    dataset_digest,
    evidence_coverage,
    ranking_metrics,
    validate_encoding_diagnostics,
    validate_labels,
)
from researchlens.evaluation_metrics import paired_changes, percentile_nearest_rank
from researchlens.evaluation_schema import ExecutionConfig, RetrievalConfig
from researchlens.ingest import CORPUS, ROOT, TECHNICAL_CORPUS, build_index
from researchlens.models import Passage, SearchHit


@pytest.fixture
def sample(tmp_path):
    index = tmp_path / "index.json"
    build_index(CORPUS, index)
    artifact = json.loads(index.read_bytes())
    dataset = load_dataset(ROOT / "evaluation/datasets/development.json")
    passages = validate_passage_artifact(artifact)
    return dataset, artifact, {p.id: SearchHit(**p.model_dump(), score=1.0) for p in passages}


def span(passage, quote=None):
    quote = quote or passage.text
    start = passage.text.index(quote)
    return dict(passage_id=passage.id, start=start, end=start + len(quote), quote=quote)


def groups(sample):
    _, _, hits = sample
    bright = hits["fixture-bright-field:p2:w0"]
    dark = hits["fixture-dark-field:p2:w0"]
    return CaseEvidence.model_validate(
        dict(
            case_id="dev-compare-imaging",
            groups=[
                dict(
                    id="bright",
                    claim_index=0,
                    description="Bright-field evidence",
                    alternatives=[[span(bright)]],
                ),
                dict(
                    id="dark",
                    claim_index=1,
                    description="Dark-field evidence",
                    alternatives=[[span(dark)]],
                ),
            ],
        )
    )


def labels(sample, entry=None):
    dataset, artifact, hits = sample
    return EvidenceLabels(
        dataset_sha256=dataset_digest(dataset),
        corpus_sha256=artifact["source_sha256"],
        shared_passage_sha256=passage_identity(
            artifact, [Passage.model_validate(p.model_dump()) for p in hits.values()]
        ),
        review_status="unreviewed",
        reviewer=None,
        review_date=None,
        notes="Test labels",
        cases=[entry or groups(sample)],
    )


class Fixed:
    def __init__(self, hits):
        self.hits = hits
        self.limits = []

    def search(self, question, limit=4):
        self.limits.append(limit)
        return self.hits[:limit]


def run(sample, ordered, **kwargs):
    return run_evaluation(
        sample[0],
        sample[1],
        Fixed(ordered),
        RetrievalConfig(implementation="mock", version="1", limit=10),
        evidence_labels=labels(sample),
        **kwargs,
    )


def test_mrr_one_and_all_sources_can_still_have_incomplete_evidence(sample):
    dataset, _, hits = sample
    entry = groups(sample)
    selected = [hits["fixture-bright-field:p2:w0"], hits["fixture-dark-field:p1:w0"]]
    metrics = ranking_metrics(dataset.cases[1], selected, entry)
    assert metrics["reciprocal_rank"] == metrics["source_recall"] == 1
    assert metrics["group_coverage"] == 0.5
    assert metrics["complete_evidence"] is False
    selected.append(hits["fixture-dark-field:p2:w0"])
    assert ranking_metrics(dataset.cases[1], selected, entry)["complete_evidence"] is True


def test_alternatives_and_complementary_spans_have_different_requirements(sample):
    entry = groups(sample)
    first, second = (g.alternatives[0][0] for g in entry.groups)
    # Pure contract example: two alternatives versus two complementary spans.
    entry.groups = [entry.groups[0].model_copy(update={"alternatives": [[first], [second]]})]
    visible = {second.passage_id: [TextRange(start=second.start, end=second.end)]}
    assert evidence_coverage(entry, visible)["complete_evidence"] is True
    entry.groups[0].alternatives = [[first, second]]
    assert evidence_coverage(entry, visible)["complete_evidence"] is False
    visible[first.passage_id] = None
    assert evidence_coverage(entry, visible)["complete_evidence"] is None
    visible[first.passage_id] = [TextRange(start=first.start, end=first.end)]
    assert evidence_coverage(entry, visible)["complete_evidence"] is True


def test_alternative_outside_original_reference_counts_for_mrr(sample):
    dataset, artifact, hits = sample
    alternate = hits["fixture-dark-field:p1:w0"]
    # Contract fixture only, not a scientific support judgment about this passage.
    entry = CaseEvidence.model_validate(
        dict(
            case_id="dev-dust",
            groups=[
                dict(
                    id="alternative",
                    claim_index=0,
                    description="Mock alternative",
                    alternatives=[[span(alternate)]],
                ),
            ],
        )
    )
    validate_labels(labels(sample, entry), dataset, artifact, validate_passage_artifact(artifact))
    metrics = ranking_metrics(dataset.cases[0], [alternate], entry)
    assert metrics["reciprocal_rank"] == 1
    assert metrics["passage_recall"] == 0  # Legacy reference-list recall is separate.


@pytest.mark.parametrize(
    "change",
    [
        "dataset",
        "corpus",
        "passages",
        "quote",
        "offset",
        "claim",
        "case",
        "negative",
        "source",
        "duplicate-group",
        "missing-claim",
        "false-review",
        "credentials",
        "duplicate-span",
        "duplicate-option",
    ],
)
def test_invalid_evidence_labels_fail_before_search(sample, change):
    value = labels(sample).model_dump(mode="json")
    entry = value["cases"][0]
    group = entry["groups"][0]
    evidence = group["alternatives"][0][0]
    if change in ("dataset", "corpus"):
        value[f"{change}_sha256"] = "0" * 64
    elif change == "passages":
        value["shared_passage_sha256"] = "0" * 64
    elif change == "quote":
        evidence["quote"] = "Invented support"
    elif change == "offset":
        evidence["start"] += 1
    elif change == "claim":
        group["claim_index"] = 99
    elif change == "case":
        entry["case_id"] = "unknown-case"
    elif change == "negative":
        entry["case_id"] = "dev-missing-size"
    elif change == "source":
        evidence.update(span(sample[2]["fixture-learning:p1:w0"]))
    elif change == "duplicate-group":
        entry["groups"].append(deepcopy(group))
    elif change == "missing-claim":
        entry["groups"].pop()
    elif change == "false-review":
        value["review_status"] = "approved"
    elif change == "credentials":
        value["api_key"] = "fake-test-secret"
    elif change == "duplicate-span":
        group["alternatives"][0].append(deepcopy(evidence))
    else:
        group["alternatives"].append(deepcopy(group["alternatives"][0]))
    retriever = Fixed([])
    with pytest.raises(ValueError):
        run_evaluation(
            sample[0],
            sample[1],
            retriever,
            RetrievalConfig(implementation="mock", version="1"),
            evidence_labels=EvidenceLabels.model_validate(value),
        )
    assert retriever.limits == []


def test_cutoffs_use_one_ranking_and_k4_is_primary(sample):
    hits = sample[2]
    ordered = [
        hits["fixture-bright-field:p2:w0"],
        hits["fixture-dark-field:p1:w0"],
        hits["fixture-bright-field:p1:w0"],
        hits["fixture-dark-field:p2:w0"],
    ]
    retriever = Fixed(ordered)
    result = run_evaluation(
        sample[0],
        sample[1],
        retriever,
        RetrievalConfig(implementation="mock", version="1", limit=10),
        evidence_labels=labels(sample),
        cutoffs=[1, 4, 10],
    )
    assert retriever.limits == [10] * 3
    comparison = result["results"][1]["metrics_at_k"]
    assert comparison["1"]["group_coverage"] == 0.5
    assert comparison["4"]["complete_evidence"] is True
    assert comparison["10"] == comparison["4"]
    assert summarize(result)["primary_k4_complete_evidence_rate"] == 1
    assert all(
        v["reciprocal_rank"] is None and v["complete_evidence"] is None
        for v in result["results"][2]["metrics_at_k"].values()
    )
    assert "k=4 is the primary" in comparison_report([result], [None])


@pytest.mark.parametrize("cutoffs", [[10], [0], [True], [1, True], [1, "4"], []])
def test_cutoffs_cannot_invent_unretrieved_ranks(sample, cutoffs):
    retriever = Fixed([])
    with pytest.raises(ValueError, match="Cutoffs"):
        run_evaluation(
            sample[0],
            sample[1],
            retriever,
            RetrievalConfig(implementation="mock", version="1", limit=4),
            cutoffs=cutoffs,
        )
    assert not retriever.limits


def test_paired_changes_retain_mixed_regressions_errors_and_unknowns(sample):
    hits = sample[2]
    bright, dark = hits["fixture-bright-field:p2:w0"], hits["fixture-dark-field:p2:w0"]
    filler = hits["fixture-dark-field:p1:w0"]
    baseline, candidate = run(sample, [filler, bright, dark]), run(sample, [bright, filler])
    changes = {c["case_id"]: c for c in paired_changes(baseline, candidate)}
    change = changes["dev-compare-imaging"]
    assert change["outcome"] == "mixed"
    assert change["deltas"]["group_coverage"] == -0.5
    assert change["deltas"]["reciprocal_rank"] == 0.5
    assert changes["dev-dust"]["outcome"] == "worsened"
    assert changes["dev-missing-size"]["outcome"] == "not-scored"
    assert paired_changes(baseline, baseline)[1]["outcome"] == "unchanged"
    assert paired_changes(candidate, baseline)[0]["outcome"] == "improved"
    candidate["results"][0]["error"] = {"stage": "retrieval", "code": "retrieval_failed"}
    assert paired_changes(baseline, candidate)[0]["outcome"] == "failed"
    assert paired_changes(candidate, baseline)[0]["outcome"] == "recovered"
    baseline["results"][0]["error"] = candidate["results"][0]["error"]
    assert paired_changes(baseline, candidate)[0]["outcome"] == "both-failed"
    candidate["results"][1]["metrics_at_k"].pop("4")
    assert paired_changes(baseline, candidate)[1]["outcome"] == "unavailable"


def test_changed_evidence_annotations_block_controlled_comparison(sample):
    baseline = run(sample, [])
    changed_labels = labels(sample)
    changed_labels.notes = "Different judgment provenance"
    candidate = run_evaluation(
        sample[0],
        sample[1],
        Fixed([]),
        RetrievalConfig(implementation="mock", version="1", limit=10),
        evidence_labels=changed_labels,
    )
    with pytest.raises(ValueError, match="evidence/scoring"):
        comparison_report([baseline, candidate], [None, None])


def embedding_measurements(sample):
    artifact = deepcopy(sample[1])
    matrix = np.ones((len(artifact["passages"]), 1), dtype=np.float32)
    artifact.update(
        schema_version=2,
        embeddings=dict(
            encoding=dict(
                model="test/mock",
                revision="a" * 40,
                dimensions=1,
                max_tokens=256,
                pooling="mean",
                normalization="l2",
                query_prefix="",
                document_prefix="",
                text="passage-text-only",
                encoding_version=1,
            ),
            passage_ids=[p["id"] for p in artifact["passages"]],
            vectors=matrix.tolist(),
            vectors_sha256=hashlib.sha256(matrix.astype("<f4").tobytes()).hexdigest(),
        ),
    )
    measurements = EncodingDiagnostics.model_validate(
        dict(
            artifact_sha256=canonical_hash(artifact),
            encoding_sha256=canonical_hash(artifact["embeddings"]["encoding"]),
            token_count_scope="encoder-input-including-instructions-and-special-tokens",
            passages=[
                dict(
                    passage_id=p.id,
                    text_sha256=hashlib.sha256(p.text.encode()).hexdigest(),
                    input_tokens=300,
                    encoded_tokens=256,
                    truncated=True,
                    retained_ranges=[dict(start=0, end=10)],
                )
                for p in sample[2].values()
            ],
        )
    )
    return artifact, measurements


def test_actual_encoder_ranges_expose_lost_evidence_and_missing_measurements(sample):
    artifact, measurements = embedding_measurements(sample)
    retriever = Fixed(
        [sample[2]["fixture-bright-field:p2:w0"], sample[2]["fixture-dark-field:p2:w0"]]
    )
    retriever.get_encoding_diagnostics = lambda: measurements.model_dump()
    config = default_retrieval_config("embeddings", artifact, "mock")
    result = run_evaluation(sample[0], artifact, retriever, config, evidence_labels=labels(sample))
    row = result["results"][1]
    assert row["metrics_at_k"]["4"]["complete_evidence"] is True
    assert row["embedding_coverage_at_k"]["4"]["complete_evidence"] is False
    assert row["embedding_truncation_loss_at_k"]["4"]["lost_group_ids"] == ["bright", "dark"]
    assert summarize(result)["encoder_truncation_rate_measured"] == 1
    del retriever.get_encoding_diagnostics
    unknown = run_evaluation(sample[0], artifact, retriever, config, evidence_labels=labels(sample))
    row = unknown["results"][1]
    assert row["embedding_coverage_at_k"]["4"]["complete_evidence"] is None
    assert row["embedding_truncation_loss_at_k"]["4"]["unknown_group_ids"] == ["bright", "dark"]
    assert summarize(unknown)["encoder_truncation_rate_measured"] is None


@pytest.mark.parametrize(
    "change",
    [
        "artifact",
        "encoding",
        "text",
        "tokens",
        "cap",
        "range",
        "overlap",
        "flag",
        "duplicate",
        "credentials",
        "string-flag",
    ],
)
def test_encoder_measurements_are_pinned_and_allowlisted(sample, change):
    artifact, measurements = embedding_measurements(sample)
    value = measurements.model_dump()
    passage = value["passages"][0]
    if change in ("artifact", "encoding"):
        value[f"{change}_sha256"] = "0" * 64
    elif change == "text":
        passage["text_sha256"] = "0" * 64
    elif change == "tokens":
        passage["encoded_tokens"] = 301
    elif change == "cap":
        passage["encoded_tokens"] = 257
    elif change == "range":
        passage["retained_ranges"][0]["end"] = 99999
    elif change == "overlap":
        passage["retained_ranges"].append(dict(start=5, end=11))
    elif change == "flag":
        passage["truncated"] = False
    elif change == "duplicate":
        value["passages"].append(deepcopy(passage))
    elif change == "credentials":
        value["api_key"] = "fake-test-secret"
    else:
        passage["truncated"] = "false"
    with pytest.raises(ValueError):
        validate_encoding_diagnostics(
            EncodingDiagnostics.model_validate(value), artifact, list(sample[2].values())
        )


def test_answer_context_loses_late_evidence_and_separates_selection(sample):
    dataset, artifact, hits = sample
    bright = hits["fixture-bright-field:p2:w0"]
    late_text = "x" * 3100 + "Late supporting sentence."
    bright.text = late_text
    for passage in artifact["passages"]:
        if passage["id"] == bright.id:
            passage["text"] = late_text
    evidence = groups(sample)
    evidence.groups[0].alternatives = [
        [type(evidence.groups[0].alternatives[0][0])(**span(bright, "Late supporting sentence."))]
    ]
    result = run_evaluation(
        dataset,
        artifact,
        Fixed([bright, hits["fixture-dark-field:p2:w0"]]),
        RetrievalConfig(implementation="mock", version="1"),
        evidence_labels=labels(sample, evidence),
    )
    row = result["results"][1]
    assert row["metrics_at_k"]["4"]["complete_evidence"] is True
    assert row["answer_context_coverage"]["complete_evidence"] is False
    assert row["answer_context_truncation_loss"]["lost_group_ids"] == ["bright"]
    assert row["answer_context_selection_loss"]["lost_group_ids"] == []
    assert row["answer"] is None  # Free preview diagnostics are not generated answers.
    selected = (
        [bright]
        + [p for p in hits.values() if p.id not in (bright.id, "fixture-dark-field:p2:w0")]
        + [hits["fixture-dark-field:p2:w0"]]
    )
    limited = run_evaluation(
        dataset,
        artifact,
        Fixed(selected),
        RetrievalConfig(implementation="mock", version="1", limit=10),
        evidence_labels=labels(sample, evidence),
    )
    assert limited["results"][1]["answer_context_selection_loss"]["lost_group_ids"] == ["dark"]


def test_p95_uses_successful_attempt_samples_not_warmups_or_failed_attempts(sample):
    result = run(sample, [], execution=ExecutionConfig(repeats=2, warmups=1))
    result["results"][0]["retrieval_attempts"] = [
        dict(latency_ms=v, error=None) for v in range(1, 21)
    ] + [dict(latency_ms=9999, error="retrieval_failed")]
    for row in result["results"][1:]:
        row["retrieval_attempts"] = []
    summary = summarize(result)
    assert summary["query_p95_ms"] == 19
    assert summary["query_median_ms"] == 10.5
    assert summary["query_timing_samples"] == 20
    assert summary["query_failed_attempts"] == 1
    assert percentile_nearest_rank([], 0.95) is None


def test_cli_cutoffs_and_paired_json_are_reproducible(sample, tmp_path, monkeypatch):
    index = tmp_path / "index.json"
    evidence = tmp_path / "evidence.json"
    evidence.write_text(labels(sample).model_dump_json())
    outputs = [tmp_path / "first", tmp_path / "second"]
    args = [
        "evaluation",
        "run",
        "--dataset",
        str(ROOT / "evaluation/datasets/development.json"),
        "--other-split",
        str(ROOT / "evaluation/datasets/held-out.json"),
        "--source",
        str(CORPUS),
        "--index",
        str(index),
        "--evidence-labels",
        str(evidence),
        "--cutoffs",
        "1",
        "4",
        "10",
    ]
    for output in outputs:
        monkeypatch.setattr(sys, "argv", [*args, "--output", str(output)])
        main()
    recorded = json.loads((outputs[0] / "run.json").read_bytes())
    assert recorded["retrieval"]["limit"] == 10
    assert recorded["cutoffs"] == [1, 4, 10]
    report, paired = tmp_path / "comparison.md", tmp_path / "paired.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "evaluation",
            "report",
            *map(str, outputs),
            "--output",
            str(report),
            "--paired-output",
            str(paired),
        ],
    )
    main()
    comparison = json.loads(paired.read_bytes())
    assert comparison["primary_k"] == 4
    assert comparison["comparisons"][0]["changes"]["4"][1]["outcome"] == "unchanged"
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    monkeypatch.setattr(sys, "argv", [*args, "--limit", "4", "--output", str(tmp_path / "bad")])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert not (tmp_path / "bad").exists()


def test_development_labels_are_drafts_and_approved_dataset_hashes_are_unchanged(tmp_path):
    expected = {
        "technical-development.json": (
            "32e76c99d650b994c03e8e3f32da921633b0a636f2f1afe2c833db7e513e85a2"
        ),
        "held-out.json": "19304c0bf72e39dd5563868ac90c0ee153e85d5ffbdf33eff81e3bbf1cd67572",
    }
    for name, checksum in expected.items():
        assert (
            hashlib.sha256((ROOT / "evaluation/datasets" / name).read_bytes()).hexdigest()
            == checksum
        )
    index = tmp_path / "technical.json"
    build_index(TECHNICAL_CORPUS, index)
    artifact = json.loads(index.read_bytes())
    dataset = load_dataset(ROOT / "evaluation/datasets/technical-development.json")
    evidence = EvidenceLabels.model_validate_json(
        (ROOT / "evaluation/labels/technical-development.json").read_bytes()
    )
    approved = validate_labels(evidence, dataset, artifact, validate_passage_artifact(artifact))
    assert set(approved) == {c.id for c in dataset.cases if not c.expected_abstention}
    assert len(approved) == 36
    assert evidence.review_status == "unreviewed"
    assert evidence.reviewer is evidence.review_date is None
    assert sum(c.query_style == "missing-evidence" for c in dataset.cases) == 7
