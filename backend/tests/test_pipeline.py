import pytest
from researchlens.ingest import CORPUS, build_index, chunk_documents
from researchlens.models import Document


def test_index_is_reproducible(tmp_path):
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    build_index(CORPUS, first)
    build_index(CORPUS, second)
    assert first.read_bytes() == second.read_bytes()


def test_chunk_windows_preserve_text_and_source_identity():
    document = Document(
        id="test",
        title="Test",
        source_url=None,
        license="CC0-1.0",
        kind="synthetic",
        text="one two three four five",
    )
    passages = chunk_documents([document], max_words=2)
    assert [p.text for p in passages] == ["one two", "three four", "five"]
    assert len({p.id for p in passages}) == 3
    assert all(p.document_id == "test" for p in passages)
    with pytest.raises(ValueError, match="unique"):
        chunk_documents([document, document])
