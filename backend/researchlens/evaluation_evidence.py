"""Compatibility entry point for researchlens_eval.evaluation_evidence."""

import sys

from researchlens_eval import evaluation_evidence as _implementation

sys.modules[__name__] = _implementation
