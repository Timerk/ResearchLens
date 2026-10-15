"""Compatibility entry point for researchlens_eval.answer_grading."""

import sys

from researchlens_eval import answer_grading as _implementation

if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
