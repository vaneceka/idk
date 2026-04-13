import json

from assignment.text.text_assignment_model import StyleSpec, TextAssignment


def load_text_assignment(path: str) -> TextAssignment:
    """
    Načte definici zadání textového dokumentu ze souboru JSON
    a převede ji na objekt TextAssignment.

    Args:
        path: Cesta k JSON souboru se zadáním.

    Returns:
        Objekt TextAssignment obsahující specifikaci stylů,
        nadpisů, objektů a bibliografie.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    styles: dict[str, StyleSpec] = {}

    for name, spec in (data.get("styles", {}) or {}).items():
        styles[name] = StyleSpec(
            name=name,
            font=spec.get("type"),
            size=spec.get("size"),
            bold=spec.get("bold"),
            italic=spec.get("italic"),
            allCaps=spec.get("allCaps"),
            alignment=spec.get("alignment"),
            color=spec.get("color"),
            lineHeight=spec.get("lineHeight"),
            pageBreakBefore=spec.get("pageBreakBefore"),
            numLevel=spec.get("numLevel"),
            basedOn=spec.get("basedOn"),
            spaceBefore=spec.get("spaceBefore"),
            tabs=[(t[0], int(t[1])) for t in (spec.get("tabs", []) or [])] or None,
        )

    return TextAssignment(
        styles=styles,
        headlines=data.get("headlines", []) or [],
        objects=data.get("objects", []) or [],
        bibliography=data.get("bibliography", []) or [],
    )
