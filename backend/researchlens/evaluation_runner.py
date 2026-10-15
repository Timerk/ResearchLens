"""Compatibility entry point for researchlens_eval.evaluation_runner."""

import sys

from researchlens_eval import evaluation_runner as _implementation

sys.modules[__name__] = _implementation
