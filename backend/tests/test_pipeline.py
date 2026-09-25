import pytest
from fastapi.testclient import TestClient
from researchlens.api import create_app
from researchlens.ingest import CORPUS, build_index, chunk_documents
from researchlens.models import Document
from researchlens.retrieval import Retriever


@pytest.fixture
def client(tmp_path):
    index = tmp_path / "index.json"
    build_index(CORPUS, index)
    with TestClient(create_app(Retriever.from_path(index))) as client:
        yield client


def test_question_returns_traceable_fixture_passage(client):
    response = client.post("/api/ask", json={"question": "Does dust cause false positives?"})
    assert response.status_code == 200
    answer = response.json()
    assert answer["passages"][0]["document_id"] == "fixture-dark-field"
    assert "Dust also scattered light" in answer["passages"][0]["text"]
    assert answer["passages"][0]["id"] == "fixture-dark-field:p2:w0"
    assert answer["mode"] == "local_preview"
    assert answer["input_tokens"] is None


def test_no_overlap_is_not_presented_as_an_answer(client):
    answer = client.post("/api/ask", json={"question": "Who composed Beethoven symphonies?"}).json()
    assert answer["status"] == "no_matches"
    assert answer["passages"] == []


@pytest.mark.parametrize("question", ["   ", "ab", "x" * 2001])
def test_invalid_questions_are_rejected(client, question):
    assert client.post("/api/ask", json={"question": question}).status_code == 422


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
