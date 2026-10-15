"""Compatibility entry point for researchlens_eval.evaluation."""

import sys

from researchlens_eval import evaluation as _implementation

if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
