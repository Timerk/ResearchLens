"""Compatibility entry point for researchlens_eval.answer_judge_experiment."""

import sys

from researchlens_eval import answer_judge_experiment as _implementation

sys.modules[__name__] = _implementation
