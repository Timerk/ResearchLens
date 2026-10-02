import hashlib

import numpy as np
import pytest
from researchlens.artifacts import canonical_hash
from researchlens.models import Passage
from researchlens.representation_experiments import (
    RepresentedRetriever,
    enriched_artifact,
    representation_inputs,
)


def passage(i, doc, text):
    return Passage(
        id=str(i),
        document_id=doc,
        title="Study title",
        text=text,
        paragraph=i,
        kind="synthetic",
        license="test",
        source_url=None,
        source_section="Methods",
    )


PASSAGES = [
    passage(1, "a", "First definition."),
    passage(2, "a", "Second qualification."),
    passage(3, "b", "Different study."),
]


def test_neighbor_representation_never_changes_canonical_text_or_crosses_documents():
    texts, ranges = representation_inputs(PASSAGES, "title-section-current-neighbors60-v1")
    assert "Next: Second qualification." in texts[0]
    assert "Previous: First definition." in texts[1]
    assert "Different study." not in texts[1]
    for p, text, core in zip(PASSAGES, texts, ranges, strict=True):
        assert text[core["start"] : core["end"]] == p.text


def test_visibility_maps_true_input_offsets_and_stale_representation_is_rejected():
    encoding = {
        "dimensions": 2,
        "text": "passage-text-only",
        "encoding_version": 2,
        "query_prefix": "",
    }

    class Encoder:
        def __init__(self):
            self.encoding = encoding

        def encode(self, texts):
            return np.tile([1.0, 0.0], (len(texts), 1))

        def measure_documents(self, texts):
            # Synthetic tokenizer keeps exactly the first canonical word after metadata.
            return [
                {
                    "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "input_tokens": len(text),
                    "encoded_tokens": 51,
                    "truncated": True,
                    "retained_ranges": [{"start": 0, "end": text.index("\n\n") + 2 + 5}],
                }
                for text in texts
            ]

    artifact = {
        "passages": [p.model_dump() for p in PASSAGES],
        "embeddings": {"encoding": encoding},
    }
    encoder = Encoder()
    enriched, diagnostics, measured = enriched_artifact(
        artifact, PASSAGES, encoder, "title-section-text-v1"
    )
    assert artifact["embeddings"]["encoding"]["text"] == "passage-text-only"
    assert all(p["retained_ranges"] == [{"start": 0, "end": 5}] for p in diagnostics["passages"])
    assert all(p["truncated"] for p in diagnostics["passages"])
    assert diagnostics["artifact_sha256"] == canonical_hash(enriched)
    assert diagnostics["passages"][0]["input_tokens"] == measured[0]["input_tokens"]
    adapter = RepresentedRetriever(enriched, PASSAGES, encoder, diagnostics)
    hits = adapter.search("question", 2)
    assert hits[0].text == PASSAGES[0].text
    enriched["representation"]["inputs_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Stale enriched representation"):
        RepresentedRetriever(enriched, PASSAGES, encoder, diagnostics)
