"""Readable MathML rendering used by the canonical corpus extractor."""

import xml.etree.ElementTree as ET
from collections import Counter

import pytest
from researchlens.corpus import prose_text
from researchlens.mathml import readable_prose, render_math


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
