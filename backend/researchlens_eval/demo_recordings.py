"""Build the public demo's recorded answers from committed evaluation evidence.

The raw answer-quality bundles stay in ignored run storage. The owner-grading packet is
committed, hash-pinned by the scoring key, and shows each selected answer in full together
with the exact passage text the model saw. This module copies those recorded answers
verbatim and adds only source metadata (section, XML location, attribution) looked up by
passage ID in the current corpus. It makes no API calls.

    uv run --directory backend python -m researchlens_eval.demo_recordings
    uv run --directory backend python -m researchlens_eval.demo_recordings --check
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from pydantic import TypeAdapter
from researchlens.ingest import TECHNICAL_CORPUS, chunk_documents
from researchlens.models import Document

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "evaluation" / "reviews" / "2026-10-14-answer-judge"
PACKET = REVIEW / "owner-grading.md"
SCORING_KEY = REVIEW / "scoring-key.json"
MANIFEST = ROOT / "evaluation" / "answer-quality-evidence-manifest.json"
PLAN = ROOT / "evaluation" / "answer-plan.json"
OUTPUT = ROOT / "data" / "demo" / "recorded-answers.json"

# Packet item -> public example. Claim, qualification, forbidden-claim and abstention
# items show the entire recorded answer; citation items do not, so none is used here.
SELECTED = (
    ("canopy-heater-fusion", "G048", "Compare illumination and fusion across two studies"),
    ("wafer-tdi-noise", "G020", "TDI stages and fixed-pattern noise in wafer inspection"),
    ("aw-ssim-loss", "G021", "How AW-SSIM differs from standard SSIM"),
    ("rotation-augmentation", "G001", "Rotating labelled canopy images without relabelling"),
    ("unsupported-trial", "G010", "A question the papers cannot answer"),
)
CONFIGURATIONS = {
    "qwen16k": ("full", "Qwen3-4B", 16000),
    "qwen12k": ("full", "Qwen3-4B", 12000),
}
FULL_ANSWER_TYPES = {"required claim", "qualification", "forbidden claim", "abstention"}
MESSAGES = {
    "answered": "Answer based on the supplied passages.",
    "insufficient_evidence": (
        "The retrieved passages do not provide enough evidence to answer this question."
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_packet(text: str) -> dict[str, dict]:
    """Return packet items by ID with question, status, sections and cited passage text."""
    parts = re.split(r"^## (G\d{3})\n", text.split("\n## Source attribution\n")[0], flags=re.M)
    items = {}
    for item_id, body in zip(parts[1::2], parts[2::2], strict=True):
        body = body.split("\n| Verdict |")[0]
        sections = [
            {"text": section, "citation_ids": re.findall(r"`([^`]+)`", citations)}
            for section, citations in re.findall(
                r"^Section \d+\n\n> (.+?)\n\nCitations: (.+?)$", body, flags=re.M | re.S
            )
        ]
        items[item_id] = {
            "type": re.search(r"^Judgment type: (.+)$", body, flags=re.M).group(1),
            "question": re.search(r"^Question\n\n(.+?)\n\n", body, flags=re.M | re.S).group(1),
            "status": re.search(r"^Response status: `(\w+)`$", body, flags=re.M).group(1),
            "sections": sections,
            "passages": dict(
                re.findall(r"^### `([^`]+)`\n\n> (.+?)\n\n", body + "\n\n", re.M | re.S)
            ),
        }
    return items


def build(root: Path = ROOT) -> dict:
    review = root / REVIEW.relative_to(ROOT)
    packet_path, key_path = review / PACKET.name, review / SCORING_KEY.name
    key = json.loads(key_path.read_text(encoding="utf-8"))
    manifest = json.loads((root / MANIFEST.relative_to(ROOT)).read_text(encoding="utf-8"))
    plan = json.loads((root / PLAN.relative_to(ROOT)).read_text(encoding="utf-8"))
    if sha256(packet_path) != key["packet_sha256"]:
        raise ValueError("owner-grading.md does not match the scoring key's packet hash")
    if key["archive_sha256"] != manifest["archive"]["sha256"]:
        raise ValueError("Scoring key and evidence manifest describe different archives")
    runs = {run["run_sha256"]: run for run in manifest["runs"]}
    items = parse_packet(packet_path.read_text(encoding="utf-8"))
    keyed = {item["id"]: item for item in key["items"]}
    corpus = chunk_documents(
        TypeAdapter(list[Document]).validate_json(
            (root / TECHNICAL_CORPUS.relative_to(ROOT)).read_bytes()
        )
    )
    metadata = {passage.id: passage for passage in corpus}

    examples = []
    for example_id, item_id, title in SELECTED:
        item, entry = items[item_id], keyed[item_id]
        if item["type"] not in FULL_ANSWER_TYPES:
            raise ValueError(f"{item_id} does not show the entire answer")
        if entry["run_sha256"] not in runs:
            raise ValueError(f"{item_id} references a run missing from the evidence manifest")
        tier, retrieval_model, context_chars = CONFIGURATIONS[entry["configuration"]]
        cited = [cid for section in item["sections"] for cid in section["citation_ids"]]
        if set(cited) != set(item["passages"]) or (item["status"] == "answered") != bool(cited):
            raise ValueError(f"{item_id} citations do not match its visible passages")
        passages = []
        for passage_id in dict.fromkeys(cited):
            source = metadata.get(passage_id)
            if source is None:
                raise ValueError(f"{item_id} cites {passage_id}, which is not in the corpus")
            passages.append(
                {**source.model_dump(mode="json"), "text": item["passages"][passage_id]}
                | {"score": None}
            )
        examples.append(
            {
                "id": example_id,
                "title": title,
                "question": item["question"],
                "recorded": {
                    "study_id": manifest["study_id"],
                    "recorded_on": plan["prices"]["date"],
                    "model": plan["model"],
                    "configuration": entry["configuration"],
                    "retrieval_tier": tier,
                    "retrieval_model": retrieval_model,
                    "context_chars": context_chars,
                    "case_id": entry["case_id"],
                    "packet_item": item_id,
                    "run_sha256": entry["run_sha256"],
                },
                "answer": {
                    "status": item["status"],
                    "mode": "openai",
                    "message": MESSAGES[item["status"]],
                    "sections": item["sections"],
                    "passages": passages,
                    "model": plan["model"],
                },
            }
        )
    return {
        "schema_version": 1,
        "description": (
            "Recorded gpt-6-luna answers from the development answer-quality study, copied "
            "verbatim from the committed blind-grading packet. Passage text is the excerpt "
            "the model saw, before readable formulas were adopted. Section, location and "
            "attribution come from the current corpus by passage ID. Only cited passages "
            "were recorded in the packet; other supplied passages are not shown."
        ),
        "source": {
            "packet": packet_path.relative_to(root).as_posix(),
            "packet_sha256": key["packet_sha256"],
            "scoring_key": key_path.relative_to(root).as_posix(),
            "archive_sha256": key["archive_sha256"],
        },
        "examples": examples,
    }


def render(document: dict) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true", help="fail if the output is stale")
    args = parser.parse_args(argv)
    document = build()
    expected = render(document)
    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.is_file() else ""
        if current != expected:
            print(f"{args.output} is stale; rerun without --check", file=sys.stderr)
            return 1
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(expected, encoding="utf-8", newline="\n")
    print(f"Wrote {len(document['examples'])} recorded answers to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
