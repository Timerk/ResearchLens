"""Download the approved CC BY 4.0 articles and reproduce the technical text corpus.

Default: rebuild offline from checked-in XML and verify the recorded checksums.
--download: explicitly refresh originals and manifest from Europe PMC.
"""

import argparse
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from researchlens.ingest import ROOT
from researchlens.models import Attribution, Document, ParagraphSource

DIRECTORY = ROOT / "data" / "technical"
SOURCES = {
    "PMC11510794": "10.3390/s24206717",
    "PMC11768589": "10.3390/s25020527",
    "PMC10934137": "10.3390/s24051622",
    "PMC11121878": "10.3390/jimaging10050111",
}
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
CHANGES = (
    "Prose extracted from article XML; whitespace normalized; section and XML locations retained; "
    "split into paragraphs and word-window passages. Figures, tables, captions, references, "
    "and back matter are omitted. Mathematical formula markup is replaced with [formula omitted]. "
    "This is a partial text extraction; consult the original article for omitted material."
)


def text(element: ET.Element | None) -> str:
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def prose_text(element: ET.Element) -> str:
    """Keep prose surrounding formulas without flattening MathML into false numeric claims."""

    def parts(node: ET.Element) -> str:
        if node.tag.rsplit("}", 1)[-1] in {"math", "inline-formula", "disp-formula"}:
            return " [formula omitted] "
        return (node.text or "") + "".join(parts(child) + (child.tail or "") for child in node)

    return " ".join(parts(element).split())


def extract(raw: bytes, pmcid: str) -> tuple[Document, dict]:
    root = ET.fromstring(raw)
    meta = root.find("./front/article-meta")
    if meta is None:
        raise ValueError("Missing article metadata")
    doi = next((text(e) for e in meta.findall("article-id") if e.get("pub-id-type") == "doi"), "")
    if doi.casefold() != SOURCES[pmcid].casefold():
        raise ValueError(f"Unexpected DOI for {pmcid}")
    permissions = meta.find("permissions")
    permission_xml = ET.tostring(permissions, encoding="unicode") if permissions is not None else ""
    if LICENSE_URL not in permission_xml:
        raise ValueError(f"Explicit CC BY 4.0 license not found for {pmcid}")
    authors = []
    for contributor in meta.findall(".//contrib"):
        if (
            contributor.get("contrib-type", "author") != "author"
            or "editor" in text(contributor.find("role")).casefold()
        ):
            continue
        name = contributor.find("name")
        if name is None:
            name = contributor.find("string-name")
        if name is not None:
            authors.append(
                " ".join(filter(None, [text(name.find("given-names")), text(name.find("surname"))]))
            )
    dates = meta.findall("pub-date")
    date = next(
        (d for d in dates if d.find("day") is not None and d.find("month") is not None), None
    )
    if not authors or date is None:
        raise ValueError(f"Missing authors or publication date for {pmcid}")
    published = (
        f"{text(date.find('year'))}-{int(text(date.find('month'))):02d}-"
        f"{int(text(date.find('day'))):02d}"
    )
    title = text(meta.find("./title-group/article-title"))
    copyright_notice = text(meta.find("./permissions/copyright-statement"))
    if not title or not copyright_notice:
        raise ValueError(f"Missing title or copyright notice for {pmcid}")
    digest = hashlib.sha256(raw).hexdigest()
    paragraphs = []
    provenance = []

    def visit(node: ET.Element, path: str, headings: list[str]) -> None:
        if node.tag in {
            "fig",
            "table-wrap",
            "ref-list",
            "fn-group",
            "supplementary-material",
            "boxed-text",
        }:
            return
        if node.tag == "sec":
            heading = text(node.find("title"))
            if heading.casefold() in {
                "acknowledgments",
                "acknowledgements",
                "author contributions",
                "data availability statement",
                "conflicts of interest",
                "conflict of interest",
                "funding statement",
                "footnotes",
                "references",
                "associated data",
            }:
                return
            headings = [*headings, heading] if heading else headings
        if node.tag == "p":
            paragraph = prose_text(node)
            if paragraph:
                paragraphs.append(paragraph)
                provenance.append(ParagraphSource(section=" > ".join(headings), locator=path))
            return
        counts: dict[str, int] = {}
        for child in node:
            counts[child.tag] = counts.get(child.tag, 0) + 1
            visit(child, f"{path}/{child.tag}[{counts[child.tag]}]", headings)

    for i, abstract in enumerate(meta.findall("abstract"), start=1):
        visit(abstract, f"./front/article-meta/abstract[{i}]", ["Abstract"])
    body = root.find("body")
    if body is None:
        raise ValueError(f"Missing full article body for {pmcid}")
    visit(body, "./body", [])
    if not paragraphs:
        raise ValueError(f"No prose extracted for {pmcid}")
    attribution = Attribution(
        authors=authors,
        publication_date=published,
        doi=doi,
        license_url=LICENSE_URL,
        copyright=copyright_notice,
        changes=CHANGES,
        source_sha256=digest,
    )
    document = Document(
        id=pmcid.lower(),
        title=title,
        source_url=f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/",
        license="CC-BY-4.0",
        kind="technical",
        text="\n\n".join(paragraphs),
        attribution=attribution,
        paragraph_sources=provenance,
    )
    record = {
        "id": document.id,
        "pmcid": pmcid,
        "title": title,
        "source_url": document.source_url,
        "download_url": f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML",
        "original_file": f"originals/{pmcid}.xml",
        "license": document.license,
        **attribution.model_dump(),
        "permission_evidence": text(permissions),
        "paragraph_count": len(paragraphs),
        "review_status": "not_human_reviewed",
    }
    return document, record


def build_corpus(directory: Path = DIRECTORY, download: bool = False) -> None:
    manifest_path = directory / "manifest.json"
    previous = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    )
    documents, records = [], []
    originals = directory / "originals"
    for pmcid in SOURCES:
        path = originals / f"{pmcid}.xml"
        if download:
            url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
            with urllib.request.urlopen(url, timeout=60) as response:
                raw = response.read()
            document, record = extract(raw, pmcid)  # Validate before saving.
            originals.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            record["retrieved_at"] = datetime.now(UTC).isoformat()
        else:
            raw = path.read_bytes()
            document, record = extract(raw, pmcid)
            old = next((r for r in previous.get("sources", []) if r["pmcid"] == pmcid), None)
            if old is None or old["source_sha256"] != record["source_sha256"]:
                raise ValueError(
                    f"Original checksum missing or changed for {pmcid}; inspect before refresh"
                )
            record["retrieved_at"] = old["retrieved_at"]
        documents.append(document.model_dump())
        records.append(record)
    directory.mkdir(parents=True, exist_ok=True)
    for path, data in (
        (manifest_path, {"schema_version": 1, "sources": records}),
        (directory / "documents.json", documents),
    ):
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    notices = [
        "RESEARCHLENS TECHNICAL CORPUS — THIRD-PARTY ATTRIBUTIONS",
        "These articles retain their authors' copyright and CC BY 4.0 licensing.",
        "The repository's software license does not replace the article licenses.",
        f"License: {LICENSE_URL}",
        "Article licenses do not automatically cover separately licensed third-party material "
        "or external image datasets. No external figure images or datasets are bundled.",
        f"Extraction changes: {CHANGES}",
        "Extracted text and questions have not received human scientific review.",
    ]
    for record in records:
        notices.append(
            "\n".join(
                [
                    record["title"],
                    "; ".join(record["authors"]),
                    f"Published: {record['publication_date']}",
                    record["copyright"],
                    f"DOI: https://doi.org/{record['doi']}",
                    record["source_url"],
                    record["permission_evidence"],
                ]
            )
        )
    (directory / "NOTICE.txt").write_text(
        "\n\n".join(notices) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--download", action="store_true", help="Refresh originals over the network"
    )
    build_corpus(download=parser.parse_args().download)
    print(f"Built four licensed articles in {DIRECTORY}")
