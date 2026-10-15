"""Compatibility entry point for researchlens_eval.evaluation_reporting."""

import sys

from researchlens_eval import evaluation_reporting as _implementation

sys.modules[__name__] = _implementation
