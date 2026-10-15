"""Compatibility entry point for researchlens_eval.evaluation_core."""

import sys

from researchlens_eval import evaluation_core as _implementation

sys.modules[__name__] = _implementation
