"""Compatibility entry point for researchlens_eval.answer_evaluation."""

import sys

from researchlens_eval import answer_evaluation as _implementation

sys.modules[__name__] = _implementation
