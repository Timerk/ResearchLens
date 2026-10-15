"""Compatibility entry point for researchlens_eval.answer_judge_review."""

import sys

from researchlens_eval import answer_judge_review as _implementation

if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
