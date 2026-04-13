import json

from assignment.spreadsheet.spreadsheet_assignment_model import (
    SpreadsheetAssignment,
    SpreadsheetCellSpec,
)


def load_spreadsheet_assignment(path: str) -> SpreadsheetAssignment:
    """
    Načte definici zadání tabulkového procesoru ze souboru JSON
    a převede ji na objekt SpreadsheetAssignment.

    Args:
        path: Cesta k JSON souboru se zadáním.

    Returns:
        Objekt SpreadsheetAssignment obsahující specifikaci buněk,
        okrajů a grafu.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cells: dict[str, SpreadsheetCellSpec] = {}

    for addr, spec in data.get("cells", {}).items():
        cells[addr] = SpreadsheetCellSpec(
            address=addr,
            input=spec.get("input"),
            expression=spec.get("expression"),
            style=spec.get("style"),
            conditionalFormat=spec.get("conditionalFormat"),
        )

    return SpreadsheetAssignment(
        cells=cells,
        borders=data.get("borders", []),
        chart=data.get("chart"),
    )
