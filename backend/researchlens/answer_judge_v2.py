"""Compatibility entry point for researchlens_eval.answer_judge_v2."""

import sys

from researchlens_eval import answer_judge_v2 as _implementation

sys.modules[__name__] = _implementation
