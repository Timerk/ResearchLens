"""Compatibility entry point for researchlens_eval.compare_retrieval."""

import sys

from researchlens_eval import compare_retrieval as _implementation

if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
