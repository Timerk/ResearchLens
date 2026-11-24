import pytest
from researchlens.corpus import adopted_corpus_bytes


@pytest.fixture(scope="session")
def adopted_corpus(tmp_path_factory):
    """The 2026-10-14 adopted corpus that evaluation labels, datasets and results pin.

    The live corpus has block spacing since 2026-11-24 (docs/block-spacing-fix.md); the
    evaluation inputs stay pinned to this byte-identical reconstruction from the originals.
    """
    path = tmp_path_factory.mktemp("adopted") / "documents.json"
    path.write_bytes(adopted_corpus_bytes())
    return path
