"""Compatibility entry point for researchlens_eval.answer_scoring."""

import sys

from researchlens_eval import answer_scoring as _implementation

sys.modules[__name__] = _implementation
