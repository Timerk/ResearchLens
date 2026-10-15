"""Compatibility entry point for researchlens_eval.answer_constants."""

import sys

from researchlens_eval import answer_constants as _implementation

sys.modules[__name__] = _implementation
