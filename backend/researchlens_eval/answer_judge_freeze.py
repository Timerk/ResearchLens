"""Record and verify the judge contract before opening owner validation grades."""

import argparse
import hashlib
import inspect
import json
from pathlib import Path

from researchlens.artifacts import atomic_write_text, canonical_hash

from researchlens_eval import answer_judge_v2 as judge
from researchlens_eval.answer_judge_review import REVIEW
from researchlens_eval.answer_scoring import Judgment, all_decided, score

FREEZE = REVIEW / "frozen-judge.json"


def current_contract():
    implementation = Path(judge.__file__).read_bytes().replace(b"\r\n", b"\n")
    scoring = inspect.getsource(score) + inspect.getsource(all_decided)
    return {
        "version": judge.VERSION,
        "model": judge.MODEL,
        "reasoning": judge.REASONING,
        "max_output_tokens": judge.OUTPUT_TOKENS,
        "prompt": judge.PROMPT,
        "rubric": judge.RUBRIC,
        "checks": judge.CHECKS,
        "schema": Judgment.model_json_schema(),
        "prompt_sha256": hashlib.sha256(judge.PROMPT.encode()).hexdigest(),
        "schema_sha256": canonical_hash(Judgment.model_json_schema()),
        "judge_implementation_sha256": hashlib.sha256(implementation).hexdigest(),
        "scoring_implementation_sha256": hashlib.sha256(scoring.encode()).hexdigest(),
        "uncertainty_policy": (
            "All-item accuracy gives unknown/UNCERTAIN no success credit; kappa uses only "
            "decidable binary pairs. Undefined kappa cannot meet the acceptance bar."
        ),
    }


def assert_frozen():
    frozen = json.loads(FREEZE.read_bytes())
    if frozen["contract"] != current_contract():
        raise ValueError("Judge differs from the committed freeze; do not spend or evaluate")
    return frozen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    if FREEZE.exists():
        raise ValueError("Never overwrite the judge freeze")
    value = {
        "frozen_before_validation": True,
        "calibration_revision_commit": args.revision,
        "contract": current_contract(),
        "decision_rule": "context-decision-rule.json",
    }
    atomic_write_text(FREEZE, json.dumps(value, indent=2, ensure_ascii=False) + "\n", newline="\n")
    print(f"Frozen contract SHA-256: {canonical_hash(value['contract'])}")


if __name__ == "__main__":
    main()
