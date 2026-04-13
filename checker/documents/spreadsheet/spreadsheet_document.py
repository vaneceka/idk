import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from models.spreadsheet_models import BorderProblem
from utils.text_utils import remove_all_spaces, replace_nbsp


class SpreadsheetDocument(ABC):
    def _load_xml(self, name: str):
        with self._zip.open(name) as f:
            return ET.fromstring(f.read())

    @staticmethod
    def from_path(path: str | Path) -> "SpreadsheetDocument":
        """
        Vytvoří konkrétní implementaci dokumentu podle přípony souboru.

        Args:
            path: Cesta k tabulkovému dokumentu.

        Returns:
            Instance odpovídající implementace SpreadsheetDocument.

        Raises:
            ValueError: Pokud formát souboru není podporovaný.
        """
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix == ".xlsx":
            from documents.spreadsheet.excel_document import ExcelDocument

            return ExcelDocument(str(path))

        if suffix == ".ods":
            from documents.spreadsheet.calc_document import CalcDocument

            return CalcDocument(str(path))

        raise ValueError(f"Nepodporovaný tabulkový formát: {path}")

    def _to_number(self, v):
        """
        Pokusí se převést hodnotu na číslo ve sjednoceném tvaru.

        Args:
            v: Vstupní hodnota.

        Returns:
            Číslo typu float, nebo None pokud převod selže.
        """
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip()
        s = remove_all_spaces(replace_nbsp(s))
        s = s.replace(",", ".")
        try:
            return float(Decimal(s))
        except (InvalidOperation, ValueError):
            return None

    @abstractmethod
    def save_debug_xml(self, out_dir: str | Path = "debug"):
        """
        Uloží interní XML strukturu dokumentu do debug složky.

        Args:
            out_dir: Výstupní složka pro uložení debug souborů.
        """
        ...

    @abstractmethod
    def has_sheet(self, name: str) -> bool:
        """
        Ověří, zda dokument obsahuje list s daným názvem.

        Args:
            name: Název listu.

        Returns:
            True, pokud list existuje, jinak False.
        """
        ...

    @abstractmethod
    def sheet_names(self) -> list[str]:
        """
        Vrátí názvy všech listů v dokumentu.

        Returns:
            Seznam názvů listů.
        """
        ...

    @abstractmethod
    def get_cell(self, ref: str) -> dict | None:
        """
        Vrátí detailní informace o buňce.

        Args:
            ref: Odkaz na buňku ve tvaru sheet!A1.

        Returns:
            Slovník s informacemi o buňce, nebo None pokud buňka neexistuje.
        """
        ...

    @abstractmethod
    def get_cell_style(self, sheet: str, addr: str) -> dict | None:
        """
        Vrátí základní stylové informace o buňce.

        Args:
            sheet: Název listu.
            addr: Adresa buňky.

        Returns:
            Slovník se stylem buňky, nebo None pokud buňka neexistuje.
        """
        ...

    @abstractmethod
    def get_cell_value(self, sheet: str, addr: str):
        """
        Vrátí hodnotu buňky.

        Args:
            sheet: Název listu.
            addr: Adresa buňky.

        Returns:
            Hodnota buňky.
        """
        ...

    @abstractmethod
    def has_formula(self, sheet: str, addr: str) -> bool:
        """
        Zjistí, zda buňka obsahuje vzorec.

        Args:
            sheet: Název listu.
            addr: Adresa buňky.

        Returns:
            True, pokud buňka obsahuje vzorec, jinak False.
        """
        ...

    @abstractmethod
    def iter_cells(self, sheet: str) -> Iterable[str]:
        """
        Iteruje adresy použitých buněk v listu.

        Args:
            sheet: Název listu.

        Returns:
            Iterátor adres buněk.
        """
        ...

    @abstractmethod
    def iter_formulas(self):
        """
        Iteruje všechny vzorce v dokumentu.

        Returns:
            Iterátor záznamů se vzorci.
        """
        ...

    @abstractmethod
    def normalize_formula(self, f: str | None) -> str:
        """
        Normalizuje vzorec do tvaru vhodného pro porovnávání.

        Args:
            f: Původní text vzorce.

        Returns:
            Normalizovaný vzorec.
        """
        ...

    @abstractmethod
    def get_defined_names(self) -> set[str]:
        """
        Vrátí množinu definovaných názvů v dokumentu.

        Returns:
            Množina definovaných názvů.
        """
        ...

    @abstractmethod
    def has_chart(self, sheet: str) -> bool:
        """
        Ověří, zda list obsahuje graf.

        Args:
            sheet: Název listu.

        Returns:
            True, pokud list obsahuje graf, jinak False.
        """
        ...

    @abstractmethod
    def chart_type(self, sheet: str) -> str | None:
        """
        Vrátí typ grafu v listu.

        Args:
            sheet: Název listu.

        Returns:
            Typ grafu, nebo None pokud graf neexistuje.
        """
        ...

    @abstractmethod
    def has_3d_chart(self, sheet: str) -> bool:
        """
        Ověří, zda list obsahuje 3D graf.

        Args:
            sheet: Název listu.

        Returns:
            True, pokud list obsahuje 3D graf, jinak False.
        """
        ...

    @abstractmethod
    def chart_title(self, sheet: str) -> str | None:
        """
        Vrátí titulek grafu.

        Args:
            sheet: Název listu.

        Returns:
            Titulek grafu, nebo None pokud není k dispozici.
        """
        ...

    @abstractmethod
    def chart_x_label(self, sheet: str) -> str | None:
        """
        Vrátí popisek osy X grafu.

        Args:
            sheet: Název listu.

        Returns:
            Popisek osy X, nebo None pokud není k dispozici.
        """
        ...

    @abstractmethod
    def chart_y_label(self, sheet: str) -> str | None:
        """
        Vrátí popisek osy Y grafu.

        Args:
            sheet: Název listu.

        Returns:
            Popisek osy Y, nebo None pokud není k dispozici.
        """
        ...

    @abstractmethod
    def chart_has_data_labels(self, sheet: str) -> bool:
        """
        Ověří, zda graf obsahuje datové popisky.

        Args:
            sheet: Název listu.

        Returns:
            True, pokud graf obsahuje datové popisky, jinak False.
        """
        ...

    @abstractmethod
    def get_array_formula_cells(self) -> list[str]:
        """
        Vrátí buňky nebo oblasti používající array formula.

        Returns:
            Seznam buněk nebo oblastí s array formulí.
        """
        ...

    @abstractmethod
    def get_cell_info(self, sheet: str, addr: str) -> dict | None:
        """
        Vrátí rozšířené informace o buňce.

        Args:
            sheet: Název listu.
            addr: Adresa buňky.

        Returns:
            Slovník s informacemi o buňce, nebo None pokud buňka neexistuje.
        """
        ...

    @abstractmethod
    def cells_with_formulas(self) -> list[dict]:
        """
        Vrátí všechny buňky, které obsahují vzorec.

        Returns:
            Seznam záznamů o buňkách se vzorci.
        """
        ...

    @abstractmethod
    def merged_ranges(self, sheet: str) -> list[tuple[int, int, int, int]]:
        """
        Vrátí sloučené oblasti v listu.

        Args:
            sheet: Název listu.

        Returns:
            Seznam oblastí ve tvaru (min_col, min_row, max_col, max_row).
        """
        ...

    @abstractmethod
    def has_conditional_formatting(self, sheet: str) -> bool:
        """
        Ověří, zda list obsahuje podmíněné formátování.

        Args:
            sheet: Název listu.

        Returns:
            True, pokud list obsahuje podmíněné formátování, jinak False.
        """
        ...

    @abstractmethod
    def check_conditional_formatting(
        self,
        sheet: str,
        expected: dict[str, list[dict]],
    ) -> list[dict]:
        """
        Porovná podmíněné formátování se zadáním.

        Args:
            sheet: Název listu.
            expected: Očekávaná pravidla podmíněného formátování.

        Returns:
            Seznam nalezených problémů.
        """
        ...

    @abstractmethod
    def check_table_borders(
        self,
        sheet: str,
        location: str,
        outer: str,
        inner: str,
    ) -> list[BorderProblem]:
        """
        Zkontroluje ohraničení tabulky v zadané oblasti.

        Args:
            sheet: Název listu.
            location: Oblast tabulky, například A1:F10.
            outer: Očekávaný styl vnějších okrajů.
            inner: Očekávaný styl vnitřních čar.

        Returns:
            Seznam nalezených problémů s ohraničením.
        """
        ...
