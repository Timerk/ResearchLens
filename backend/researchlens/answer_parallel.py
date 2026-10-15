"""Compatibility entry point for researchlens_eval.answer_parallel."""

import sys

from researchlens_eval import answer_parallel as _implementation

sys.modules[__name__] = _implementation
