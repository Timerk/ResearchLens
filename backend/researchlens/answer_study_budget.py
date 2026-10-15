"""Compatibility entry point for researchlens_eval.answer_study_budget."""

import sys

from researchlens_eval import answer_study_budget as _implementation

sys.modules[__name__] = _implementation
