"""Compatibility entry point for researchlens_eval.evaluation_schema."""

import sys

from researchlens_eval import evaluation_schema as _implementation

sys.modules[__name__] = _implementation
