"""Compatibility entry point for researchlens_eval.evaluation_metrics."""

import sys

from researchlens_eval import evaluation_metrics as _implementation

sys.modules[__name__] = _implementation
