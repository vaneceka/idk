from dataclasses import dataclass
from typing import Any


@dataclass
class SpreadsheetCellSpec:
    """
    Reprezentuje specifikaci jedné buňky v zadání tabulkového procesoru.

    Attributes:
        address: Adresa buňky.
        input: Očekávaná vstupní hodnota buňky.
        expression: Očekávaný vzorec nebo výraz buňky.
        style: Očekávané stylové vlastnosti buňky.
        conditionalFormat: Očekávaná pravidla podmíněného formátování buňky.
    """

    address: str
    input: Any | None = None
    expression: str | None = None
    style: dict | None = None
    conditionalFormat: list[dict] | None = None


@dataclass
class SpreadsheetAssignment:
    """
    Reprezentuje celé zadání pro kontrolu tabulkového procesoru.

    Attributes:
        cells: Mapa adres buněk na jejich očekávané specifikace.
        borders: Seznam definic očekávaného ohraničení tabulek.
        chart: Očekávaná specifikace grafu.
    """

    cells: dict[str, SpreadsheetCellSpec]
    borders: list[dict]
    chart: dict | None
