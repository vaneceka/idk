from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Iterator

from documents.spreadsheet.spreadsheet_document import SpreadsheetDocument
from models.spreadsheet_models import BorderProblem, CalcStyleInfo
from utils.text_utils import remove_all_spaces
from utils.xml_debug import dump_zip_structure_pretty


class CalcDocument(SpreadsheetDocument):
    NS = {
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "number": "urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0",
        "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
        "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
        "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
        "chart": "urn:oasis:names:tc:opendocument:xmlns:chart:1.0",
        "dr3d": "urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0",
    }

    def __init__(self, path: str):
        self.path = path
        self._zip = zipfile.ZipFile(path)
        self.content = self._load_xml("content.xml")
        self.styles = self._load_xml("styles.xml")

        self.number_styles: dict[str, int] = {}
        self._collect_number_styles(self.content)
        self._collect_number_styles(self.styles)
        self.objects = self._collect_objects()

    def _load_xml(self, name: str) -> ET.Element:
        """
        Načte XML soubor z XLSX archivu.

        Args:
            name: Vnitřní cesta k XML souboru.

        Returns:
            Kořenový XML element.
        """
        with self._zip.open(name) as f:
            return ET.fromstring(f.read())

    def _collect_objects(self) -> dict[str, ET.Element]:
        """
        Načte vložené objekty z ODS archivu.

        Returns:
            Slovník ve tvaru cesta k objektu -> kořenový XML element objektu.
        """
        out: dict[str, ET.Element] = {}

        for name in self._zip.namelist():
            if name.startswith("Object") and name.endswith("content.xml"):
                with self._zip.open(name) as f:
                    out[name] = ET.fromstring(f.read())

        return out

    def _collect_number_styles(self, root: ET.Element | None) -> None:
        """
        Sesbírá informace o číselných stylech a počtu desetinných míst.

        Args:
            root: XML kořen, ve kterém se mají číselné styly hledat.
        """
        if root is None:
            return

        for ns in root.findall(f".//{{{self.NS['number']}}}number-style"):
            name = ns.attrib.get(f"{{{self.NS['style']}}}name")
            if not name:
                continue

            for child in ns.findall(f"{{{self.NS['number']}}}number"):
                dp = child.attrib.get(f"{{{self.NS['number']}}}decimal-places")
                if dp is not None:
                    self.number_styles[name] = int(dp)

    def save_debug_xml(self, out_dir: str | Path = "debug") -> None:
        dump_zip_structure_pretty(self.path, Path(out_dir) / "calc")

    def _iter_sheets(self) -> Iterator[ET.Element]:
        """
        Iteruje všechny listy tabulky v dokumentu.

        Yields:
            XML elementy jednotlivých listů.
        """
        yield from self.content.findall(".//table:table", self.NS)

    def sheet_names(self) -> list[str]:
        names = []
        for sheet in self._iter_sheets():
            name = sheet.attrib.get(f"{{{self.NS['table']}}}name")
            if name:
                names.append(name)
        return names

    def _get_sheet_el(self, sheet_name: str) -> ET.Element | None:
        """
        Vrátí XML element listu podle názvu.

        Args:
            sheet_name: Název listu.

        Returns:
            XML element listu, nebo None pokud list neexistuje.
        """
        for sheet in self._iter_sheets():
            if sheet.attrib.get(f"{{{self.NS['table']}}}name") == sheet_name:
                return sheet
        return None

    def _addr_to_row_col(self, addr: str) -> tuple[int, int]:
        """
        Převede adresu buňky ve formátu A1 na dvojici (řádek, sloupec).

        Args:
            addr: Adresa buňky.

        Returns:
            Dvojice (row, col), obě hodnoty jsou 1-based.

        Raises:
            ValueError: Pokud adresa nemá platný formát.
        """
        m = re.fullmatch(r"([A-Z]+)(\d+)", addr.upper())
        if not m:
            raise ValueError(f"Neplatná adresa buňky: {addr}")

        col_letters, row = m.groups()
        row = int(row)

        col = 0
        for c in col_letters:
            col = col * 26 + (ord(c) - ord("A") + 1)

        return row, col

    def _iter_sheet_rows_with_repeat(
        self, sheet_el: ET.Element
    ) -> Iterator[tuple[int, ET.Element, int]]:
        """
        Iteruje řádky listu včetně informace o opakování řádků.

        Args:
            sheet_el: XML element listu.

        Yields:
            Trojice (start_index, row_element, row_repeat).
        """
        row_idx = 0

        for row in sheet_el.findall("table:table-row", self.NS):
            row_repeat = int(
                row.attrib.get(
                    f"{{{self.NS['table']}}}number-rows-repeated",
                    "1",
                )
            )
            yield row_idx, row, row_repeat
            row_idx += row_repeat

    def _iter_row_cells_with_repeat(
        self, row: ET.Element
    ) -> Iterator[tuple[int, ET.Element, int]]:
        """
        Iteruje buňky řádku včetně informace o opakování sloupců.

        Args:
            row: XML element řádku.

        Yields:
            Trojice (start_index, cell_element, col_repeat).
        """
        col_idx = 0

        for cell in row.findall("table:table-cell", self.NS):
            col_repeat = int(
                cell.attrib.get(
                    f"{{{self.NS['table']}}}number-columns-repeated",
                    "1",
                )
            )
            yield col_idx, cell, col_repeat
            col_idx += col_repeat

    def _find_cell(self, sheet_name: str, addr: str) -> dict | None:
        """
        Najde buňku v listu a vrátí její interní reprezentaci.

        Args:
            sheet_name: Název listu.
            addr: Adresa buňky.

        Returns:
            Slovník s informacemi o buňce, nebo None pokud buňka neexistuje.
        """
        row_target, col_target = self._addr_to_row_col(addr)

        sheet_el = self._get_sheet_el(sheet_name)
        if sheet_el is None:
            return None

        for row_start, row, row_repeat in self._iter_sheet_rows_with_repeat(sheet_el):
            for offset_r in range(row_repeat):
                row_idx = row_start + offset_r + 1
                if row_idx != row_target:
                    continue

                for col_start, cell, col_repeat in self._iter_row_cells_with_repeat(
                    row
                ):
                    for offset_c in range(col_repeat):
                        col_idx = col_start + offset_c + 1
                        if col_idx == col_target:
                            formula = cell.attrib.get(f"{{{self.NS['table']}}}formula")
                            value = cell.attrib.get(f"{{{self.NS['office']}}}value")

                            col_defaults = self._column_default_styles(sheet_el)
                            col_default = (
                                col_defaults[col_target - 1]
                                if col_target - 1 < len(col_defaults)
                                else None
                            )

                            return {
                                "sheet": sheet_name,
                                "address": addr,
                                "formula": formula,
                                "value_cached": value,
                                "raw_cell": cell,
                                "col_default_style": col_default,
                            }

                return None

        return None

    def get_array_formula_cells(self) -> list[str]:
        cells = []

        for sheet in self.content.findall(".//table:table", self.NS):
            sheet_name = sheet.attrib.get(f"{{{self.NS['table']}}}name", "Sheet")

            row_idx = 0
            for row in sheet.findall("table:table-row", self.NS):
                row_idx += 1
                col_idx = 0

                for cell in row.findall("table:table-cell", self.NS):
                    col_idx += 1

                    rows_span = cell.attrib.get(
                        f"{{{self.NS['table']}}}number-matrix-rows-spanned"
                    )
                    cols_span = cell.attrib.get(
                        f"{{{self.NS['table']}}}number-matrix-columns-spanned"
                    )

                    if rows_span or cols_span:
                        col_letter = chr(ord("A") + col_idx - 1)
                        cells.append(f"{sheet_name}!{col_letter}{row_idx}")

        return cells

    def get_cell_info(
        self, sheet: str, addr: str
    ) -> dict[str, bool | str | None] | None:
        cell = self._find_cell(sheet, addr)
        if cell is None:
            return None

        raw = cell["raw_cell"]

        formula = raw.attrib.get(f"{{{self.NS['table']}}}formula")

        value = raw.attrib.get(f"{{{self.NS['office']}}}value")

        if formula and formula.startswith("of:="):
            formula = "=" + formula[4:]

        return {
            "exists": True,
            "formula": formula,
            "value_cached": value,
            "is_error": value is not None and value.startswith("#"),
        }

    def iter_formulas(self) -> Iterator[dict[str, str | None]]:
        for sheet in self.content.findall(".//table:table", self.NS):
            sheet_name = sheet.attrib.get(f"{{{self.NS['table']}}}name")

            for cell in sheet.findall(".//table:table-cell", self.NS):
                formula = cell.attrib.get(f"{{{self.NS['table']}}}formula")
                if formula:
                    formula = formula.replace("of:=", "=")

                    yield {
                        "sheet": sheet_name,
                        "formula": formula,
                    }

    def normalize_formula(self, f: str | None) -> str:
        if not f:
            return ""

        f = f.strip()

        if f.startswith("of:="):
            f = "=" + f[4:]

        # [.E2] -> E2
        f = re.sub(r"\[\.(\w+\$?\d+)\]", r"\1", f)

        # [.C2:.C23] -> C2:C23
        f = re.sub(r"\[\.(\w+):\.(\w+)\]", r"\1:\2", f)

        f = f.replace(";", ",")

        f = re.sub(r'"([^"]+)"', lambda m: f'"{m.group(1).upper()}"', f)

        f = remove_all_spaces(f)

        return f.upper()

    def get_defined_names(self) -> set[str]:
        names = set()

        for ne in self.content.findall(".//table:named-range", self.NS):
            name = ne.attrib.get(f"{{{self.NS['table']}}}name")
            if name:
                names.add(name.upper())

        return names

    def cells_with_formulas(self) -> list[dict[str, str]]:
        out = []

        for sheet in self.content.findall(".//table:table", self.NS):
            sheet_name = sheet.attrib.get(f"{{{self.NS['table']}}}name", "Sheet")

            for row_start, row, _row_repeat in self._iter_sheet_rows_with_repeat(sheet):
                row_idx = row_start + 1

                for col_start, cell, _col_repeat in self._iter_row_cells_with_repeat(
                    row
                ):
                    col_idx = col_start + 1

                    formula = cell.attrib.get(f"{{{self.NS['table']}}}formula")
                    if not formula:
                        continue

                    addr = f"{self._col_to_letters(col_idx)}{row_idx}"
                    out.append(
                        {
                            "sheet": sheet_name,
                            "address": addr,
                            "formula": formula,
                        }
                    )

        return out

    def _col_to_letters(self, col: int) -> str:
        """
        Převede číslo sloupce na písmenové označení.

        Args:
            col: Číslo sloupce, 1-based.

        Returns:
            Označení sloupce, například A nebo AA.
        """
        s = ""
        while col:
            col, r = divmod(col - 1, 26)
            s = chr(65 + r) + s
        return s

    def merged_ranges(self, sheet: str):
        sheet_el = self._get_sheet_el(sheet)
        if sheet_el is None:
            return []

        ranges = []

        for row_start, row, _row_repeat in self._iter_sheet_rows_with_repeat(sheet_el):
            row_idx = row_start + 1

            for col_start, cell, _col_repeat in self._iter_row_cells_with_repeat(row):
                col_idx = col_start + 1

                rows = int(
                    cell.attrib.get(f"{{{self.NS['table']}}}number-rows-spanned", "1")
                )
                cols = int(
                    cell.attrib.get(
                        f"{{{self.NS['table']}}}number-columns-spanned", "1"
                    )
                )

                if rows > 1 or cols > 1:
                    ranges.append(
                        (col_idx, row_idx, col_idx + cols - 1, row_idx + rows - 1)
                    )

        return ranges

    def has_conditional_formatting(self, sheet: str) -> bool:
        return bool(self.content.findall(".//style:map", self.NS))

    def check_conditional_formatting(
        self, sheet: str, expected: dict[str, list[dict]]
    ) -> list[dict]:
        if self._get_sheet_el(sheet) is None:
            return [{"kind": "sheet_missing", "sheet": sheet}]

        problems: list[dict] = []

        op_map = {
            "greaterThan": ">",
            "lessThan": "<",
            "greaterThanOrEqual": ">=",
            "lessThanOrEqual": "<=",
        }

        for cell_addr, rules in expected.items():
            actual = self._ods_cell_cf_rules(sheet, cell_addr)

            for exp in rules:
                operator = exp.get("operator")
                value = exp.get("value")

                if not isinstance(operator, str):
                    problems.append(
                        {
                            "kind": "bad_expected_rule",
                            "cell": cell_addr,
                            "operator": operator,
                            "value": value,
                        }
                    )
                    continue

                want_op = op_map.get(operator)
                want_val = self._to_number(value)

                if want_op is None or want_val is None:
                    problems.append(
                        {
                            "kind": "bad_expected_rule",
                            "cell": cell_addr,
                            "operator": operator,
                            "value": value,
                        }
                    )
                    continue

                ok = any(
                    op == want_op and val is not None and abs(val - want_val) < 0.01
                    for op, val in actual
                )

                if not ok:
                    problems.append(
                        {
                            "kind": "missing_rule",
                            "cell": cell_addr,
                            "operator": operator,
                            "value": value,
                        }
                    )

        return problems

    def _empty_style_info(self) -> CalcStyleInfo:
        """
        Vrátí výchozí prázdnou reprezentaci stylu buňky.

        Returns:
            Styl buňky s výchozími hodnotami.
        """
        return CalcStyleInfo()

    def _find_style(self, style_name: str | None) -> CalcStyleInfo:
        """
        Najde styl podle jména a vrátí jeho rozparsované vlastnosti.

        Args:
            style_name: Název stylu.

        Returns:
            Objekt s vlastnostmi stylu.
        """
        if not style_name:
            return self._empty_style_info()

        style_el = self._find_style_element(style_name)
        if style_el is None:
            return self._empty_style_info()

        borders: dict[str, str] = {}
        bold = False
        align_h: str | None = None
        wrap: bool | None = None

        number_format = style_el.attrib.get(f"{{{self.NS['style']}}}data-style-name")
        decimal_places = (
            self.number_styles.get(number_format) if number_format is not None else None
        )

        for el in style_el.iter():
            if el.tag.endswith("text-properties"):
                if el.attrib.get(f"{{{self.NS['fo']}}}font-weight") == "bold":
                    bold = True

            if el.tag.endswith("paragraph-properties"):
                align_h = el.attrib.get(f"{{{self.NS['fo']}}}text-align")

            if el.tag.endswith("table-cell-properties"):
                general = self._parse_border(
                    el.attrib.get(f"{{{self.NS['fo']}}}border")
                )
                if general:
                    for side in ("top", "bottom", "left", "right"):
                        borders.setdefault(side, general)

                for side in ("top", "bottom", "left", "right"):
                    val = el.attrib.get(f"{{{self.NS['fo']}}}border-{side}")
                    parsed = self._parse_border(val)
                    if parsed:
                        borders[side] = parsed

                wo = el.attrib.get(f"{{{self.NS['fo']}}}wrap-option")
                if wo is not None:
                    wrap = wo != "no-wrap"

        parent = style_el.attrib.get(f"{{{self.NS['style']}}}parent-style-name")
        if parent:
            p = self._find_style(parent)
            for side, val in p.borders.items():
                borders.setdefault(side, val)

            bold = bold or p.bold
            align_h = align_h or p.align_h
            number_format = number_format or p.number_format
            decimal_places = (
                decimal_places if decimal_places is not None else p.decimal_places
            )
            wrap = wrap if wrap is not None else p.wrap

        return CalcStyleInfo(
            borders=borders,
            bold=bold,
            align_h=align_h,
            number_format=number_format,
            decimal_places=decimal_places,
            wrap=wrap,
        )

    def _resolved_cell_style(self, cell_info: dict) -> CalcStyleInfo:
        """
        Vrátí výsledný styl buňky, včetně fallbacku na výchozí styl sloupce.

        Args:
            cell_info: Interní informace o buňce.

        Returns:
            Styl buňky.
        """
        raw = cell_info["raw_cell"]

        style_name = raw.attrib.get(f"{{{self.NS['table']}}}style-name")
        if not style_name:
            style_name = cell_info.get("col_default_style")

        return self._find_style(style_name)

    def get_cell_style(self, sheet: str, addr: str) -> dict | None:
        cell = self._find_cell(sheet, addr)
        if not cell:
            return None

        style = self._resolved_cell_style(cell)

        return {
            "number_format": style.number_format,
            "decimal_places": style.decimal_places,
            "align_h": style.align_h,
            "bold": style.bold,
            "wrap": style.wrap,
        }

    def _parse_border(self, val: str | None) -> str | None:
        """
        Převede textovou reprezentaci ohraničení na interní styl čáry.

        Args:
            val: Textová hodnota atributu border.

        Returns:
            Název stylu čáry, nebo None pokud hodnotu nelze interpretovat.
        """
        if not val or val == "none":
            return None
        m = re.search(r"([\d.]+)pt", val)
        if not m:
            return None
        pt = float(m.group(1))
        if pt >= 2.0:
            return "thick"
        if pt >= 0.7:
            return "thin"
        return None

    def _find_style_element(self, name: str) -> ET.Element | None:
        """
        Najde XML element stylu podle jména.

        Args:
            name: Název stylu.

        Returns:
            XML element stylu, nebo None pokud styl neexistuje.
        """
        style_name_attr = f"{{{self.NS['style']}}}name"
        for s in self.content.iter():
            if s.attrib.get(style_name_attr) == name:
                return s

        if self.styles is not None:
            for s in self.styles.iter():
                if s.attrib.get(style_name_attr) == name:
                    return s

        return None

    def _column_default_styles(self, sheet: ET.Element) -> list[str | None]:
        """
        Vrátí seznam výchozích stylů buněk pro sloupce daného listu.

        Args:
            sheet: XML element listu.

        Returns:
            Seznam názvů stylů po jednotlivých sloupcích.
        """
        defaults = []

        for col in sheet.findall("table:table-column", self.NS):
            rep = int(
                col.attrib.get(f"{{{self.NS['table']}}}number-columns-repeated", "1")
            )
            style = col.attrib.get(f"{{{self.NS['table']}}}default-cell-style-name")
            defaults.extend([style] * rep)

        return defaults

    def iter_cells(self, sheet: str) -> Iterator[str]:
        sheet_el = self._get_sheet_el(sheet)
        if sheet_el is None:
            return

        for row_start, row, row_repeat in self._iter_sheet_rows_with_repeat(sheet_el):
            for offset_r in range(row_repeat):
                row_idx = row_start + offset_r + 1

                for col_start, cell, col_repeat in self._iter_row_cells_with_repeat(
                    row
                ):
                    text = "".join(cell.itertext()).strip()
                    value = cell.attrib.get(f"{{{self.NS['office']}}}value")

                    if not text and value is None:
                        continue

                    for offset_c in range(col_repeat):
                        col_idx = col_start + offset_c + 1
                        yield f"{self._col_to_letters(col_idx)}{row_idx}"

    def get_cell_value(self, sheet: str, addr: str) -> str | None:
        cell = self._find_cell(sheet, addr)
        if cell is None:
            return None

        raw = cell["raw_cell"]

        text = "".join(raw.itertext()).strip()
        if text:
            return text

        return raw.attrib.get(f"{{{self.NS['office']}}}value")

    def has_formula(self, sheet: str, addr: str) -> bool:
        cell = self._find_cell(sheet, addr)
        if not cell:
            return False
        return cell["formula"] is not None

    def _iter_charts(self) -> Iterator[tuple[ET.Element, ET.Element]]:
        """
        Iteruje všechny grafy v hlavním obsahu i ve vložených objektech.

        Yields:
            Dvojice (chart_element, source_root).
        """
        for ch in self.content.findall(".//chart:chart", self.NS):
            yield ch, self.content

        for obj in self.objects.values():
            for ch in obj.findall(".//chart:chart", self.NS):
                yield ch, obj

    def has_chart(self, sheet: str) -> bool:
        return any(True for _ in self._iter_charts())

    def chart_title(self, sheet: str) -> str | None:
        for chart, _root in self._iter_charts():
            p = chart.find(".//chart:title//text:p", self.NS)
            if p is not None:
                return "".join(p.itertext()).strip()
        return None

    def chart_x_label(self, sheet: str) -> str | None:
        for chart, _root in self._iter_charts():
            p = chart.find(
                ".//chart:axis[@chart:dimension='x']//chart:title//text:p", self.NS
            )
            if p is not None:
                return "".join(p.itertext()).strip()
        return None

    def chart_y_label(self, sheet: str) -> str | None:
        for chart, _root in self._iter_charts():
            p = chart.find(
                ".//chart:axis[@chart:dimension='y']//chart:title//text:p", self.NS
            )
            if p is not None:
                return "".join(p.itertext()).strip()
        return None

    def chart_has_data_labels(self, sheet: str) -> bool:
        for chart, root in self._iter_charts():
            for series in chart.findall(".//chart:series", self.NS):
                style_name = series.attrib.get(f"{{{self.NS['chart']}}}style-name")
                if not style_name:
                    continue

                style = root.find(
                    f".//style:style[@style:name='{style_name}']", self.NS
                )
                if style is None:
                    continue

                props = style.find("style:chart-properties", self.NS)
                if props is None:
                    continue

                if (
                    props.attrib.get(f"{{{self.NS['chart']}}}data-label-number")
                    == "value"
                    or props.attrib.get(f"{{{self.NS['chart']}}}display-label")
                    == "true"
                ):
                    return True

        return False

    def chart_type(self, sheet: str) -> str | None:
        for chart, _root in self._iter_charts():
            chart_class = chart.attrib.get(f"{{{self.NS['chart']}}}class")
            if not chart_class:
                continue

            if ":" in chart_class:
                return chart_class.split(":")[1]

            return chart_class

        return None

    def has_3d_chart(self, sheet: str) -> bool:
        for chart, _source in self._iter_charts():
            if chart.attrib.get(f"{{{self.NS['chart']}}}three-dimensional") == "true":
                return True

            for el in chart.iter():
                if el.tag.startswith(f"{{{self.NS['dr3d']}}}"):
                    return True

        return False

    def get_cell(self, ref: str) -> dict | None:
        if "!" not in ref:
            return None

        sheet, addr = ref.split("!", 1)

        info = self.get_cell_info(sheet, addr)
        if not info:
            return None

        return {
            "exists": True,
            "formula": info.get("formula"),
            "value_cached": info.get("value_cached"),
            "is_error": info.get("is_error", False),
        }

    def has_sheet(self, name: str) -> bool:
        return name in self.sheet_names()

    def _ods_cell_cf_rules(self, sheet: str, addr: str) -> list[tuple[str, float]]:
        """
        Vrátí pravidla podmíněného formátování vztahující se k dané buňce.

        Args:
            sheet: Název listu.
            addr: Adresa buňky.

        Returns:
            Seznam dvojic (operátor, hodnota).
        """
        rules = []

        sheet_prefix = sheet + "."

        for cf in self.content.iter():
            if not cf.tag.endswith("conditional-format"):
                continue

            target = None
            for k, v in cf.attrib.items():
                if k.endswith("target-range-address"):
                    target = v
                    break

            if not target or not target.startswith(sheet_prefix):
                continue

            ranges_part = target[len(sheet_prefix) :]

            for rng in ranges_part.split(" "):
                if ":" not in rng:
                    continue

                if not self.cell_in_range(addr, rng):
                    continue

                for cond in cf:
                    if not cond.tag.endswith("condition"):
                        continue

                    val = None
                    for k, v in cond.attrib.items():
                        if k.endswith("value"):
                            val = v
                            break

                    if not val:
                        continue

                    m = re.match(r"\s*([<>]=?)\s*(-?\d+(?:\.\d+)?)", val)
                    if not m:
                        continue

                    op, num = m.groups()
                    rules.append((op, float(num)))

        return rules

    def cell_in_range(self, cell: str, range_: str) -> bool:
        """
        Ověří, zda buňka spadá do zadaného rozsahu.

        Args:
            cell: Adresa buňky.
            range_: Rozsah ve formátu A1:B5.

        Returns:
            True, pokud buňka leží v rozsahu, jinak False.
        """

        def split_addr(a):
            col = "".join(c for c in a if c.isalpha())
            row = int("".join(c for c in a if c.isdigit()))
            return col, row

        start, end = range_.split(":")
        c_col, c_row = split_addr(cell)
        s_col, s_row = split_addr(start)
        e_col, e_row = split_addr(end)

        return s_col <= c_col <= e_col and s_row <= c_row <= e_row

    def _parse_a1_range(self, location: str) -> tuple[int, int, int, int]:
        """
        Převede rozsah ve formátu A1:B5 na číselné hranice.

        Args:
            location: Textový rozsah.

        Returns:
            Čtveřici (min_row, max_row, min_col, max_col).
        """
        start, end = location.split(":", 1)
        r1, c1 = self._addr_to_row_col(start)
        r2, c2 = self._addr_to_row_col(end)
        return min(r1, r2), max(r1, r2), min(c1, c2), max(c1, c2)

    def check_table_borders(
        self,
        sheet: str,
        location: str,
        outer: str,
        inner: str,
    ) -> list[BorderProblem]:
        sheet_el = self._get_sheet_el(sheet)
        if sheet_el is None:
            return [BorderProblem(kind="sheet_missing", sheet=sheet)]

        col_defaults = self._column_default_styles(sheet_el)
        s_row, e_row, s_col_n, e_col_n = self._parse_a1_range(location)

        cell_borders: dict[tuple[int, int], dict[str, str]] = {}

        for row_start, row, row_repeat in self._iter_sheet_rows_with_repeat(sheet_el):
            for offset_r in range(row_repeat):
                row_idx = row_start + offset_r + 1
                if not (s_row <= row_idx <= e_row):
                    continue

                for col_start, cell, col_repeat in self._iter_row_cells_with_repeat(
                    row
                ):
                    for offset_c in range(col_repeat):
                        col_idx = col_start + offset_c + 1
                        if not (s_col_n <= col_idx <= e_col_n):
                            continue

                        col_default_style = (
                            col_defaults[col_idx - 1]
                            if col_idx - 1 < len(col_defaults)
                            else None
                        )

                        cell_info = {
                            "raw_cell": cell,
                            "col_default_style": col_default_style,
                        }

                        style = self._resolved_cell_style(cell_info)
                        cell_borders[(row_idx, col_idx)] = style.borders

        problems: list[BorderProblem] = []

        # horní vnější
        for c in range(s_col_n, e_col_n + 1):
            b = cell_borders.get((s_row, c), {})
            if b.get("top") != outer:
                problems.append(
                    BorderProblem(
                        kind="outer",
                        side="top",
                        cell=f"{self._col_to_letters(c)}{s_row}",
                        expected=outer,
                    )
                )

        # dolní vnější
        for c in range(s_col_n, e_col_n + 1):
            b = cell_borders.get((e_row, c), {})
            if b.get("bottom") != outer:
                problems.append(
                    BorderProblem(
                        kind="outer",
                        side="bottom",
                        cell=f"{self._col_to_letters(c)}{e_row}",
                        expected=outer,
                    )
                )

        # levý vnější
        for r in range(s_row, e_row + 1):
            b = cell_borders.get((r, s_col_n), {})
            if b.get("left") != outer:
                problems.append(
                    BorderProblem(
                        kind="outer",
                        side="left",
                        cell=f"{self._col_to_letters(s_col_n)}{r}",
                        expected=outer,
                    )
                )

        # pravý vnější
        for r in range(s_row, e_row + 1):
            b = cell_borders.get((r, e_col_n), {})
            if b.get("right") != outer:
                problems.append(
                    BorderProblem(
                        kind="outer",
                        side="right",
                        cell=f"{self._col_to_letters(e_col_n)}{r}",
                        expected=outer,
                    )
                )

        # vnitřní vodorovné - mezi řádky r a r+1
        for r in range(s_row, e_row):
            missing = False
            for c in range(s_col_n, e_col_n + 1):
                upper = cell_borders.get((r, c), {})
                lower = cell_borders.get((r + 1, c), {})
                if upper.get("bottom") == inner or lower.get("top") == inner:
                    continue
                missing = True
                break

            if missing:
                problems.append(
                    BorderProblem(
                        kind="inner_h",
                        range=location,
                        expected=inner,
                    )
                )

        # vnitřní svislé - mezi sloupci c a c+1
        for c in range(s_col_n, e_col_n):
            missing = False
            for r in range(s_row, e_row + 1):
                left_cell = cell_borders.get((r, c), {})
                right_cell = cell_borders.get((r, c + 1), {})
                if left_cell.get("right") == inner or right_cell.get("left") == inner:
                    continue
                missing = True
                break

            if missing:
                problems.append(
                    BorderProblem(
                        kind="inner_v",
                        range=location,
                        expected=inner,
                    )
                )

        return problems
