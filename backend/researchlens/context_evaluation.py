"""Compatibility entry point for researchlens_eval.context_evaluation."""

import sys

from researchlens_eval import context_evaluation as _implementation

sys.modules[__name__] = _implementation
