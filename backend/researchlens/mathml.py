"""Approved mathml-readable-v2 transcription with whole-formula fallback."""

import xml.etree.ElementTree as ET
from collections import Counter


def local_name(node: ET.Element) -> str:
    return node.tag.rsplit("}", 1)[-1]


def render_math(node: ET.Element) -> str:
    """Render a conservative presentation MathML subset with explicit grouping."""
    tag = local_name(node)
    children = list(node)
    if tag in {"mi", "mn", "mo", "mtext"}:
        if children:
            raise ValueError("Unsupported children in MathML token")
        value = " ".join((node.text or "").split())
        if not value and tag != "mtext":
            raise ValueError("Unsupported empty MathML token")
        variant = node.get("mathvariant", "normal")
        if variant not in {"normal", "italic"}:
            if variant not in {"bold", "sans-serif", "double-struck", "script"}:
                raise ValueError("Unsupported MathML variant")
            value = f"{variant}({value})"
        return value
    if (node.text or "").strip() or any((c.tail or "").strip() for c in children):
        raise ValueError("Unsupported mixed MathML content")
    if tag == "mspace" and not children:
        if node.get("width", "0").startswith("-"):
            raise ValueError("Unsupported negative MathML spacing")
        return ""
    if tag in {"math", "mrow", "mstyle", "mtd"}:
        value = " ".join(filter(None, (render_math(child) for child in children)))
        if not value and tag != "mtd":
            raise ValueError("Unsupported empty MathML row")
        return value
    if tag in {"msub", "msup", "munder", "mover", "mfrac"} and len(children) == 2:
        left, right = (render_math(child) for child in children)
        if not left or not right:
            raise ValueError("Unsupported empty MathML operand")
        if tag == "mfrac":
            if node.get("linethickness", "1") != "1":
                raise ValueError("Unsupported fraction line convention")
            return f"({left}) / ({right})"
        if tag in {"munder", "mover"}:
            return f"{'under' if tag == 'munder' else 'over'}({left}; {right})"
        operator = {"msub": "_", "msup": "^"}[tag]
        return f"({left}){operator}({right})"
    if tag == "msubsup" and len(children) == 3:
        base, subscript, superscript = (render_math(child) for child in children)
        return f"({base})_({subscript})^({superscript})"
    if tag == "mfenced":
        separators = "".join(node.get("separators", ",").split())
        values = [render_math(child) for child in children]
        body = values[0] if values else ""
        for i, value in enumerate(values[1:]):
            separator = separators[min(i, len(separators) - 1)] if separators else ""
            body += f" {separator} {value}" if separator else f" {value}"
        return f"{node.get('open', '(')}{body}{node.get('close', ')')}"
    if tag in {"mtable", "mtr"}:
        expected = "mtr" if tag == "mtable" else "mtd"
        if not children or any(local_name(c) != expected for c in children):
            raise ValueError("Unsupported MathML table structure")
        separator = "; " if tag == "mtable" else ", "
        return "[" + separator.join(render_math(child) for child in children) + "]"
    # Prescripts require a notation decision and human scientific review.
    raise ValueError(f"Unsupported MathML element: {tag}")


def readable_prose(
    element: ET.Element, counts: Counter, replacements: list[str] | None = None
) -> str:
    def parts(node: ET.Element) -> str:
        if local_name(node) in {"math", "inline-formula", "disp-formula"}:
            math = next((child for child in node.iter() if local_name(child) == "math"), None)
            if math is not None:
                try:
                    rendered = render_math(math)
                except ValueError:
                    counts["unsupported_formulas"] += 1
                else:
                    if rendered:
                        counts["rendered_formulas"] += 1
                        if replacements is not None:
                            replacements.append(rendered)
                        return f" {rendered} "
            counts["remaining_placeholders"] += 1
            if replacements is not None:
                replacements.append("[formula omitted]")
            return " [formula omitted] "
        return (node.text or "") + "".join(parts(child) + (child.tail or "") for child in node)

    return " ".join(parts(element).split())
