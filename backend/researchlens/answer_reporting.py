"""Compatibility entry point for researchlens_eval.answer_reporting."""

import sys

from researchlens_eval import answer_reporting as _implementation

sys.modules[__name__] = _implementation
