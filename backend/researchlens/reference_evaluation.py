"""Compatibility entry point for researchlens_eval.reference_evaluation."""

import sys

from researchlens_eval import reference_evaluation as _implementation

if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
