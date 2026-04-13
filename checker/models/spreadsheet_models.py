import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class CalcStyleInfo:
    """
    Uchovává rozparsované informace o stylu buňky v tabulkovém dokumentu.

    Attributes:
        borders: Mapa stran buňky na styl ohraničení.
        bold: Určuje, zda je text v buňce tučný.
        align_h: Vodorovné zarovnání obsahu buňky.
        number_format: Název číselného formátu přiřazeného buňce.
        decimal_places: Počet desetinných míst definovaný stylem.
        wrap: Určuje, zda je v buňce zapnuté zalamování textu.
    """

    borders: dict[str, str] = field(default_factory=dict)
    bold: bool = False
    align_h: str | None = None
    number_format: str | None = None
    decimal_places: int | None = None
    wrap: bool | None = None


@dataclass
class BorderProblem:
    """
    Reprezentuje nalezený problém s ohraničením tabulky.

    Attributes:
        kind: Typ nalezeného problému.
        sheet: Název listu, ve kterém byl problém nalezen.
        side: Strana tabulky, které se problém týká.
        range: Rozsah tabulky, ve kterém byl problém detekován.
        cell: Konkrétní buňka, ke které se problém vztahuje.
        expected: Očekávaný styl ohraničení.
    """

    kind: str
    sheet: str | None = None
    side: str | None = None
    range: str | None = None
    cell: str | None = None
    expected: str | None = None


@dataclass
class SheetXmlInfo:
    """
    Uchovává informace o XML reprezentaci listu v XLSX dokumentu.

    Attributes:
        xml: Kořenový XML element listu.
        path: Vnitřní cesta k XML souboru listu v archivu.
    """

    xml: ET.Element
    path: str
