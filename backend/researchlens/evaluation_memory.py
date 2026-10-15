"""Compatibility entry point for researchlens_eval.evaluation_memory."""

import sys

from researchlens_eval import evaluation_memory as _implementation

sys.modules[__name__] = _implementation
