"""Checks for proposal rendering without changing the approved extraction."""

import xml.etree.ElementTree as ET
from collections import Counter

import pytest
from researchlens.corpus import prose_text
from researchlens.formula_prototype import (
    build_prototype,
    formula_alignment,
    readable_prose,
    render_math,
)
from researchlens.formula_remapping import (
    boundary,
    held_out_reference_review,
    remap_labels,
    remap_span,
    window_ranges,
)
from researchlens.ingest import TECHNICAL_CORPUS, chunk_documents
from researchlens.models import Document


def test_symbol_restores_gaussian_sigma_in_canonical_and_preserves_legacy_behavior():
    node = ET.fromstring(
        '<p>Gaussian deviation (<inline-formula><math xmlns="http://www.w3.org/1998/Math/MathML">'
        "<mi>σ</mi></math></inline-formula>) determines the window.</p>"
    )
    counts = Counter()
    assert readable_prose(node, counts) == "Gaussian deviation ( σ ) determines the window."
    assert counts == {"rendered_formulas": 1}
    assert prose_text(node) == "Gaussian deviation ( σ ) determines the window."
    assert prose_text(node, readable_formulas=False) == (
        "Gaussian deviation ( [formula omitted] ) determines the window."
    )


def test_fraction_and_scripts_preserve_grouping():
    math = ET.fromstring(
        "<math><mfrac><msub><mi>k</mi><mn>1</mn></msub>"
        "<msup><mi>σ</mi><mn>2</mn></msup></mfrac></math>"
    )
    assert render_math(math) == "((k)_(1)) / ((σ)^(2))"


def test_unsupported_formula_keeps_explicit_placeholder():
    node = ET.fromstring(
        "<p>Before <inline-formula><math><mmultiscripts><mi>x</mi>"
        "</mmultiscripts></math></inline-formula> after.</p>"
    )
    counts = Counter()
    assert readable_prose(node, counts) == "Before [formula omitted] after."
    assert counts == {"unsupported_formulas": 1, "remaining_placeholders": 1}
    with pytest.raises(ValueError, match="Unsupported"):
        render_math(ET.fromstring("<mmultiscripts />"))


def test_prototype_cannot_overwrite_canonical_corpus():
    with pytest.raises(ValueError, match="must stay under"):
        build_prototype(TECHNICAL_CORPUS.parent)


@pytest.mark.parametrize(
    "markup",
    [
        "<math><mfrac><mn>1</mn></mfrac></math>",
        "<math><mi><mn>12</mn></mi></math>",
        "<math><mrow>42<mi>x</mi></mrow></math>",
        "<math><mfrac linethickness='0'><mn>1</mn><mn>2</mn></mfrac></math>",
        "<math><msqrt><mn>2</mn></msqrt></math>",
        "<math><mi /></math>",
    ],
)
def test_malformed_or_unsupported_formula_falls_back_as_a_whole(markup):
    counts = Counter()
    node = ET.fromstring(f"<p>Before {markup} after.</p>")
    assert readable_prose(node, counts) == "Before [formula omitted] after."
    assert counts["remaining_placeholders"] == 1


def test_accents_are_not_exponents_and_fences_do_not_invent_commas():
    assert (
        render_math(ET.fromstring("<mover accent='true'><mi>x</mi><mo>¯</mo></mover>"))
        == "over(x; ¯)"
    )
    assert (
        render_math(ET.fromstring("<mfenced separators=''><mi>x</mi><mi>y</mi></mfenced>"))
        == "(x y)"
    )
    assert (
        render_math(
            ET.fromstring(
                "<mfenced separators=';, '><mi>a</mi><mi>b</mi><mi>c</mi><mi>d</mi></mfenced>"
            )
        )
        == "(a ; b , c , d)"
    )


def test_numbers_and_variants_are_preserved_without_computation():
    assert (
        render_math(
            ET.fromstring(
                "<mrow><mn>0.61</mn><mo>×</mo><mn>0.405</mn><mtext> </mtext>"
                "<mi mathvariant='bold'>k</mi></mrow>"
            )
        )
        == "0.61 × 0.405 bold(k)"
    )


def test_alignment_is_atomic_and_rejects_prose_changes():
    edits = formula_alignment("A [formula omitted] B", "A σ B", ["σ"])
    assert boundary(2, edits) == 2
    assert boundary(19, edits) == 3
    with pytest.raises(ValueError, match="inside"):
        boundary(4, edits)
    with pytest.raises(ValueError, match="beyond"):
        formula_alignment("A [formula omitted] B", "A σ C", ["σ"])


def sample_document(text):
    return Document(
        id="sample",
        title="Sample",
        source_url="https://example.org",
        license="CC-BY-4.0",
        kind="technical",
        text=text,
    )


def test_repeated_quotes_follow_original_location_and_split_remains_and():
    before = sample_document("a b repeat a b repeat")
    old_passages = chunk_documents([before], max_words=3)
    new_passages = chunk_documents([before], max_words=2)
    span = {"passage_id": old_passages[1].id, "start": 0, "end": 10, "quote": "a b repeat"}
    labels = {
        "cases": [{"case_id": "case", "groups": [{"id": "part-1", "alternatives": [[span]]}]}]
    }
    proposed, rows = remap_labels(labels, old_passages, new_passages, {("sample", 1): []})
    assert rows[0]["status"] == "shifted only"
    assert [s["passage_id"] for s in rows[0]["new"]] == ["sample:p1:w2", "sample:p1:w4"]
    assert len(proposed["cases"][0]["groups"][0]["alternatives"][0]) == 2
    assert labels["cases"][0]["groups"][0]["alternatives"][0] == [span]


def test_partial_placeholder_cannot_map():
    before = sample_document("A [formula omitted] B")
    after = sample_document("A σ B")
    old, new = chunk_documents([before]), chunk_documents([after])
    status, mapped, _ = remap_span(
        {"passage_id": old[0].id, "start": 4, "end": 19, "quote": "ormula omitted]"},
        {p.id: p for p in old},
        {p.id: p for p in new},
        {("sample", 1): formula_alignment(before.text, after.text, ["σ"])},
        window_ranges(old),
        window_ranges(new),
    )
    assert status == "cannot map"
    assert mapped == []


def test_held_out_reference_split_and_freeze_check_only_need_references():
    document = sample_document("a b c d e f")
    old = chunk_documents([document], max_words=3)
    new = chunk_documents([document], max_words=2)
    held_out = {
        "corpus_sha256": "old",
        "source_versions": [],
        "cases": [
            {
                "id": "hold-test",
                "references": [
                    {
                        "passage_id": old[1].id,
                        "source_id": "sample",
                        "paragraph": 1,
                        "source_section": None,
                        "source_locator": None,
                    }
                ],
            }
        ],
    }
    report = held_out_reference_review(
        held_out, old, new, {"source_sha256": "candidate"}, {("sample", 1): []}
    )
    assert report["references"][0]["status"] == "ID changed"
    assert report["references"][0]["proposed_passage_ids"] == ["sample:p1:w2", "sample:p1:w4"]
    assert report["freeze_check"]["corpus_pin_matches"] is False
