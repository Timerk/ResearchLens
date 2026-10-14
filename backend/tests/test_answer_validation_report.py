import hashlib
import json

import pytest
from researchlens import answer_validation_report as module


def test_sealed_hash_is_verified_before_grade_parsing(tmp_path, monkeypatch):
    grades = tmp_path / "validation-grades.csv"
    grades.write_text("item_id,verdict,notes\nG001,PASS,Supported\n", encoding="utf-8")
    digest = hashlib.sha256(grades.read_bytes()).hexdigest()
    (tmp_path / "owner-review.md").write_text(f"Sealed validation CSV SHA-256: {digest}\n")
    (tmp_path / "scoring-key.json").write_text(
        json.dumps({"items": [{"id": "G001", "half": "validation"}]})
    )
    monkeypatch.setattr(module, "REVIEW", tmp_path)
    monkeypatch.setattr(module, "assert_frozen", lambda: {"contract": "test"})
    assert module.verified_grades(grades)[2]["G001"]["verdict"] == "PASS"
    grades.write_text("corrupt\n")
    with pytest.raises(ValueError, match="do not match owner-review"):
        module.verified_grades(grades)
