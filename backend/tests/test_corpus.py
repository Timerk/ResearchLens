import hashlib
import json
import shutil
import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter
from researchlens.api import create_app
from researchlens.config import Settings
from researchlens.corpus import DIRECTORY, LICENSE_URL, SOURCES, build_corpus, extract, prose_text
from researchlens.ingest import TECHNICAL_CORPUS, build_index, chunk_documents
from researchlens.models import Document
from researchlens.retrieval import Retriever


def test_checked_in_corpus_rebuilds_offline_and_has_traceable_provenance(tmp_path):
    shutil.copytree(DIRECTORY, tmp_path / "technical")
    target = tmp_path / "technical"
    before = {
        name: (target / name).read_bytes()
        for name in ("manifest.json", "documents.json", "NOTICE.txt")
    }
    build_corpus(target)
    assert all((target / name).read_bytes() == content for name, content in before.items())
    documents = TypeAdapter(list[Document]).validate_json(before["documents.json"])
    assert {d.id for d in documents} == {p.lower() for p in SOURCES}
    painted = next(d for d in documents if d.id == "pmc11768589")
    assert len(painted.attribution.authors) == 5
    assert "Tao Peng" not in painted.attribution.authors  # Academic editor, not an author.
    for document in documents:
        raw = (target / "originals" / f"{document.id.upper()}.xml").read_bytes()
        root = ET.fromstring(raw)
        assert document.attribution.source_sha256 == hashlib.sha256(raw).hexdigest()
        assert document.attribution.authors
        assert document.attribution.license_url == LICENSE_URL
        assert document.kind == "technical"
        assert len(document.paragraph_sources) > 10
        for paragraph, source in zip(
            document.text.split("\n\n"), document.paragraph_sources, strict=True
        ):
            assert source.section
            assert prose_text(root.find(source.locator)) == paragraph
            assert "Acknowledgments" not in source.section
            assert "References" not in source.section
        passages = chunk_documents([document])
        assert all(p.attribution == document.attribution and p.source_locator for p in passages)


def test_changed_original_is_rejected(tmp_path):
    shutil.copytree(DIRECTORY, tmp_path / "technical")
    target = tmp_path / "technical"
    path = target / "originals" / "PMC11510794.xml"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="checksum"):
        build_corpus(target)


def test_rejects_wrong_license_or_article_identity():
    raw = (DIRECTORY / "originals" / "PMC11510794.xml").read_bytes()
    with pytest.raises(ValueError, match="license"):
        extract(raw.replace(b"licenses/by/4.0", b"licenses/by-nc-nd/4.0"), "PMC11510794")
    with pytest.raises(ValueError, match="DOI"):
        extract(raw, "PMC10934137")


def test_technical_retrieval_and_http_citations(tmp_path):
    index = tmp_path / "index.json"
    build_index(TECHNICAL_CORPUS, index)
    retriever = Retriever.from_path(index)
    queries = {
        "forward backward lighting aircraft glass canopy": "pmc11510794",
        "deflectometry painted heating devices ResNet": "pmc11768589",
        "TDI stages column fixed pattern noise wafer": "pmc10934137",
        "AW-SSIM artificial defect generation two-stage training": "pmc11121878",
    }
    for question, expected in queries.items():
        assert retriever.search(question)[0].document_id == expected
    with TestClient(create_app(retriever, Settings())) as client:
        response = client.post("/api/ask", json={"question": next(iter(queries))})
    assert response.status_code == 200
    passage = response.json()["passages"][0]
    assert passage["attribution"]["license_url"] == LICENSE_URL
    assert passage["source_section"] and passage["source_locator"]
    assert passage["kind"] == "technical"
    assert response.json()["input_tokens"] is None


def test_manifest_matches_document_metadata():
    manifest = json.loads((DIRECTORY / "manifest.json").read_text(encoding="utf-8"))
    documents = TypeAdapter(list[Document]).validate_json(TECHNICAL_CORPUS.read_bytes())
    for record, document in zip(manifest["sources"], documents, strict=True):
        assert record["id"] == document.id
        assert record["title"] == document.title
        assert record["doi"] == document.attribution.doi
        assert record["review_status"] == "not_human_reviewed"
        assert "creativecommons.org/licenses/by/4.0" in record["permission_evidence"]


def test_prose_retains_formula_context_without_flattening_math():
    node = ET.fromstring(
        "<p>Noise is <inline-formula><math><mi>x</mi><mn>2</mn></math>"
        "</inline-formula> under these conditions.</p>"
    )
    assert prose_text(node) == "Noise is [formula omitted] under these conditions."
