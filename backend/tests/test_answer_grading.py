"""Check the committed review's blinding, split isolation and evidence identity."""

import hashlib
import json
import re
from collections import Counter, defaultdict

import pytest
from researchlens.answer_grading import ROOT, TYPES, write_sample

REVIEW = ROOT / "evaluation/reviews/2026-10-14-answer-judge"


def test_committed_packet_is_blind_and_matches_frozen_key():
    packet_bytes = (REVIEW / "owner-grading.md").read_bytes()
    packet = packet_bytes.decode("utf-8")
    key = json.loads((REVIEW / "scoring-key.json").read_text())
    assert hashlib.sha256(packet_bytes).hexdigest() == key["packet_sha256"]
    assert re.findall(r"^## (G\d{3})$", packet, re.MULTILINE) == [
        item["id"] for item in key["items"]
    ]
    assert packet.count("|  |  |") == 60
    for config in ("tfidf4", "qwen4", "qwen12k", "qwen16k", "TF-IDF", "Qwen"):
        assert config not in packet
    assert "tech-" not in packet
    assert not re.search(
        r"^(Judge verdict|Baseline prediction|Configuration|Half):", packet, re.MULTILINE
    )
    assert "judge reason" not in packet.lower()
    assert "### `pmc" in packet
    assert "## Source attribution" in packet


def test_split_has_no_question_leakage_and_covers_available_strata():
    key = json.loads((REVIEW / "scoring-key.json").read_text())
    halves_by_question = defaultdict(set)
    for item in key["items"]:
        halves_by_question[item["case_id"]].add(item["half"])
    assert all(len(halves) == 1 for halves in halves_by_question.values())
    for half in ("calibration", "validation"):
        half_items = [item for item in key["items"] if item["half"] == half]
        assert len(half_items) == 30
        assert len({item["cohort"] for item in half_items}) == 5
        for kind in TYPES:
            items = [item for item in half_items if item["type"] == kind]
            assert len(items) == 6
            assert len({item["configuration"] for item in items}) == 4
            assert len({item["case_id"] for item in items}) == 6
            if kind != "forbidden_claim":
                assert {False, True} <= {item["prediction"] for item in items}
    assert set(Counter(item["configuration"] for item in key["items"]).values()) == {15}
    assert sum(item["prediction"] is None for item in key["items"]) == 2
    assert all(item["half"] == "calibration" for item in key["items"] if item["prediction"] is None)
    previously_audited = {
        "tech-autoencoder-exact",
        "tech-imagenet-initialization",
        "tech-stable-camera",
        "tech-moving-signal-addition",
        "tech-compare-localization-outputs",
        "tech-compare-training-splits",
        "tech-missing-factory-warranty",
        "tech-missing-autoencoder-ct",
        "tech-unrelated-database-isolation",
        "tech-unrelated-exchange-rate",
        "tech-compare-training-computers",
    }
    assert all(
        item["half"] == "calibration"
        for item in key["items"]
        if item["case_id"] in previously_audited
    )


def test_preparer_refuses_to_overwrite_owner_grades_before_reading_archive(tmp_path):
    (tmp_path / "owner-grading.md").write_text("Owner's completed review", encoding="utf-8")
    with pytest.raises(ValueError, match="never overwrite"):
        write_sample(tmp_path / "missing-archive.gz", tmp_path)
    assert (tmp_path / "owner-grading.md").read_text() == "Owner's completed review"
