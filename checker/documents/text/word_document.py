import io
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

from assignment.text.text_assignment_model import StyleSpec
from documents.text.text_document import TextDocument
from models.text_models import (
    BibliographySource,
    DocumentObject,
    ObjectCaptionInfo,
    TocIllegalContentError,
)
from utils.text_utils import normalize_spaces
from utils.xml_debug import dump_zip_structure_pretty

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "b": "http://schemas.openxmlformats.org/officeDocument/2006/bibliography",
    "o": "urn:schemas-microsoft-com:office:office",
    "v": "urn:schemas-microsoft-com:vml",
    "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
}


class WordDocument(TextDocument):
    COVER_STYLES = {
        "desky-fakulta": [
            "desky-fakulta",
        ],
        "desky-nazev-prace": [
            "desky-nazev-prace",
        ],
        "desky-rok-a-jmeno": [
            "desky-rok-a-jmeno",
        ],
    }

    LIST_LEVEL_STYLE_NAMES = {
        1: {
            "List",
            "List Number",
            "List Bullet",
            "Číslovaný seznam",
            "Seznam s odrážkami",
            "Seznam",
        },
        2: {
            "List 2",
            "List Number 2",
            "List Bullet 2",
            "Číslovaný seznam 2",
            "Seznam s odrážkami 2",
            "Seznam 2",
        },
    }

    BIB_TYPE_MAP = {
        "book": "book",
        "articleinaperiodical": "article",
        "journalarticle": "article",
        "conferenceproceedings": "article",
        "report": "report",
        "websites": "www",
        "internet site": "www",
    }

    ALLOWED_BIBLIOGRAPHY_TOC_ITEMS = {
        "bibliografie",
        "literatura",
        "references",
        "seznam literatury",
        "seznam použité literatury",
    }

    def __init__(self, path: str):
        self.path = path
        self.NS = NS
        self._zip = zipfile.ZipFile(path)
        self._xml = self._load("word/document.xml")
        self._styles_xml = self._load("word/styles.xml")
        self._sections = self._split_into_sections()
        self._style_by_id, self._style_by_name = self._build_style_maps()
        self._rels = self._build_rels_map()
        self._parent_map = self._build_parent_map()
    
    def _build_parent_map(self) -> dict[ET.Element, ET.Element]:
        """
        Vytvoří mapu potomků na jejich rodičovské elementy.

        Returns:
            Slovník, kde klíčem je XML element a hodnotou jeho přímý rodič.
        """
        return {
            child: parent for parent in self._xml.iter() for child in parent
        }

    def _find_style_by_id(self, style_id: str | None) -> ET.Element | None:
        """
        Najde XML element stylu podle interního identifikátoru.

        Args:
            style_id: Interní identifikátor stylu.

        Returns:
            XML element stylu, nebo None pokud styl neexistuje.
        """
        if not style_id:
            return None
        return self._style_by_id.get(style_id)

    def _parent_of(self, el: ET.Element) -> ET.Element | None:
        """
        Vrátí rodičovský XML element pro zadaný prvek.

        Args:
            el: XML element, jehož rodič se má zjistit.

        Returns:
            Rodičovský element, nebo None pokud není známý.
        """
        return getattr(self, "_parent_map", {}).get(el)

    def _build_rels_map(self) -> dict[str, str]:
        """
        Načte mapování relationship ID na cílové části dokumentu.

        Returns:
            Slovník ve tvaru rId -> target path.
        """
        try:
            rels = self._load("word/_rels/document.xml.rels")
        except KeyError:
            return {}

        out: dict[str, str] = {}
        for rel in rels.findall(".//rel:Relationship", self.NS):
            rid = rel.attrib.get("Id")
            target = rel.attrib.get("Target")
            if rid and target:
                out[rid] = target
        return out

    def _rel_target_path(self, r_id: str) -> str | None:
        """
        Přeloží relationship ID na úplnou interní cestu v DOCX archivu.

        Args:
            r_id: Identifikátor relace.

        Returns:
            Cesta k cílové části dokumentu, nebo None pokud relace neexistuje.
        """
        target = self._rels.get(r_id)
        if not target:
            return None
        return target if target.startswith("word/") else f"word/{target}"

    def _build_style_maps(self) -> tuple[dict[str, ET.Element], dict[str, ET.Element]]:
        """
        Vytvoří mapy stylů podle styleId a podle názvu stylu.

        Returns:
            Dvojici slovníků:
            - styleId -> XML element stylu
            - název stylu -> XML element stylu
        """
        by_id: dict[str, ET.Element] = {}
        by_name: dict[str, ET.Element] = {}

        for s in self._styles_xml.findall(".//w:style", self.NS):
            sid = s.attrib.get(f"{{{self.NS['w']}}}styleId")
            if sid:
                by_id[sid] = s
                by_name[sid.strip()] = s

            name_el = s.find("w:name", self.NS)
            name = (
                name_el.attrib.get(f"{{{self.NS['w']}}}val")
                if name_el is not None
                else None
            )
            if name:
                by_name[name.strip()] = s

        return by_id, by_name

    def save_debug_xml(self, out_dir: str | Path = "debug") -> None:
        dump_zip_structure_pretty(self.path, Path(out_dir) / "word")

    def _load(self, name: str) -> ET.Element:
        """
        Načte XML soubor z DOCX archivu.

        Args:
            name: Vnitřní cesta k XML souboru v archivu.

        Returns:
            Kořenový XML element načteného souboru.
        """
        with self._zip.open(name) as f:
            return ET.fromstring(f.read())

    def _paragraph_is_in_textbox_or_object(self, p: ET.Element) -> bool:
        """
        Ověří, zda odstavec leží uvnitř textového pole nebo kresleného objektu.

        Args:
            p: XML element odstavce.

        Returns:
            True pokud je odstavec uvnitř textboxu nebo objektu, jinak False.
        """
        cur = p

        while True:
            parent = self._parent_of(cur)
            if parent is None:
                return False

            tag = parent.tag.split("}")[-1]

            if tag in {
                "txbxContent",
                "textbox",
                "shape",
                "group",
                "pict",
                "drawing",
                "AlternateContent",
                "Fallback",
            }:
                return True

            cur = parent

    def iter_paragraphs(self) -> Iterable[ET.Element]:
        for p in self._xml.findall(".//w:p", self.NS):
            if self._paragraph_is_in_textbox_or_object(p):
                continue
            yield p

    def _iter_blocks_in_order(self, parent: ET.Element):
        """
        Prochází bloky dokumentu v pořadí čtení včetně zanořených struktur.
        """
        for el in parent:
            tag = el.tag

            yield el

            if tag.endswith("}sdt"):
                sdt_content = el.find("w:sdtContent", self.NS)
                if sdt_content is not None:
                    yield from self._iter_blocks_in_order(sdt_content)

            elif tag.endswith("}tbl"):
                for tr in el.findall("w:tr", self.NS):
                    for tc in tr.findall("w:tc", self.NS):
                        yield from self._iter_blocks_in_order(tc)

    def _split_into_sections(self) -> list[list[ET.Element]]:
        """
        Rozdělí obsah dokumentu na oddíly podle elementů sectPr.

        Returns:
            Seznam oddílů, kde každý oddíl obsahuje své XML bloky.
        """
        sections: list[list[ET.Element]] = []
        current: list[ET.Element] = []

        body = self._xml.find("w:body", self.NS)
        if body is None:
            return []

        for el in self._iter_blocks_in_order(body):
            current.append(el)

            if el.tag.endswith("}sectPr"):
                sections.append(current)
                current = []
                continue

            if el.tag.endswith("}p"):
                ppr = el.find("w:pPr", self.NS)
                if ppr is not None and ppr.find("w:sectPr", self.NS) is not None:
                    sections.append(current)
                    current = []

        if current:
            sections.append(current)

        return sections

    def section_count(self) -> int:
        return len(self._sections)

    def _section(self, index: int) -> list[ET.Element]:
        """
        Vrátí XML bloky patřící do zadaného oddílu.

        Args:
            index: Index oddílu.

        Returns:
            Seznam XML elementů oddílu, nebo prázdný seznam pokud index neexistuje.
        """
        if index < 0 or index >= len(self._sections):
            return []
        return self._sections[index]

    def has_toc_in_section(self, section_index: int) -> bool:
        for instr in self._get_field_instructions(self._section(section_index)):
            if instr.startswith("TOC") and "\\o" in instr:
                return True
        return False

    def has_text_in_section(self, section_index: int, min_words: int = 1) -> bool:
        parts: list[str] = []

        for el in self._section(section_index):
            parts.extend(self._iter_text_nodes(el))

        full_text = " ".join(parts).strip()
        if not full_text:
            return False

        words = re.findall(r"\b[\w]+(?:[-'][\w]+)?\b", full_text, flags=re.UNICODE)
        return len(words) >= min_words

    def _is_bibliography_sdt(self, sdt: ET.Element) -> bool:
        """
        Ověří, zda content control odpovídá bibliografii.

        Args:
            sdt: XML element content controlu.

        Returns:
            True pokud jde o bibliografii, jinak False.
        """
        sdt_pr = sdt.find("w:sdtPr", self.NS)
        if sdt_pr is None:
            return False

        if sdt_pr.find("w:bibliography", self.NS) is not None:
            return True

        alias_el = sdt_pr.find("w:alias", self.NS)
        tag_el = sdt_pr.find("w:tag", self.NS)

        alias_val = (
            alias_el.attrib.get(f"{{{self.NS['w']}}}val", "")
            if alias_el is not None
            else ""
        )
        tag_val = (
            tag_el.attrib.get(f"{{{self.NS['w']}}}val", "")
            if tag_el is not None
            else ""
        )

        alias_val = alias_val.lower()
        tag_val = tag_val.lower()

        if "citace pro" in alias_val and "bibliografi" in alias_val:
            return True

        if tag_val.startswith("citpro#b#"):
            return True

        return False

    def has_bibliography_in_section(self, section_index: int) -> bool:
        for el in self._section(section_index):
            for sdt in el.findall(".//w:sdt", self.NS):
                if self._is_bibliography_sdt(sdt):
                    return True
        return False

    def _get_field_instructions(self, section: list[ET.Element]) -> list[str]:
        """
        Vrátí instrukce polí nalezené v zadaném oddílu.

        Args:
            section: Seznam XML bloků oddílu.

        Returns:
            Seznam textových instrukcí polí.
        """
        instrs = []

        for el in section:
            el_instructions = self._extract_instructions_from_element(el)
            instrs.extend(el_instructions)

        return instrs

    def _has_list_in_section(self, section_index: int, keywords: list[str]) -> bool:
        """
        Ověří, zda oddíl obsahuje generovaný seznam objektů podle zadaných klíčových slov.

        Args:
            section_index: Index oddílu.
            keywords: Klíčová slova hledaná v instrukci pole TOC.

        Returns:
            True pokud oddíl obsahuje odpovídající seznam, jinak False.
        """
        section = self._section(section_index)

        for instr in self._get_field_instructions(section):
            instr_u = instr.upper()

            if not instr_u.startswith("TOC"):
                continue

            if "\\C" not in instr_u and "\\T" not in instr_u:
                continue

            if any(keyword.upper() in instr_u for keyword in keywords):
                return True

        return False

    def has_list_of_figures_in_section(self, section_index: int) -> bool:
        return self._has_list_in_section(section_index, ["obrázek", "figure"])

    def has_list_of_tables_in_section(self, section_index: int) -> bool:
        return self._has_list_in_section(section_index, ["tabulka", "table"])

    def _normalize_font(self, font: str | None) -> str | None:
        """
        Normalizuje název fontu odstraněním doplňkových částí názvu.

        Args:
            font: Původní název fontu.

        Returns:
            Normalizovaný název fontu, nebo None.
        """
        if not font:
            return None
        font = re.sub(r"\s*\(.*$", "", font)
        return font.strip()

    def _iter_style_chain(
        self, style: ET.Element | None, *, follow_link: bool = True
    ) -> Iterator[ET.Element]:
        """
        Iteruje styl a jeho nadřazené styly včetně případně linked stylu.

        Args:
            style: Výchozí styl.
            follow_link: Určuje, zda se má zohlednit i linked styl.

        Yields:
            XML elementy stylů v pořadí dědičnosti.
        """
        visited: set[int] = set()

        while style is not None and id(style) not in visited:
            visited.add(id(style))
            yield style

            if follow_link:
                linked = self._get_linked_style(style)
                if linked is not None and id(linked) not in visited:
                    style = linked
                    continue

            based = style.find("w:basedOn", self.NS)
            based_id = (
                based.attrib.get(f"{{{self.NS['w']}}}val")
                if based is not None
                else None
            )
            style = self._find_style_by_id(based_id.strip()) if based_id else None

    def _get_style_attr(
        self,
        style: ET.Element | None,
        path: str,
        attr: str,
        *,
        follow_link: bool,
        cast: Callable[[str], Any] | None = None,
        transform: Callable[[str], str] | None = None,
    ) -> Any | None:
        """
        Najde atribut ve stylu nebo v jeho předcích.

        Args:
            style: Výchozí styl.
            path: XPath cesta k hledanému elementu.
            attr: Název atributu.
            follow_link: Určuje, zda se má sledovat i linked styl.
            cast: Volitelná funkce pro převod hodnoty.
            transform: Volitelná funkce pro úpravu textové hodnoty.

        Returns:
            Hodnota atributu, nebo None pokud není nalezena.
        """
        for st in self._iter_style_chain(style, follow_link=follow_link):
            el = st.find(path, self.NS)
            if el is None:
                continue
            val = el.attrib.get(attr)
            if val is None or val == "":
                continue
            if transform:
                val = transform(val)
            if cast:
                val = cast(val)
            return val
        return None

    def _resolve_font(self, style: ET.Element | None) -> str | None:
        """
        Zjistí výsledný font stylu.

        Args:
            style: XML element stylu.

        Returns:
            Název fontu, nebo None pokud jej nelze určit.
        """
        for st in self._iter_style_chain(style, follow_link=False):
            rpr = st.find("w:rPr", self.NS)
            if rpr is None:
                continue

            fonts = rpr.find("w:rFonts", self.NS)
            if fonts is None:
                continue

            font = (
                fonts.attrib.get(f"{{{self.NS['w']}}}ascii")
                or fonts.attrib.get(f"{{{self.NS['w']}}}hAnsi")
                or fonts.attrib.get(f"{{{self.NS['w']}}}cs")
            )
            if font:
                return self._normalize_font(font)

        return None

    def _resolve_alignment(self, style: ET.Element | None) -> str | None:
        """
        Zjistí výsledné zarovnání odstavce pro styl.

        Args:
            style: XML element stylu.

        Returns:
            Hodnota zarovnání, nebo None.
        """
        return self._get_style_attr(
            style, "w:pPr/w:jc", f"{{{self.NS['w']}}}val", follow_link=False
        )

    def _resolve_space_before(self, style: ET.Element | None) -> int | None:
        """
        Zjistí spacing before pro styl.

        Args:
            style: XML element stylu.

        Returns:
            Hodnota odsazení před odstavcem, nebo None.
        """
        return self._get_style_attr(
            style,
            "w:pPr/w:spacing",
            f"{{{self.NS['w']}}}before",
            follow_link=False,
            cast=int,
        )

    def _resolve_color(self, style: ET.Element | None) -> str | None:
        """
        Zjistí výslednou barvu textu pro styl.

        Args:
            style: XML element stylu.

        Returns:
            Barva ve formátu hex, nebo None.
        """
        val = self._get_style_attr(
            style,
            "w:rPr/w:color",
            f"{{{self.NS['w']}}}val",
            follow_link=True,
            transform=lambda x: x.upper(),
        )

        if val is None or val == "AUTO":
            return "000000"

        return val

    def _resolve_size(self, style: ET.Element | None) -> float | None:
        """
        Zjistí výslednou velikost písma stylu.

        Args:
            style: XML element stylu.

        Returns:
            Velikost písma v bodech, nebo None.
        """
        val = self._get_style_attr(
            style, "w:rPr/w:sz", f"{{{self.NS['w']}}}val", follow_link=False, cast=int
        )
        if val is not None:
            return val / 2.0

        fallback = self.get_doc_default_font_size()
        return float(fallback) if fallback is not None else None

    def _resolve_page_break_before(self, style: ET.Element | None) -> bool:
        """
        Ověří, zda styl vynucuje zalomení stránky před odstavcem.

        Args:
            style: XML element stylu.

        Returns:
            True pokud styl obsahuje pageBreakBefore, jinak False.
        """
        for st in self._iter_style_chain(style, follow_link=True):
            if st.find("w:pPr/w:pageBreakBefore", self.NS) is not None:
                return True
        return False

    def _resolve_tabs(self, style: ET.Element | None) -> list[tuple[str, int]] | None:
        """
        Vrátí definované tabulátory stylu.

        Args:
            style: XML element stylu.

        Returns:
            Seznam dvojic (typ, pozice), nebo None pokud styl tabulátory nemá.
        """
        for st in self._iter_style_chain(style, follow_link=False):
            tabs_el = st.find("w:pPr/w:tabs", self.NS)
            if tabs_el is None:
                continue

            out: list[tuple[str, int]] = []
            for tab in tabs_el.findall("w:tab", self.NS):
                val = tab.attrib.get(f"{{{self.NS['w']}}}val")
                pos = tab.attrib.get(f"{{{self.NS['w']}}}pos")
                if val and pos:
                    out.append((val, int(pos)))

            if out:
                return out

        return None

    def _resolve_line_height(self, style: ET.Element | None) -> float | None:
        """
        Zjistí výslednou výšku řádku pro styl.

        Args:
            style: XML element stylu.

        Returns:
            Výška řádku jako násobek základní výšky, nebo None.
        """
        for st in self._iter_style_chain(style, follow_link=False):
            spacing = st.find("w:pPr/w:spacing", self.NS)
            if spacing is None:
                continue

            line = spacing.attrib.get(f"{{{self.NS['w']}}}line")
            rule = (spacing.attrib.get(f"{{{self.NS['w']}}}lineRule") or "auto").lower()

            if not line:
                continue

            if rule == "auto":
                try:
                    return int(line) / 240.0
                except (ValueError, TypeError):
                    continue
            continue

        dd = self._styles_xml.find(
            ".//w:docDefaults/w:pPrDefault/w:pPr/w:spacing", self.NS
        )
        if dd is None:
            return None

        line = dd.attrib.get(f"{{{self.NS['w']}}}line")
        rule = (dd.attrib.get(f"{{{self.NS['w']}}}lineRule") or "auto").lower()

        if not line:
            return None

        if rule == "auto":
            try:
                return int(line) / 240.0
            except (ValueError, TypeError):
                return None

        return None

    def get_doc_default_font_size(self) -> int | None:
        dd = self._styles_xml.find(".//w:docDefaults/w:rPrDefault/w:rPr", self.NS)
        if dd is None:
            return None
        sz = dd.find("w:sz", self.NS)
        if sz is None:
            return None
        return int(sz.attrib[f"{{{self.NS['w']}}}val"]) // 2

    def _resolve_bool(self, style: ET.Element | None, tag: str) -> bool | None:
        """
        Zjistí logickou vlastnost stylu podle zadaného tagu.

        Args:
            style: XML element stylu.
            tag: Název tagu ve w:rPr.

        Returns:
            True nebo False podle hodnoty vlastnosti, nebo None pokud není definována.
        """
        for st in self._iter_style_chain(style, follow_link=True):
            el = st.find(f"w:rPr/w:{tag}", self.NS)
            if el is None:
                continue

            val = el.attrib.get(f"{{{self.NS['w']}}}val")
            return val not in ("0", "false", "False", "none")

        return None

    def _get_linked_style(self, style: ET.Element | None) -> ET.Element | None:
        """
        Vrátí linked styl navázaný na zadaný styl.

        Args:
            style: XML element stylu.

        Returns:
            XML element linked stylu, nebo None.
        """
        if style is None:
            return None
        link = style.find("w:link", self.NS)
        if link is None:
            return None
        return self._find_style_by_id(link.attrib.get(f"{{{self.NS['w']}}}val"))

    def _extract_numbering_info(
        self, style: ET.Element
    ) -> tuple[bool | None, int | None]:
        """
        Zjistí, zda styl obsahuje číslování, a případně vrátí jeho úroveň.

        Args:
            style: XML element stylu.

        Returns:
            Dvojici:
            - True a úroveň číslování, pokud je číslování ve stylu aktivní,
            - (None, None), pokud styl číslování nemá nebo jej nelze určit.
        """
        ppr = style.find("w:pPr", self.NS)
        if ppr is None:
            return None, None

        numpr = ppr.find("w:numPr", self.NS)
        if numpr is None:
            return None, None

        num_id = numpr.find("w:numId", self.NS)
        if num_id is None:
            return None, None

        num_id_val = num_id.attrib.get(f"{{{self.NS['w']}}}val")
        if num_id_val is None:
            return None, None

        try:
            val = int(num_id_val)
        except ValueError:
            return None, None

        if val <= 0:
            return None, None

        ilvl = numpr.find("w:ilvl", self.NS)
        if ilvl is None:
            return True, 0

        ilvl_val = ilvl.attrib.get(f"{{{self.NS['w']}}}val")
        if ilvl_val is None:
            return True, 0

        try:
            num_level = int(ilvl_val)
        except ValueError:
            return True, 0

        return True, num_level

    def _build_style_spec(
        self,
        style: ET.Element,
        *,
        default_alignment: str | None = None,
    ) -> StyleSpec:
        """
        Sestaví objekt StyleSpec z XML reprezentace stylu.

        Args:
            style: XML element stylu.
            default_alignment: Výchozí zarovnání použité při absenci explicitní hodnoty.

        Returns:
            Styl převedený do struktury StyleSpec.
        """
        font = self._resolve_font(style)
        color = self._resolve_color(style)
        size = self._resolve_size(style)
        bold = self._resolve_bool(style, "b")
        italic = self._resolve_bool(style, "i")
        all_caps = self._resolve_bool(style, "caps")
        alignment = self._resolve_alignment(style) or default_alignment
        line_height = self._resolve_line_height(style)
        page_break = self._resolve_page_break_before(style)
        before = self._resolve_space_before(style)
        tabs = self._resolve_tabs(style)

        is_numbered, num_level = self._extract_numbering_info(style)

        ppr = style.find("w:pPr", self.NS)
        if ppr is not None:
            jc = ppr.find("w:jc", self.NS)
            if jc is not None:
                alignment = jc.attrib.get(f"{{{self.NS['w']}}}val") or alignment

        based_el = style.find("w:basedOn", self.NS)
        based_on = (
            based_el.attrib.get(f"{{{self.NS['w']}}}val")
            if based_el is not None
            else None
        )

        name_el = style.find("w:name", self.NS)
        name = (
            str(name_el.attrib.get(f"{{{self.NS['w']}}}val") or "")
            if name_el is not None
            else ""
        )

        return StyleSpec(
            name=name,
            font=font,
            size=size,
            bold=bold,
            italic=italic,
            allCaps=all_caps,
            color=color,
            alignment=alignment,
            lineHeight=line_height,
            pageBreakBefore=page_break,
            isNumbered=is_numbered,
            numLevel=num_level,
            basedOn=based_on,
            spaceBefore=before,
            tabs=tabs,
        )

    def _find_style(self, *, name: str | None = None) -> ET.Element | None:
        """
        Najde styl podle názvu.

        Args:
            name: Název stylu.

        Returns:
            XML element stylu, nebo None pokud styl neexistuje.
        """
        if not name:
            return None
        return self._style_by_name.get(name.strip())

    def get_normal_style(self) -> StyleSpec | None:
        return self.get_style_by_any_name(["Normal"], default_alignment="both")

    def _style_heading_level_inherited(self, style: ET.Element | None) -> int | None:
        """
        Zjistí úroveň nadpisu definovanou stylem nebo jeho předky.

        Args:
            style: XML element stylu.

        Returns:
            Úroveň nadpisu, nebo None pokud ji nelze určit.
        """
        for st in self._iter_style_chain(style, follow_link=False):
            ppr = st.find("w:pPr", self.NS)
            if ppr is None:
                continue

            out = ppr.find("w:outlineLvl", self.NS)
            if out is None:
                continue

            val_s = out.attrib.get(f"{{{self.NS['w']}}}val")
            if val_s and val_s.isdigit():
                return int(val_s) + 1

        return None

    def _style_heading_level_direct(self, style: ET.Element | None) -> int | None:
        """
        Zjistí úroveň nadpisu definovanou přímo stylem.

        Args:
            style: XML element stylu.

        Returns:
            Úroveň nadpisu, nebo None pokud ji styl přímo nedefinuje.
        """
        if style is None:
            return None

        ppr = style.find("w:pPr", self.NS)
        if ppr is None:
            return None

        out = ppr.find("w:outlineLvl", self.NS)
        if out is None:
            return None

        val_s = out.attrib.get(f"{{{self.NS['w']}}}val")
        if val_s and val_s.isdigit():
            return int(val_s) + 1

        return None

    def _find_heading_styles_by_outline_level(self, level: int) -> list[ET.Element]:
        """
        Najde všechny styly nadpisů odpovídající zadané outline úrovni.

        Args:
            level: Hledaná úroveň nadpisu.

        Returns:
            Seznam XML stylů odpovídajících úrovni.
        """
        out: list[ET.Element] = []

        for s in self._styles_xml.findall(".//w:style", self.NS):
            style_type = s.attrib.get(f"{{{self.NS['w']}}}type")
            if style_type != "paragraph":
                continue

            if self._style_heading_level_inherited(s) == level:
                out.append(s)

        return out

    def _find_used_heading_styles_by_outline_level(
        self, level: int
    ) -> list[ET.Element]:
        """
        Najde skutečně použité styly nadpisů pro zadanou úroveň.

        Args:
            level: Hledaná úroveň nadpisu.

        Returns:
            Seznam použitých XML stylů odpovídajících úrovni.
        """
        out: list[ET.Element] = []
        seen_ids: set[str] = set()

        for p in self._xml.findall(".//w:body//w:p", self.NS):
            p_style = p.find("w:pPr/w:pStyle", self.NS)
            if p_style is None:
                continue

            style_id = p_style.attrib.get(f"{{{self.NS['w']}}}val")
            if not style_id or style_id in seen_ids:
                continue

            style = self._find_style_by_id(style_id)
            if style is None:
                continue

            style_type = style.attrib.get(f"{{{self.NS['w']}}}type")
            if style_type != "paragraph":
                continue

            if self._style_heading_level_inherited(style) == level:
                out.append(style)
                seen_ids.add(style_id)

        return out

    def get_heading_styles(self, level: int) -> list[StyleSpec]:
        styles = self._find_used_heading_styles_by_outline_level(level)

        if not styles:
            styles = self._find_heading_styles_by_outline_level(level)

        return [
            self._build_style_spec(style, default_alignment="start") for style in styles
        ]

    def get_custom_style(self, style_name: str) -> StyleSpec | None:
        return self.get_style_by_any_name([style_name])

    def get_style_by_any_name(
        self, names: list[str], *, default_alignment: str | None = None
    ) -> StyleSpec | None:
        for n in names:
            style = self._find_style(name=n)
            if style is not None:
                return self._build_style_spec(
                    style, default_alignment=default_alignment
                )
        return None

    def _iter_text_nodes(self, element: ET.Element) -> list[str]:
        """
        Vrátí textové uzly obsažené v zadaném elementu.

        Args:
            element: XML element.

        Returns:
            Seznam textových částí nalezených v potomcích w:t.
        """
        parts: list[str] = []
        for t in element.findall(".//w:t", self.NS):
            if t.text:
                parts.append(t.text)
        return parts

    def paragraph_text(self, p: ET.Element) -> str:
        txt = "".join(self._iter_text_nodes(p))
        return normalize_spaces(txt)
    
    def paragraph_style_id(self, p: ET.Element) -> str | None:
        ppr = p.find("w:pPr", self.NS)
        if ppr is None:
            return None
        ps = ppr.find("w:pStyle", self.NS)
        if ps is None:
            return None
        return ps.attrib.get(f"{{{self.NS['w']}}}val")

    def _style_level_from_styles_xml(self, style_id: str) -> int | None:
        """
        Zjistí úroveň nadpisu podle styleId.

        Args:
            style_id: Identifikátor stylu.

        Returns:
            Úroveň nadpisu, nebo None pokud ji nelze určit.
        """
        style = self._find_style_by_id(style_id)
        if style is None:
            return None
        return self._style_heading_level_inherited(style)

    def _heading_text(self, p: ET.Element) -> str:
        """
        Vrátí text nadpisu bez textů z vnořených objektů.

        Args:
            p: XML element odstavce.

        Returns:
            Text nadpisu bez textů z textboxů a dalších objektů.
        """
        parts = []

        for child in p:
            tag = child.tag.split("}")[-1]

            if tag == "r":
                for t in child.findall("w:t", self.NS):
                    if t.text:
                        parts.append(t.text)

            elif tag == "hyperlink":
                for r in child.findall("w:r", self.NS):
                    for t in r.findall("w:t", self.NS):
                        if t.text:
                            parts.append(t.text)

        return normalize_spaces("".join(parts))

    def iter_headings(self) -> list[tuple[str, int]]:
        items: list[tuple[str, int]] = []

        for p in self._xml.findall(".//w:body/w:p", self.NS):
            sid = self.paragraph_style_id(p)
            if not sid:
                continue

            lvl = self._style_level_from_styles_xml(sid)
            if lvl is None:
                continue

            txt = self._heading_text(p)
            if not txt:
                continue

            items.append((txt, lvl))

        return items

    def _is_bibliography_paragraph(self, p: ET.Element) -> bool:
        """
        Ověří, zda odstavec patří do seznamu literatury.

        Args:
            p: XML element odstavce.

        Returns:
            True pokud jde o bibliografický odstavec, jinak False.
        """
        ppr = p.find("w:pPr", self.NS)
        if ppr is None:
            return False

        ps = ppr.find("w:pStyle", self.NS)
        if ps is None:
            return False

        style = (ps.attrib.get(f"{{{self.NS['w']}}}val", "") or "").strip().lower()
        return style in ("bibliografie", "bibliography")

    def _iter_artifact_candidates(self) -> Iterator[tuple[int, ET.Element, str]]:
        """
        Iteruje odstavce vhodné pro kontrolu artefaktů v textu.

        Yields:
            Trojice obsahující pořadí odstavce, element odstavce a jeho text.
        """
        for i, p in enumerate(self._xml.findall(".//w:body/w:p", self.NS), start=1):
            if self._paragraph_is_toc_or_object_list(p):
                continue

            if self._is_bibliography_paragraph(p):
                continue

            text = self.paragraph_text(p)
            if text and text.strip():
                yield i, p, text.strip()

    def find_html_artifacts(self) -> list[tuple[int, str]]:
        results = []
        ENTITY_RE = re.compile(
            r"&(?:nbsp|amp|lt|gt|quot|apos);|&#\d+;|&#x[0-9a-fA-F]+;"
        )
        TAG_RE = re.compile(r"<\s*/?\s*[a-zA-Z][a-zA-Z0-9:_-]*(\s+[^<>]*)?>")

        for i, p, t in self._iter_artifact_candidates():
            if ENTITY_RE.search(t) or TAG_RE.search(t):
                results.append((i, t))
        return results

    def find_txt_artifacts(self) -> list[tuple[int, str]]:
        results = []

        ASCII_BULLETS_RE = re.compile(r"^\s*(?:[\*\-•]|[0-9]+\)|[0-9]+\.)\s+")
        WEIRD_SPACING_RE = re.compile(r"(?: {3,}|\t+)")
        ASCII_SEPARATORS_RE = re.compile(r"^\s*(?:={4,}|-{4,}|_{4,}|\*{4,})\s*$")

        for i, p, t in self._iter_artifact_candidates():
            text = t.strip()
            if not text:
                continue

            has_real_list = p.find(".//w:numPr", self.NS) is not None

            if WEIRD_SPACING_RE.search(text):
                results.append((i, text))
                continue

            if ASCII_SEPARATORS_RE.match(text):
                results.append((i, text))
                continue

            if (not has_real_list) and ASCII_BULLETS_RE.match(text):
                results.append((i, text))
                continue

        return results

    def _is_probably_list(self, p_el: ET.Element, s: str) -> bool:
        """
        Odhadne, zda text odpovídá seznamové položce.

        Args:
            p_el: XML element odstavce.
            s: Text odstavce.

        Returns:
            True pokud text pravděpodobně představuje seznam, jinak False.
        """
        bullet_like_re = re.compile(
            r"^\s*(?:[-•*]|[0-9]+[.)]|[a-zA-Z][.)]|[ivxlcdmIVXLCDM]+[.)])\s+"
        )

        if bullet_like_re.match(s):
            return True

        ppr = p_el.find("w:pPr", self.NS)
        if ppr is not None and ppr.find("w:numPr", self.NS) is not None:
            return True

        if p_el.find(".//w:numPr", self.NS) is not None:
            return True

        style = (self.paragraph_style_name(p_el) or "").lower()
        if any(
            key in style
            for key in (
                "list",
                "seznam",
                "odráž",
                "odraz",
                "bullet",
                "number",
                "čísl",
                "cisl",
            )
        ):
            return True

        return False
    
    def _looks_like_hard_wrapped_line(self, s: str) -> bool:
        """
        Odhadne, zda text vypadá jako tvrdě zalomený řádek převzatý z PDF.

        Args:
            s: Text řádku.

        Returns:
            True pokud text odpovídá tvrdému zalomení, jinak False.
        """
        if not s:
            return False
        if len(s) > 55:
            return False
        if s.endswith((".", "!", "?", ":", ";")):
            return False
        stripped = s.lstrip()
        if stripped and stripped[0].islower():
            return True
        if "," in s and len(s) >= 25:
            return True
        return False

    def _flush_run(
        self,
        results: list[tuple[int, str]],
        run: list[tuple[int, str]],
        threshold: int,
    ) -> None:
        """
        Přidá běh kandidátů do výsledků, pokud překročí daný práh.

        Args:
            results: Cílový seznam výsledků.
            run: Aktuální běh kandidátních řádků.
            threshold: Minimální délka běhu pro zařazení do výsledků.
        """
        if len(run) >= threshold:
            results.append(run[0])
            if len(run) > 1:
                results.append(run[1])
        run.clear()

    def find_pdf_artifacts(self) -> list[tuple[int, str]]:
        RUN_THRESHOLD = 6
        results = []
        paragraphs = list(self._xml.findall(".//w:body/w:p", self.NS))
        HYPHEN_END_RE = re.compile(r"[A-Za-zÁ-ž]\-$")
        texts = []

        for i, p in enumerate(paragraphs, start=1):
            if self._paragraph_is_toc_or_object_list(p):
                texts.append((i, "", True, p))
                continue

            t = (self.paragraph_text(p) or "").strip()

            if not t:
                texts.append((i, "", True, p))
                continue

            if p.find(".//w:br[@w:type='page']", self.NS) is not None:
                texts.append((i, "", True, p))
                continue

            if p.find(".//w:lastRenderedPageBreak", self.NS) is not None and len(t) < 10:
                texts.append((i, "", True, p))
                continue

            style = (self.paragraph_style_name(p) or "").lower()
            if any(k in style for k in ("caption", "titulek", "popis")):
                texts.append((i, "", True, p))
                continue

            if re.match(
                r"^\s*(obrázek|graf|tabulka|figure|chart|table)\s+\d+",
                t,
                re.IGNORECASE,
            ):
                texts.append((i, "", True, p))
                continue

            texts.append((i, t, False, p))

        for idx, t, skipped, p_el in texts:
            if skipped or not t:
                continue

            if self.paragraph_is_heading(p_el) or self._is_probably_list(p_el, t):
                continue

            if HYPHEN_END_RE.search(t):
                results.append((idx, t))

        run: list[tuple[int, str]] = []

        for idx, t, skipped, p_el in texts:
            if skipped or not t:
                self._flush_run(results, run, RUN_THRESHOLD)
                continue

            if self.paragraph_is_heading(p_el) or self._is_probably_list(p_el, t):
                self._flush_run(results, run, RUN_THRESHOLD)
                continue

            if len(t) < 25:
                self._flush_run(results, run, RUN_THRESHOLD)
                continue

            if self._looks_like_hard_wrapped_line(t):
                run.append((idx, t))
            else:
                self._flush_run(results, run, RUN_THRESHOLD)

        self._flush_run(results, run, RUN_THRESHOLD)

        uniq = {}
        for i, t in results:
            uniq[i] = t
        return sorted([(i, uniq[i]) for i in uniq.keys()])

    def _ppr_has_page_break_before(self, ppr: ET.Element | None) -> bool:
        """
        Ověří, zda pPr obsahuje pageBreakBefore.

        Args:
            ppr: XML element vlastností odstavce.

        Returns:
            True pokud je pageBreakBefore přítomno, jinak False.
        """
        if ppr is None:
            return False
        return ppr.find("w:pageBreakBefore", self.NS) is not None

    def paragraph_has_page_break(self, p: ET.Element) -> bool:
        return self._ppr_has_page_break_before(p.find("w:pPr", self.NS))

    def _style_has_page_break(self, style_id: str | None) -> bool:
        """
        Ověří, zda daný styl (nebo některý z jeho nadřazených stylů) obsahuje zalomení stránky.

        Args:
            style_id: ID kontrolovaného stylu.

        Returns:
            True pokud styl vynucuje zalomení stránky před odstavcem, jinak False.
        """
        style = self._find_style_by_id(style_id)
        if style is None:
            return False

        for st in self._iter_style_chain(style, follow_link=False):
            if self._ppr_has_page_break_before(st.find("w:pPr", self.NS)):
                return True

        return False

    def paragraph_text_raw(self, p: ET.Element) -> str:
        parts = []

        for t in p.findall(".//w:t", self.NS):
            if t.text is not None:
                parts.append(t.text)

        for tab in p.findall(".//w:tab", self.NS):
            parts.append("\t")

        return "".join(parts)

    def _section_properties(self, index: int) -> ET.Element | None:
        """
        Vrátí element sectPr pro zadaný oddíl.

        Args:
            index: Index oddílu.

        Returns:
            XML element sectPr, nebo None pokud jej nelze najít.
        """
        sec = self._section(index)
        if not sec:
            return None

        for el in reversed(sec):
            if el.tag.endswith("}sectPr"):
                return el

            if el.tag.endswith("}p"):
                ppr = el.find("w:pPr", self.NS)
                if ppr is not None:
                    sect = ppr.find("w:sectPr", self.NS)
                    if sect is not None:
                        return sect

        return None

    def _section_part_ref_elements(
        self, section_index: int, kind: str, *, only_default: bool = False
    ) -> list[ET.Element] | None:
        """
        Vrátí reference na části záhlaví nebo zápatí v oddílu.

        Pokud oddíl nemá vlastní reference, zkusí je dohledat v předchozích oddílech,
        protože ve Wordu může být záhlaví/zápatí převzato z minulého oddílu.

        Args:
            section_index: Index oddílu.
            kind: Typ části, například 'header' nebo 'footer'.
            only_default: Určuje, zda se mají vrátit jen default reference.

        Returns:
            Seznam referencí, nebo None pokud oddíl neexistuje.
        """
        sect_pr = self._section_properties(section_index)
        if sect_pr is None:
            return None

        for i in range(section_index, -1, -1):
            sect_pr = self._section_properties(i)
            if sect_pr is None:
                continue

            refs = sect_pr.findall(f"w:{kind}Reference", self.NS)

            if only_default:
                refs = [
                    ref
                    for ref in refs
                    if ref.attrib.get(f"{{{self.NS['w']}}}type", "default") == "default"
                ]

            if refs:
                return refs

        return []

    def _part_has_content(
        self,
        xml: ET.Element,
        *,
        check_text: bool = True,
        check_instr: bool = False,
        check_drawing: bool = False,
        check_math: bool = False,
    ) -> bool:
        """
        Ověří, zda XML část obsahuje zvolený typ obsahu.

        Args:
            xml: XML element části dokumentu.
            check_text: Kontrolovat text.
            check_instr: Kontrolovat instrukce polí.
            check_drawing: Kontrolovat kresby.
            check_math: Kontrolovat matematické objekty.

        Returns:
            True pokud je nalezen požadovaný obsah, jinak False.
        """
        if check_text:
            for t in xml.findall(".//w:t", self.NS):
                if t.text and t.text.strip():
                    return True

        if check_instr:
            for instr in xml.findall(".//w:instrText", self.NS):
                if instr.text and instr.text.strip():
                    return True

        if check_drawing and xml.findall(".//w:drawing", self.NS):
            return True

        if check_math and (
            xml.findall(".//m:oMath", self.NS) or xml.findall(".//m:oMathPara", self.NS)
        ):
            return True

        return False

    def _section_parts_have_content(
        self,
        index: int,
        kind: str,
        *,
        only_default: bool = False,
        check_text: bool = True,
        check_instr: bool = False,
        check_drawing: bool = False,
        check_math: bool = False,
    ) -> bool | None:
        """
        Ověří, zda části daného typu v oddílu obsahují zvolený obsah.

        Args:
            index: Index oddílu.
            kind: Typ části, například 'header' nebo 'footer'.
            only_default: Kontrolovat jen default reference.
            check_text: Kontrolovat text.
            check_instr: Kontrolovat instrukce polí.
            check_drawing: Kontrolovat kresby.
            check_math: Kontrolovat matematické objekty.

        Returns:
            True pokud obsah existuje, False pokud ne, nebo None pokud oddíl neexistuje.
        """
        refs = self._section_part_ref_elements(index, kind, only_default=only_default)
        if refs is None:
            return None

        for ref in refs:
            r_id = ref.attrib.get(f"{{{self.NS['r']}}}id")
            if not r_id:
                continue

            xml = self._load_part_by_rid(r_id)
            if xml is None:
                continue

            if self._part_has_content(
                xml,
                check_text=check_text,
                check_instr=check_instr,
                check_drawing=check_drawing,
                check_math=check_math,
            ):
                return True

        return False

    def section_has_header_or_footer_content(self, section_index: int) -> bool:
        has_header = self._section_parts_have_content(
            section_index,
            "header",
            only_default=True,
            check_text=True,
            check_instr=True,
        )
        has_footer = self._section_parts_have_content(
            section_index,
            "footer",
            only_default=True,
            check_text=True,
            check_instr=True,
        )

        return bool(has_header or has_footer)

    def _drawing_image_rids(self, drawing: ET.Element) -> list[str]:
        rids: list[str] = []

        for blip in drawing.findall(".//a:blip", self.NS):
            rid = blip.attrib.get(f"{{{self.NS['r']}}}embed")
            if rid:
                rids.append(rid)

        for imagedata in drawing.findall(".//v:imagedata", self.NS):
            rid = imagedata.attrib.get(f"{{{self.NS['r']}}}id")
            if rid:
                rids.append(rid)

        return list(dict.fromkeys(rids))
    
    def _drawing_chart_rids(self, drawing: ET.Element) -> list[str]:
        rids: list[str] = []

        for chart in drawing.findall(".//c:chart", self.NS):
            rid = chart.attrib.get(f"{{{self.NS['r']}}}id")
            if rid:
                rids.append(rid)

        return list(dict.fromkeys(rids))

    def _is_inside_fallback(self, element: ET.Element) -> bool:
        """
        Ověří, zda je element uvnitř větve mc:Fallback.

        Args:
            element: XML element.

        Returns:
            True pokud je element uvnitř mc:Fallback, jinak False.
        """
        fallback_tag = f"{{{self.NS['mc']}}}Fallback"
        current: ET.Element | None = element

        while current is not None:
            if current.tag == fallback_tag:
                return True

            current = self._parent_map.get(current)

        return False

    def iter_objects(self) -> list[DocumentObject]:
        objects: list[DocumentObject] = []
        seen: set[tuple[str, tuple[str, ...]]] = set()

        for p in self.iter_paragraphs():
            for drawing in p.findall(".//w:drawing", self.NS):
                if self._is_inside_fallback(drawing):
                    continue

                if drawing.find(".//pic:pic", self.NS) is not None:
                    rids = self._drawing_image_rids(drawing)
                    targets = tuple(sorted(self._rels.get(rid, rid) for rid in rids))

                    if not targets:
                        continue

                    key = ("image", targets)
                    if key not in seen:
                        seen.add(key)
                        objects.append(
                            DocumentObject(type="image", element=p, drawing=drawing)
                        )
                    continue

                if drawing.find(".//c:chart", self.NS) is not None:
                    rids = self._drawing_chart_rids(drawing)
                    targets = tuple(sorted(self._rels.get(rid, rid) for rid in rids))

                    if not targets:
                        continue

                    key = ("chart", targets)
                    if key not in seen:
                        seen.add(key)
                        objects.append(
                            DocumentObject(type="chart", element=p, drawing=drawing)
                        )
                    continue

            for obj in p.findall(".//w:object", self.NS):
                if self._is_inside_fallback(obj):
                    continue

                ole = obj.find(".//o:OLEObject", self.NS)
                if ole is None:
                    continue

                prog_id = (ole.attrib.get("ProgID") or "").strip()

                if prog_id.startswith("Excel.Sheet"):
                    key = ("table", (str(id(obj)),))
                    if key not in seen:
                        seen.add(key)
                        objects.append(DocumentObject(type="table", element=p))
                    continue

            if p.findall(".//m:oMath", self.NS) or p.findall(".//m:oMathPara", self.NS):
                key = ("equation", (str(id(p)),))
                if key not in seen:
                    seen.add(key)
                    objects.append(DocumentObject(type="equation", element=p))

        for tbl in self._xml.findall(".//w:tbl", self.NS):
            if self._is_inside_fallback(tbl):
                continue

            key = ("table", (str(id(tbl)),))
            if key not in seen:
                seen.add(key)
                objects.append(DocumentObject(type="table", element=tbl))

        return objects
    
    def _caption_paragraph_text(self, p: ET.Element) -> str:
        """
        Vrátí viditelný text konkrétního odstavce titulku bez instrukcí polí.

        Args:
            p: XML element odstavce.

        Returns:
            Text odstavce.
        """
        parts: list[str] = []
        inside_instr = False

        for child in p:
            tag = child.tag

            if tag == f"{{{self.NS['w']}}}r":
                fld_char = child.find("w:fldChar", self.NS)
                if fld_char is not None:
                    fld_type = fld_char.attrib.get(f"{{{self.NS['w']}}}fldCharType")
                    if fld_type == "begin":
                        inside_instr = True
                    elif fld_type == "separate":
                        inside_instr = False
                    elif fld_type == "end":
                        inside_instr = False
                    continue

                if inside_instr:
                    continue

                if child.find("w:footnoteReference", self.NS) is not None:
                    continue

                if child.find("w:endnoteReference", self.NS) is not None:
                    continue

                for t in child.findall("w:t", self.NS):
                    if t.text:
                        parts.append(t.text)

            elif tag == f"{{{self.NS['w']}}}fldSimple":
                instr = child.attrib.get(f"{{{self.NS['w']}}}instr", "") or ""
                instr_upper = instr.upper()

                if "PAGEREF" in instr_upper or "REF " in instr_upper:
                    continue

                for t in child.findall(".//w:t", self.NS):
                    if t.text:
                        parts.append(t.text)

            elif tag == f"{{{self.NS['w']}}}sdt":
                for t in child.findall(".//w:t", self.NS):
                    if t.text:
                        parts.append(t.text)

        return normalize_spaces("".join(parts)).strip()

    def iter_figure_caption_texts(self) -> list[str]:
        captions: list[str] = []
        seen: set[str] = set()

        FIGURE_CAPTION_RE = re.compile(
            r"^(obrázek|figure)\s+\d+\s*:?",
            re.IGNORECASE,
        )

        paragraphs = self._xml.findall(".//w:p", self.NS)

        for i, p in enumerate(paragraphs, start=1):
            label = self._paragraph_has_seq_caption(p)
            raw_text = normalize_spaces(self._caption_paragraph_text(p)).strip()
            style_name = self._style_name_of(p)

            if not label:
                continue

            if not raw_text:
                continue

            is_caption_style = (style_name or "").strip().lower() == "titulek"

            if not FIGURE_CAPTION_RE.match(raw_text) and not is_caption_style:
                continue

            if not FIGURE_CAPTION_RE.match(raw_text):
                continue

            text = raw_text

            if text in seen:
                continue

            seen.add(text)
            captions.append(text)

        return captions
        
    def _list_entry_text_without_page_number(self, p: ET.Element) -> str:
        """
        Vrátí text položky seznamu obrázků bez čísla stránky.

        Args:
            p: XML odstavec s položkou seznamu obrázků.

        Returns:
            Text položky bez koncového čísla stránky.
        """
        parts: list[str] = []

        for idx, r in enumerate(p.findall(".//w:r", self.NS), start=1):
            instr_texts: list[str] = []
            for instr in r.findall(".//w:instrText", self.NS):
                if instr.text:
                    instr_texts.append(instr.text)

            joined_instr = " ".join(instr_texts).upper()

            texts: list[str] = []
            for t in r.findall(".//w:t", self.NS):
                if t.text:
                    texts.append(t.text)

            run_text = "".join(texts)

            if "PAGEREF" in joined_instr:
                break

            if run_text:
                parts.append(run_text)

        text = normalize_spaces("".join(parts)).strip()

        return text

    def _extract_toc_caption_label(self, joined_instr: str) -> str | None:
        """
        Z TOC pole vytáhne hodnotu parametru \\c.

        Args:
            joined_instr: Spojený text instrukcí pole.

        Returns:
            Hodnota parametru \\c nebo None.
        """
        m = re.search(r'\\C\s+"([^"]+)"', joined_instr, re.IGNORECASE)
        if not m:
            return None

        return normalize_spaces(m.group(1)).strip().upper()

    def _is_figure_toc_label(self, label: str | None) -> bool:
        """
        Určí, zda label TOC odpovídá seznamu obrázků.

        Args:
            label: Hodnota parametru \\c z TOC pole.

        Returns:
            True, pokud jde o label obrázků.
        """
        if not label:
            return False

        if label in {"OBRÁZEK", "FIGURE"}:
            return True

        if label.startswith("OBRÁZEK") or label.startswith("FIGURE"):
            return True

        return False

    def iter_list_of_figures_texts(self) -> list[str]:
        items: list[str] = []

        paragraphs = list(self._xml.findall(".//w:body//w:p", self.NS))

        is_inside_figures_toc = False
        seen_list_heading = False
        waiting_for_figures_toc_after_heading = False

        for i, p in enumerate(paragraphs, start=1):
            para_text = normalize_spaces(self.paragraph_text(p)).strip()

            instr_texts: list[str] = []
            for instr in p.findall(".//w:instrText", self.NS):
                if instr.text:
                    instr_texts.append(instr.text.upper())

            joined_instr = " ".join(instr_texts)
            toc_label = self._extract_toc_caption_label(joined_instr)

            upper_para = para_text.upper()

            if upper_para in {"SEZNAM OBRÁZKŮ", "LIST OF FIGURES"}:
                seen_list_heading = True
                waiting_for_figures_toc_after_heading = True

                text = normalize_spaces(self._list_entry_text_without_page_number(p)).strip()
                if not text:
                    continue

            if not is_inside_figures_toc:
                if "TOC" in joined_instr and "\\C" in joined_instr:
                    if self._is_figure_toc_label(toc_label):
                        is_inside_figures_toc = True
                        waiting_for_figures_toc_after_heading = False

                    elif waiting_for_figures_toc_after_heading:
                        is_inside_figures_toc = True
                        waiting_for_figures_toc_after_heading = False

                if not is_inside_figures_toc:
                    if waiting_for_figures_toc_after_heading and para_text:
                        if upper_para not in {"SEZNAM OBRÁZKŮ", "LIST OF FIGURES"}:
                            waiting_for_figures_toc_after_heading = False
                    continue

            else:
                if "TOC" in joined_instr and "\\C" in joined_instr:
                    if not self._is_figure_toc_label(toc_label):
                        break

            if p.find("w:pPr/w:sectPr", self.NS) is not None:
                break

            text = normalize_spaces(self._list_entry_text_without_page_number(p)).strip()

            if not text:
                continue

            upper = text.upper()

            if upper in {"SEZNAM OBRÁZKŮ", "LIST OF FIGURES"}:
                continue

            if upper.startswith("OBRÁZEK") or upper.startswith("FIGURE"):
                items.append(text)

        return items

    def _object_image_rids(self, element) -> list[str]:
        """
        Získá seznam ID relací (rId) všech obrázků v daném XML elementu.

        Args:
            element: XML element k prohledání (např. tvar nebo kresba).

        Returns:
            Seznam nalezených rId (např. ['rId4', 'rId5']).
        """
        rids = []

        for blip in element.findall(".//a:blip", self.NS):
            rid = blip.attrib.get(f"{{{self.NS['r']}}}embed")
            if rid:
                rids.append(rid)

        return rids

    def _get_image_bytes(self, r_id: str) -> bytes | None:
        """
        Vrátí binární data obrázku podle jeho ID relace (rId).

        Args:
            r_id: ID relace (např. 'rId4').

        Returns:
            Bajty obrázku nebo None při chybě.
        """
        target = self._rels.get(r_id)
        if not target or not target.startswith("media/"):
            return None

        media_path = f"word/{target}"
        try:
            with self._zip.open(media_path) as f:
                return f.read()
        except KeyError:
            return None

    def get_object_image_bytes(self, obj: DocumentObject) -> bytes | None:
        if obj is None or obj.type != "image" or obj.element is None:
            return None

        for rid in self._object_image_rids(obj.element):
            img = self._get_image_bytes(rid)
            if img:
                return img

        return None

    def get_object_qr_data(self, obj: DocumentObject) -> str | None:
        try:
            import cv2
            import numpy as np
            from PIL import Image
        except ImportError:
            return None
        image_bytes = self.get_object_image_bytes(obj)
        if not image_bytes:
            return None

        try:
            with Image.open(io.BytesIO(image_bytes)) as im:
                im = im.convert("RGB")
                arr = np.array(im)
                arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        except Exception:
            return None

        detector = cv2.QRCodeDetector()

        try:
            data, points, _ = detector.detectAndDecode(arr)
        except Exception:
            return None

        if data:
            return data.strip()

        return None

    def get_object_data_id(self, obj: DocumentObject) -> str | None:
        return self.get_object_qr_data(obj)

    def _paragraph_has_seq_caption(self, p: ET.Element) -> str | None:
        """
        Zjistí, zda odstavec obsahuje caption pole typu SEQ.

        Args:
            p: XML element odstavce.

        Returns:
            Název SEQ sekvence, například 'Obrázek' nebo 'Tabulka',
            nebo None pokud odstavec SEQ caption neobsahuje.
        """
        if p is None:
            return None

        instructions = self._extract_instructions_from_element(p)

        if not instructions:
            return None

        joined_instr = " ".join(instructions)

        m = re.search(r"\bSEQ\s+([^\s\\]+)", joined_instr, re.IGNORECASE)
        if m:
            return m.group(1)

        return None

    def _get_adjacent_paragraph(
        self,
        element: ET.Element,
        direction: int,
    ) -> ET.Element | None:
        """
        Vrátí nejbližší neprázdný odstavec před nebo za zadaným elementem.

        Args:
            element: Výchozí element, vůči kterému se hledá sousední odstavec.
            direction: Směr hledání; -1 pro předchozí odstavec, 1 pro následující.

        Returns:
            Nejbližší neprázdný odstavec v daném směru, nebo None pokud neexistuje.
        """
        paragraphs = list(self.iter_paragraphs())
        try:
            idx = paragraphs.index(element)
        except ValueError:
            return None

        # direction == -1 pro hledání zpět, 1 pro hledání vpřed
        search_space = (
            reversed(paragraphs[:idx]) if direction == -1 else paragraphs[idx + 1 :]
        )

        for p in search_space:
            if self.paragraph_text(p):
                return p
        return None

    def _paragraph_before(self, element: ET.Element) -> ET.Element | None:
        """
        Vrátí nejbližší neprázdný odstavec před zadaným elementem.

        Args:
            element: Element, před kterým se hledá odstavec.

        Returns:
            Předchozí neprázdný odstavec, nebo None pokud neexistuje.
        """
        return self._get_adjacent_paragraph(element, direction=-1)

    def _paragraph_after(self, element: ET.Element) -> ET.Element | None:
        """
        Vrátí nejbližší neprázdný odstavec za zadaným elementem.

        Args:
            element: Element, za kterým se hledá odstavec.

        Returns:
            Následující neprázdný odstavec, nebo None pokud neexistuje.
        """
        return self._get_adjacent_paragraph(element, direction=1)

    def _extract_instructions_from_element(self, element: ET.Element) -> list[str]:
        """
        Vrátí instrukce polí nalezené v elementu.

        Args:
            element: XML element pro prohledání.

        Returns:
            Seznam textů instrukcí.
        """
        instrs: list[str] = []

        for fld in element.findall(".//w:fldSimple", self.NS):
            instr_val = fld.attrib.get(f"{{{self.NS['w']}}}instr")
            if instr_val:
                instrs.append(instr_val.strip())

        for instr_el in element.findall(".//w:instrText", self.NS):
            if instr_el.text:
                instrs.append(instr_el.text.strip())

        return instrs

    def _paragraph_is_toc_or_object_list(self, p: ET.Element) -> bool:
        """
        Ověří, zda odstavec patří do automaticky generovaného obsahu
        nebo seznamu objektů.

        Args:
            p: XML element odstavce.

        Returns:
            True pokud odstavec patří do obsahu nebo seznamu objektů,
            jinak False.
        """
        instructions = self._extract_instructions_from_element(p)
        instr_joined = " ".join(instructions).upper()

        if "TOC" in instr_joined:
            return True

        if "PAGEREF" in instr_joined:
            cur: ET.Element | None = p

            while cur is not None:
                if cur.tag == f"{{{self.NS['w']}}}sdt":
                    sdt_text = " ".join(
                        self._extract_instructions_from_element(cur)
                    ).upper()
                    if "TOC" in sdt_text:
                        return True

                cur = self._parent_of(cur)

        return False

    def _load_bibliography_xml(self) -> ET.Element | None:
        """
        Načte XML část obsahující bibliografické zdroje.

        Returns:
            Kořenový XML element bibliografie, nebo None pokud nebyla nalezena.
        """
        for name in self._zip.namelist():
            if not name.startswith("customXml/") or not name.endswith(".xml"):
                continue

            try:
                root = self._load(name)
            except Exception:
                continue

            if root is not None and root.findall(".//b:Source", self.NS):
                return root

        return None

    def iter_bibliography_source_tags(self) -> list[str]:
        bib = self._load_bibliography_xml()
        if bib is None:
            return []

        tags: list[str] = []
        for src in bib.findall(".//b:Source", self.NS):
            tag_el = src.find("b:Tag", self.NS)
            if tag_el is not None and (tag_el.text or "").strip():
                tags.append((tag_el.text or "").strip())

        return tags

    def find_duplicate_bibliography_tags(self) -> list[str]:
        tags = self.iter_bibliography_source_tags()
        seen = set()
        dup = set()
        for t in tags:
            if t in seen:
                dup.add(t)
            else:
                seen.add(t)
        return sorted(dup)

    def iter_citation_tags_in_order(self) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []

        for sdt in self._xml.findall(".//w:sdt", self.NS):
            sdt_pr = sdt.find("w:sdtPr", self.NS)
            if sdt_pr is None or sdt_pr.find("w:citation", self.NS) is None:
                continue

            tag = self._extract_citation_tag_from_sdt(sdt)
            if not tag:
                continue

            if tag not in seen:
                seen.add(tag)
                ordered.append(tag)

        return ordered

    def _extract_citation_tag_from_sdt(self, sdt: ET.Element) -> str | None:
        """
        Získá citační tag z content controlu citace.

        Args:
            sdt: XML element content controlu.

        Returns:
            Citační tag, nebo None pokud se jej nepodaří zjistit.
        """
        CITATION_INSTR_RE = re.compile(r"\bCITATION\s+([^\s\\]+)", re.IGNORECASE)
        instr_parts = []
        for instr_el in sdt.findall(".//w:instrText", self.NS):
            if instr_el.text:
                instr_parts.append(instr_el.text)

        if instr_parts:
            joined = " ".join(instr_parts)
            m = CITATION_INSTR_RE.search(joined)
            if m:
                return m.group(1)

        for fld in sdt.findall(".//w:fldSimple", self.NS):
            instr = (fld.attrib.get(f"{{{self.NS['w']}}}instr") or "").strip()
            m = CITATION_INSTR_RE.search(instr)
            if m:
                return m.group(1)

        return None

    def _extract_citation_result_number_from_sdt(self, sdt: ET.Element) -> int | None:
        """
        Získá zobrazené číslo citace z výsledného textu content controlu.

        Args:
            sdt: XML element content controlu citace.

        Returns:
            Číslo citace, nebo None pokud jej nelze určit.
        """
        CITATION_RESULT_NUM_RE = re.compile(r"\(?\s*(\d+)\s*\)?")  # (2) nebo 2
        parts: list[str] = []
        for t_el in sdt.findall(".//w:sdtContent//w:t", self.NS):
            if t_el.text:
                parts.append(t_el.text)

        rendered = "".join(parts).strip()
        if not rendered:
            return None

        m = CITATION_RESULT_NUM_RE.search(rendered)
        if not m:
            return None
        try:
            return int(m.group(1))
        except ValueError:
            return None

    def get_unique_citation_tags(self) -> set[str]:
        return set(self.iter_citation_tags_in_order())

    def _source_match_tokens(self, src) -> list[str]:
        """
        Připraví rozpoznávací tokeny zdroje pro párování s vyrenderovanou bibliografií.
        """
        tokens: list[str] = []

        author = str(getattr(src, "author", "") or "").strip()
        title = str(getattr(src, "title", "") or "").strip()
        year = str(getattr(src, "year", "") or "").strip()

        if author:
            tokens.append(author.lower())
            first_part = author.split(",")[0].strip().lower()
            if first_part and first_part not in tokens:
                tokens.append(first_part)

        if title:
            tokens.append(title.lower())

        if year:
            tokens.append(year)

        return tokens
    
    def _iter_rendered_bibliography_paragraphs(self) -> list[str]:
        """
        Vrátí texty položek ze zobrazeného seznamu literatury v pořadí v dokumentu.

        Returns:
            Seznam textů bibliografických položek.
        """
        paragraphs: list[str] = []

        for sdt in self._xml.findall(".//w:sdt", self.NS):
            if not self._is_bibliography_sdt(sdt):
                continue

            for p in sdt.findall(".//w:p", self.NS):
                ppr = p.find("w:pPr", self.NS)
                if ppr is None:
                    continue

                ps = ppr.find("w:pStyle", self.NS)
                if ps is None:
                    continue

                style = ps.attrib.get(f"{{{self.NS['w']}}}val", "").lower()
                if style not in ("bibliografie", "bibliography"):
                    continue

                text = self.paragraph_text(p).strip()
                if text:
                    paragraphs.append(text)

        return paragraphs

    def iter_rendered_bibliography_tags_in_order(self) -> list[str]:
        paragraphs = self._iter_rendered_bibliography_paragraphs()
        sources = list(self.iter_bibliography_sources())

        ordered_tags: list[str] = []
        used_tags: set[str] = set()

        for paragraph in paragraphs:
            paragraph_l = paragraph.lower()
            best_tag = None
            best_score = -1

            for src in sources:
                tag = (src.tag or "").strip()
                if not tag or tag in used_tags:
                    continue

                score = 0
                for token in self._source_match_tokens(src):
                    if token and token in paragraph_l:
                        score += 1

                if score > best_score:
                    best_score = score
                    best_tag = tag

            if best_tag and best_score > 0:
                used_tags.add(best_tag)
                ordered_tags.append(best_tag)

        return ordered_tags

    def _parse_ref_order(self, src) -> int | float:
        """
        Vrátí RefOrder zdroje jako číslo pro řazení.

        Returns:
            Hodnota RefOrder, nebo nekonečno při chybějící/neplatné hodnotě.
        """
        ref_el = src.find("b:RefOrder", self.NS)
        if ref_el is None:
            return float("inf")

        try:
            return int((ref_el.text or "").strip())
        except ValueError:
            return float("inf")


    def iter_bibliography_source_tags_in_order(self) -> list[str]:
        bib = self._load_bibliography_xml()
        if bib is None:
            return []

        items: list[tuple[int | float, str]] = []

        for src in bib.findall(".//b:Source", self.NS):
            tag_el = src.find("b:Tag", self.NS)
            if tag_el is None:
                continue

            tag = (tag_el.text or "").strip()
            if not tag:
                continue

            ref_order = self._parse_ref_order(src)
            items.append((ref_order, tag))

        items.sort(key=lambda item: item[0])
        return [tag for _, tag in items]

    def has_bibliography(self) -> bool:
        for sdt in self._xml.findall(".//w:sdt", self.NS):
            if self._is_bibliography_sdt(sdt):
                return True

        for instr in self._xml.findall(".//w:instrText", self.NS):
            text = (instr.text or "").strip().upper()
            if "BIBLIOGRAPHY" in text:
                return True

        for p in self._xml.findall(".//w:p", self.NS):
            ppr = p.find("w:pPr", self.NS)
            if ppr is None:
                continue

            pstyle = ppr.find("w:pStyle", self.NS)
            if pstyle is None:
                continue

            style = (
                pstyle.attrib.get(f"{{{self.NS['w']}}}val", "") or ""
            ).strip().lower()

            if style in {"bibliografie", "bibliography"}:
                return True

        return False

    def count_bibliography_items(self) -> int:
        count = 0

        for sdt in self._xml.findall(".//w:sdt", self.NS):
            if not self._is_bibliography_sdt(sdt):
                continue

            sdt_pr = sdt.find("w:sdtPr", self.NS)
            is_word_bib = (
                sdt_pr is not None
                and sdt_pr.find("w:bibliography", self.NS) is not None
            )

            if is_word_bib:
                for p in sdt.findall(".//w:p", self.NS):
                    ppr = p.find("w:pPr", self.NS)
                    if ppr is None:
                        continue

                    ps = ppr.find("w:pStyle", self.NS)
                    if ps is None:
                        continue

                    style = ps.attrib.get(f"{{{self.NS['w']}}}val", "").lower()
                    if style in ("bibliografie", "bibliography"):
                        if self.paragraph_text(p):
                            count += 1
            else:
                for tr in sdt.findall(".//w:tr", self.NS):
                    row_texts = []

                    for p in tr.findall(".//w:p", self.NS):
                        txt = self.paragraph_text(p)
                        if txt:
                            row_texts.append(txt)

                    row_text = " ".join(row_texts).strip()
                    if row_text:
                        count += 1

        if count > 0:
            return count

        for p in self._xml.findall(".//w:p", self.NS):
            ppr = p.find("w:pPr", self.NS)
            if ppr is None:
                continue

            ps = ppr.find("w:pStyle", self.NS)
            if ps is None:
                continue

            style = ps.attrib.get(f"{{{self.NS['w']}}}val", "").strip().lower()
            if style not in ("bibliografie", "bibliography"):
                continue

            if self.paragraph_text(p).strip():
                count += 1

        return count

    def _bib_text(self, el: ET.Element | None) -> str:
        """
        Vrátí oříznutý text XML elementu bibliografie.

        Args:
            el: XML element.

        Returns:
            Text elementu bez okolních mezer, nebo prázdný řetězec.
        """
        return (el.text or "").strip() if el is not None else ""

    def _bib_norm_type(self, src_type: str) -> str:
        """
        Normalizuje typ bibliografického zdroje na interní označení.

        Args:
            src_type: Původní typ zdroje.

        Returns:
            Normalizovaný typ zdroje.
        """
        st = (src_type or "").strip().lower()
        return self.BIB_TYPE_MAP.get(st, st)

    def _bib_author_string(self, src: ET.Element) -> str:
        """
        Sestaví textovou reprezentaci autorů bibliografického zdroje.

        Args:
            src: XML element bibliografického zdroje.

        Returns:
            Řetězec s autory nebo korporátním autorem.
        """
        persons = src.findall(".//b:Author//b:Person", self.NS)

        seen: set[tuple[str, str]] = set()
        out: list[str] = []

        for p in persons:
            last = self._bib_text(p.find("b:Last", self.NS))
            first = self._bib_text(p.find("b:First", self.NS))

            key = (last, first)
            if key in seen:
                continue
            seen.add(key)

            if last and first:
                out.append(f"{last}, {first}")
            elif last:
                out.append(last)
            elif first:
                out.append(first)

        if out:
            return "; ".join(out)

        corp = src.find(".//b:Author//b:Corporate", self.NS)
        return self._bib_text(corp) or ""

    def iter_bibliography_sources(self) -> list[BibliographySource]:
        bib = self._load_bibliography_xml()
        if bib is None:
            return []

        sources: list[BibliographySource] = []

        for src in bib.findall(".//b:Source", self.NS):
            tag = self._bib_text(src.find("b:Tag", self.NS))
            if not tag:
                continue

            stype = self._bib_norm_type(
                self._bib_text(src.find("b:SourceType", self.NS))
            )
            author = self._bib_author_string(src)

            title = self._bib_text(src.find("b:Title", self.NS))
            if title.endswith("."):
                title = title[:-1].strip()

            year = self._bib_text(src.find("b:Year", self.NS))
            publisher = self._bib_text(src.find("b:Publisher", self.NS))
            city = self._bib_text(src.find("b:City", self.NS))
            stdnum = self._bib_text(src.find("b:StandardNumber", self.NS))
            ref_order = self._bib_text(src.find("b:RefOrder", self.NS))
            url = self._bib_text(src.find("b:URL", self.NS))
            note = self._bib_text(src.find("b:Comments", self.NS))

            year_accessed = self._bib_text(src.find("b:YearAccessed", self.NS))
            month_accessed = self._bib_text(src.find("b:MonthAccessed", self.NS))
            day_accessed = self._bib_text(src.find("b:DayAccessed", self.NS))

            access_date = " ".join(
                part for part in (day_accessed, month_accessed, year_accessed) if part
            ).strip()

            journal = self._bib_text(
                src.find("b:JournalName", self.NS)
            ) or self._bib_text(src.find("b:JournalTitle", self.NS))
            volume = self._bib_text(src.find("b:Volume", self.NS))
            number = self._bib_text(src.find("b:Issue", self.NS)) or self._bib_text(
                src.find("b:Number", self.NS)
            )
            pages = self._bib_text(src.find("b:Pages", self.NS))

            sources.append(
                BibliographySource(
                    tag=tag,
                    type=stype,
                    author=author,
                    title=title,
                    year=year,
                    publisher=publisher,
                    address=city,
                    isbn=stdnum,
                    ref_order=ref_order,
                    url=url,
                    journal=journal,
                    volume=volume,
                    number=number,
                    pages=pages,
                    note=note,
                    access_date=access_date,
                )
            )

        return sources

    def _body_child_of(self, el: ET.Element) -> ET.Element | None:
        """
        Vrátí přímého potomka w:body, pod kterého zadaný element patří.

        Args:
            el: XML element uvnitř těla dokumentu.

        Returns:
            Přímý potomek body, nebo None pokud jej nelze určit.
        """
        WP_BODY = f"{{{self.NS['w']}}}body"

        cur = el
        while cur is not None:
            parent = self._parent_of(cur)
            if parent is None:
                return None
            if parent.tag == WP_BODY:
                return cur
            cur = parent
        return None

    def _is_inside_toc_sdt(self, p: ET.Element) -> bool:
        """
        Ověří, zda je odstavec umístěný uvnitř content controlu obsahu.

        Args:
            p: XML element odstavce.

        Returns:
            True pokud je odstavec uvnitř TOC SDT, jinak False.
        """
        cur = p
        while True:
            if cur.tag == f"{{{self.NS['w']}}}sdt":
                pr = cur.find("w:sdtPr", self.NS)
                if pr is not None and pr.find("w:docPartObj", self.NS) is not None:
                    return True

            parent = self._parent_of(cur)
            if parent is None:
                break
            cur = parent

        return False

    def _paragraph_is_citation_only(self, p: ET.Element) -> bool:
        """
        Ověří, zda odstavec obsahuje pouze samotnou citaci nebo její číslo.

        Args:
            p: XML element odstavce.

        Returns:
            True pokud odstavec představuje jen citaci, jinak False.
        """
        CIT_ONLY_NUM_RE = re.compile(r"^[\(\[\s]*\d+[\)\]\s]*$")
        visible = (self.paragraph_text(p) or "").strip()

        if not visible:
            return bool(p.findall(".//w:sdt[w:sdtPr/w:citation]", self.NS))

        if not CIT_ONLY_NUM_RE.fullmatch(visible):
            return False

        return bool(p.findall(".//w:sdt[w:sdtPr/w:citation]", self.NS))

    def _paragraph_section_index(self, p: ET.Element) -> int | None:
        """
        Určí index oddílu, do kterého odstavec patří.

        Args:
            p: XML element odstavce.

        Returns:
            Index oddílu, nebo None pokud jej nelze určit.
        """
        body_child = self._body_child_of(p)
        if body_child is None:
            return None

        for si, sec in enumerate(self._sections):
            for el in sec:
                if el is body_child:
                    return si
        return None

    def _is_citation_sdt(self, sdt: ET.Element) -> bool:
        """
        Ověří, zda content control odpovídá citaci.

        Args:
            sdt: XML element content controlu.

        Returns:
            True pokud jde o citaci, jinak False.
        """
        sdt_pr = sdt.find("w:sdtPr", self.NS)
        if sdt_pr is None:
            return False

        if sdt_pr.find("w:citation", self.NS) is not None:
            return True

        alias_el = sdt_pr.find("w:alias", self.NS)
        tag_el = sdt_pr.find("w:tag", self.NS)

        alias_val = (
            alias_el.attrib.get(f"{{{self.NS['w']}}}val", "")
            if alias_el is not None
            else ""
        )
        tag_val = (
            tag_el.attrib.get(f"{{{self.NS['w']}}}val", "")
            if tag_el is not None
            else ""
        )

        alias_val = alias_val.lower()
        tag_val = tag_val.lower()

        return (
            "citace pro" in alias_val
            and tag_val.startswith("citpro#")
            and "#b#" not in tag_val
        )

    def _extract_any_citation_tag_from_sdt(self, sdt: ET.Element) -> str | None:
        """
        Pokusí se získat citační tag z content controlu více způsoby.

        Args:
            sdt: XML element content controlu.

        Returns:
            Citační tag, nebo None pokud jej nelze zjistit.
        """
        tag = self._extract_citation_tag_from_sdt(sdt)
        if tag:
            return tag

        sdt_pr = sdt.find("w:sdtPr", self.NS)
        if sdt_pr is None:
            return None

        tag_el = sdt_pr.find("w:tag", self.NS)
        if tag_el is None:
            return None

        raw = (tag_el.attrib.get(f"{{{self.NS['w']}}}val") or "").strip()
        if not raw:
            return None

        low = raw.lower()
        if low.startswith("citpro#") and "#b#" not in low:
            return raw

        return None

    def _extract_any_citation_number_from_sdt(self, sdt: ET.Element) -> int | None:
        """
        Získá číslo citace ze zobrazeného textu content controlu.

        Args:
            sdt: XML element content controlu.

        Returns:
            Číslo citace, nebo None pokud jej nelze zjistit.
        """
        text = "".join(t.text or "" for t in sdt.findall(".//w:t", self.NS)).strip()
        m = re.search(r"\((\d+)\)", text)
        if m:
            return int(m.group(1))
        return None

    def _extract_citations_from_paragraph(self, p: ET.Element) -> list[tuple[str, int]]:
        """
        Vrátí všechny citace nalezené v odstavci.

        Args:
            p: XML element odstavce.

        Returns:
            Seznam dvojic ve tvaru (tag, číslo).
        """
        out: list[tuple[str, int]] = []

        for sdt in p.findall(".//w:sdt", self.NS):
            sdt_pr = sdt.find("w:sdtPr", self.NS)
            if sdt_pr is None:
                continue

            if sdt_pr.find("w:citation", self.NS) is not None:
                tag = self._extract_citation_tag_from_sdt(sdt)
                if not tag:
                    continue

                num = self._extract_citation_result_number_from_sdt(sdt)
                if num is None:
                    num = self._extract_any_citation_number_from_sdt(sdt)
                if num is None:
                    continue

                out.append((tag, num))
                continue

            if self._is_citation_sdt(sdt):
                tag = self._extract_any_citation_tag_from_sdt(sdt)
                if not tag:
                    continue

                num = self._extract_any_citation_number_from_sdt(sdt)
                if num is None:
                    continue

                out.append((tag, num))

        return out


    def _paragraph_direct_text(self, p: ET.Element) -> str:
        """
        Vrátí pouze přímý text odstavce, bez textu z textboxů,
        drawing/pict objektů a bez instrukcí polí.

        Args:
            p: XML element odstavce.

        Returns:
            Přímý text odstavce.
        """
        parts: list[str] = []
        inside_instr = False

        for child in p:
            tag = child.tag

            if tag != f"{{{self.NS['w']}}}r":
                continue

            if child.find("w:drawing", self.NS) is not None:
                continue

            if child.find("w:pict", self.NS) is not None:
                continue

            fld_char = child.find("w:fldChar", self.NS)
            if fld_char is not None:
                fld_type = fld_char.attrib.get(f"{{{self.NS['w']}}}fldCharType")
                if fld_type == "begin":
                    inside_instr = True
                elif fld_type in {"separate", "end"}:
                    inside_instr = False
                continue

            if inside_instr:
                continue

            if child.find("w:instrText", self.NS) is not None:
                continue

            if child.find("w:footnoteReference", self.NS) is not None:
                continue

            if child.find("w:endnoteReference", self.NS) is not None:
                continue

            for t in child.findall("w:t", self.NS):
                if t.text:
                    parts.append(t.text)

        return normalize_spaces("".join(parts)).strip()

    def _extract_citations_from_text(self, text: str) -> list[tuple[str, int]]:
        """
        Vrátí citace nalezené v čistém textu ve formátu (tag, číslo).

        Args:
            text: Text, ve kterém se mají hledat citační značky.

        Returns:
            Seznam dvojic (tag, číslo).
        """
        if not text:
            return []

        numbers = re.findall(r"\((\d+)\)", text)
        if not numbers:
            return []

        found: list[tuple[str, int]] = []
        seen: set[tuple[str, int]] = set()

        citation_map: dict[int, str] = {}

        for tag, num in self._extract_citations_from_paragraph_text_source(text):
            citation_map[num] = tag

        for num_str in numbers:
            num = int(num_str)
            tag = citation_map.get(num, "?")
            item = (tag, num)

            if item not in seen:
                seen.add(item)
                found.append(item)

        return found

    def _extract_citations_from_paragraph_text_source(
        self,
        text: str,
    ) -> list[tuple[str, int]]:
        """
        Pomocná funkce pro převod citačních značek z textu na dvojice
        (tag, číslo). Pokud nelze určit tag, použije se '?'.

        Args:
            text: Zdrojový text.

        Returns:
            Seznam dvojic (tag, číslo).
        """
        if not text:
            return []

        numbers = re.findall(r"\((\d+)\)", text)
        if not numbers:
            return []

        return [("?", int(n)) for n in numbers]

    def find_citations_in_wrong_places(self) -> list[dict]:
        problems: list[dict] = []
        paragraphs = list(self.iter_paragraphs())

        first_h1_section: int | None = None
        for i, p in enumerate(paragraphs, start=1):
            heading_level = self.paragraph_heading_level(p)
            sec_idx = self._paragraph_section_index(p)

            if heading_level == 1:
                first_h1_section = sec_idx
                break

        for i, p in enumerate(paragraphs, start=1):
            raw_text = (self.paragraph_text_raw(p) or "").strip()
            visible_text = (self.paragraph_text(p) or "").strip()
            direct_text = (self._paragraph_direct_text(p) or "").strip()

            snippet = (visible_text or raw_text or "").strip()
            snippet_short = snippet[:120] if snippet else ""

            cites = self._extract_citations_from_paragraph(p)
            direct_cites = self._extract_citations_from_text(direct_text)

            if not cites:
                continue

            in_toc = self.paragraph_is_toc(p)
            is_heading = self.paragraph_is_heading(p)
            heading_level = self.paragraph_heading_level(p)
            sec_idx = self._paragraph_section_index(p)

            in_cover_part = (
                sec_idx is not None
                and first_h1_section is not None
                and sec_idx < first_h1_section
            )

            in_first_section = sec_idx == 0

            is_empty = self.paragraph_is_empty(p)
            is_citation_only = self._paragraph_is_citation_only(p)
            empty_or_only_cit = is_empty or is_citation_only

            reason_key = None
            relevant_cites = cites

            if in_toc:
                reason_key = "reason_in_toc"

            elif is_heading and direct_cites:
                reason_key = "reason_in_heading"
                relevant_cites = direct_cites

            elif in_first_section or in_cover_part:
                reason_key = "reason_in_cover"

            elif empty_or_only_cit:
                reason_key = "reason_citation_only_or_empty"

            if not reason_key:
                continue

            for tag, num in relevant_cites:
                problems.append(
                    {
                        "tag": tag,
                        "num": num,
                        "reason_key": reason_key,
                        "snippet": snippet_short,
                        "section": sec_idx,
                    }
                )

        return problems

    def _load_part_by_rid(self, r_id: str) -> ET.Element | None:
        """
        Načte XML část dokumentu podle relationship ID.

        Args:
            r_id: Identifikátor relace.

        Returns:
            Kořenový XML element části, nebo None pokud část neexistuje.
        """
        part = self._rel_target_path(r_id)
        if not part:
            return None
        try:
            return self._load(part)
        except KeyError:
            return None

    def _paragraph_is_generated_by_field(self, p: ET.Element) -> bool:
        """
        Ověří, zda je odstavec generovaný pomocí pole.

        Args:
            p: XML element odstavce.

        Returns:
            True pokud odstavec obsahuje field char nebo instrukce pole, jinak False.
        """
        if p.findall(".//w:fldChar", self.NS):
            return True
        if p.findall(".//w:instrText", self.NS):
            return True
        return False

    def _visible_text(self, element: ET.Element) -> str:
        """
        Vrátí viditelný text elementu s ignorováním skrytých runů.

        Args:
            element: XML element.

        Returns:
            Viditelný text po normalizaci mezer.
        """
        parts = []

        for r in element.findall(".//w:r", self.NS):
            rpr = r.find("w:rPr", self.NS)
            if rpr is not None and rpr.find("w:webHidden", self.NS) is not None:
                continue

            if r.find("w:tab", self.NS) is not None:
                parts.append(" ")

            for t in r.findall("w:t", self.NS):
                if t.text:
                    parts.append(t.text)

        txt = "".join(parts)
        txt = normalize_spaces(txt)
        return txt

    def get_style_parent(self, style_name: str) -> str | None:
        style_el = self._find_style(name=style_name)
        if style_el is None:
            return None

        based_el = style_el.find("w:basedOn", self.NS)
        if based_el is None:
            return None

        parent_id = based_el.attrib.get(f"{{{self.NS['w']}}}val")
        if not parent_id:
            return None

        parent_style = self._find_style_by_id(parent_id)
        if parent_style is None:
            return None

        name_el = parent_style.find("w:name", self.NS)
        if name_el is None:
            return None

        return name_el.attrib.get(f"{{{self.NS['w']}}}val")

    def get_used_paragraph_styles(self) -> set[str]:
        used: set[str] = set()

        for p in self.iter_paragraphs():
            ppr = p.find("w:pPr", self.NS)
            if ppr is None:
                continue

            ps = ppr.find("w:pStyle", self.NS)
            if ps is None:
                continue

            style_id = ps.attrib.get(f"{{{self.NS['w']}}}val")
            if not style_id:
                continue

            style_el = self._find_style_by_id(style_id)
            if style_el is None:
                continue

            name_el = style_el.find("w:name", self.NS)
            if name_el is None:
                continue

            name = name_el.attrib.get(f"{{{self.NS['w']}}}val")
            if name:
                used.add(name)

        return used

    def style_exists(self, style_name: str) -> bool:
        return self._find_style(name=style_name) is not None

    def _get_style_numbering_info(
        self,
        style: ET.Element,
        level: int,
    ) -> tuple[bool, bool, int | None]:
        """
        Zjistí, zda je styl číslovaný, zda je číslování hierarchické
        a jakou má úroveň číslování.

        Args:
            style: XML element stylu.
            level: Úroveň nadpisu.

        Returns:
            Trojici (is_numbered, is_hierarchical, num_level).
        """
        num_id = None
        num_level = None

        for current_style in self._iter_style_chain(style, follow_link=False):
            ppr = current_style.find("w:pPr", self.NS)
            if ppr is None:
                continue

            numpr = ppr.find("w:numPr", self.NS)
            if numpr is None:
                continue

            if num_level is None:
                ilvl_el = numpr.find("w:ilvl", self.NS)
                if ilvl_el is not None:
                    ilvl_val = ilvl_el.attrib.get(f"{{{self.NS['w']}}}val")
                    if ilvl_val is not None:
                        num_level = int(ilvl_val)

            numid_el = numpr.find("w:numId", self.NS)
            if numid_el is not None:
                candidate_num_id = numid_el.attrib.get(f"{{{self.NS['w']}}}val")
                if candidate_num_id:
                    num_id = candidate_num_id
                    break

        if num_level is None:
            num_level = level - 1

        if not num_id:
            return False, False, None

        numbering = self._load("word/numbering.xml")

        abstract_id = None
        for num in numbering.findall(".//w:num", self.NS):
            if num.attrib.get(f"{{{self.NS['w']}}}numId") == num_id:
                abs_el = num.find("w:abstractNumId", self.NS)
                if abs_el is not None:
                    abstract_id = abs_el.attrib.get(f"{{{self.NS['w']}}}val")
                    break

        if abstract_id is None:
            return True, False, num_level

        lvl_text = None
        for absn in numbering.findall(".//w:abstractNum", self.NS):
            if absn.attrib.get(f"{{{self.NS['w']}}}abstractNumId") == abstract_id:
                for lvl_el in absn.findall("w:lvl", self.NS):
                    if lvl_el.attrib.get(f"{{{self.NS['w']}}}ilvl") == str(num_level):
                        txt = lvl_el.find("w:lvlText", self.NS)
                        if txt is not None:
                            lvl_text = txt.attrib.get(f"{{{self.NS['w']}}}val")
                        break

        if not lvl_text:
            return True, False, num_level

        required = [f"%{i}" for i in range(1, level + 1)]
        is_hierarchical = all(r in lvl_text for r in required)

        return True, is_hierarchical, num_level

    def get_heading_numbering_info(
        self,
        level: int,
    ) -> tuple[bool, bool, int | None]:
        styles = self._find_used_heading_styles_by_outline_level(level)

        if not styles:
            styles = self._find_heading_styles_by_outline_level(level)

        if not styles:
            return False, False, None

        for style in styles:
            is_numbered, is_hierarchical, num_level = self._get_style_numbering_info(
                style,
                level,
            )
            if is_numbered:
                return is_numbered, is_hierarchical, num_level

        return False, False, None

    def _paragraph_is_bibliography(self, p: ET.Element) -> bool:
        """
        Ověří, zda odstavec patří do bibliografie.

        Args:
            p: XML element odstavce.

        Returns:
            True pokud odstavec patří do bibliografie, jinak False.
        """
        cur = p
        while True:
            if cur.tag == f"{{{self.NS['w']}}}sdt":
                pr = cur.find("w:sdtPr", self.NS)
                if pr is not None and pr.find("w:bibliography", self.NS) is not None:
                    return True

            parent = self._parent_of(cur)
            if parent is None:
                break
            cur = parent

        ppr = p.find("w:pPr", self.NS)
        if ppr is None:
            return False
        ps = ppr.find("w:pStyle", self.NS)
        if ps is None:
            return False
        sid = (ps.attrib.get(f"{{{self.NS['w']}}}val") or "").strip().lower()

        return sid in {"bibliography", "bibliografie"} or "bibliograf" in sid

    def _iter_rpr_chain_for_style_id(self, style_id: str | None) -> Iterator[ET.Element]:
        """
        Iteruje rPr elementy stylu a jeho nadřazených stylů.

        Args:
            style_id: Identifikátor stylu.

        Yields:
            XML elementy rPr v pořadí dědičnosti.
        """
        if not style_id:
            return

        style = self._find_style_by_id(style_id)
        if style is None:
            return

        for st in self._iter_style_chain(style):
            rpr = st.find("w:rPr", self.NS)
            if rpr is not None:
                yield rpr

    def _iter_paragraph_style_rpr_chain(self, p: ET.Element) -> Iterator[ET.Element]:
        """
        Iteruje rPr řetězec odstavcového stylu.

        Args:
            p: XML element odstavce.

        Yields:
            XML elementy rPr.
        """
        style_id = self.paragraph_style_id(p)

        if style_id:
            yield from self._iter_rpr_chain_for_style_id(style_id)
            return

        for fallback_id in ("Normln", "Normal"):
            style = self._find_style_by_id(fallback_id)
            if style is not None:
                for st in self._iter_style_chain(style):
                    rpr = st.find("w:rPr", self.NS)
                    if rpr is not None:
                        yield rpr
                return

    def _iter_run_style_rpr_chain(self, r: ET.Element) -> Iterator[ET.Element]:
        """
        Iteruje rPr řetězec znakového stylu runu.

        Args:
            r: XML element runu.

        Yields:
            XML elementy rPr.
        """
        rpr = r.find("w:rPr", self.NS)
        if rpr is None:
            return

        rstyle = rpr.find("w:rStyle", self.NS)
        if rstyle is None:
            return

        style_id = rstyle.attrib.get(f"{{{self.NS['w']}}}val")
        yield from self._iter_rpr_chain_for_style_id(style_id)

    def _paragraph_style_rpr_chain(self, p: ET.Element) -> list[ET.Element]:
        """
        Vrátí seznam rPr elementů odstavcového stylu a jeho předků.

        Args:
            p: XML element odstavce.

        Returns:
            Seznam rPr elementů v pořadí dědičnosti.
        """
        return list(self._iter_paragraph_style_rpr_chain(p))

    def _run_style_rpr_chain(self, r: ET.Element) -> list[ET.Element]:
        """
        Vrátí seznam rPr elementů znakového stylu runu a jeho předků.

        Args:
            r: XML element runu.

        Returns:
            Seznam rPr elementů v pořadí dědičnosti.
        """
        return list(self._iter_run_style_rpr_chain(r))
    
    def _first_style_child(self, rpr_chains: list[list[ET.Element]], tag: str) -> ET.Element | None:
        """
        Najde první výskyt zadaného child elementu v řetězcích stylů.

        Args:
            rpr_chains: Seznam řetězců rPr elementů.
            tag: Název hledaného child tagu bez prefixu w:.

        Returns:
            První nalezený XML element, nebo None.
        """
        for chain in rpr_chains:
            for rpr in chain:
                el = rpr.find(f"w:{tag}", self.NS)
                if el is not None:
                    return el
        return None

    def _same_enabled_flag(
        self, run_rpr: ET.Element, rpr_chains: list[list[ET.Element]], tag: str
    ) -> bool:
        """
        Ověří, zda je zapnutí nebo vypnutí vlastnosti stejné jako ve stylu.

        Args:
            run_rpr: rPr element konkrétního runu.
            rpr_chains: Řetězce rPr elementů stylů.
            tag: Název porovnávaného tagu bez prefixu w:.

        Returns:
            True pokud má run stejnou hodnotu vlastnosti jako styl, jinak False.
        """
        run_el = run_rpr.find(f"w:{tag}", self.NS)
        if run_el is None:
            return True

        run_enabled = self._is_enabled(run_el)

        style_el = self._first_style_child(rpr_chains, tag)
        style_enabled = self._is_enabled(style_el) if style_el is not None else False

        return run_enabled == style_enabled


    def _same_size(
        self, run_rpr: ET.Element, rpr_chains: list[list[ET.Element]]
    ) -> bool:
        """
        Ověří, zda je velikost písma runu stejná jako ve stylu.

        Args:
            run_rpr: rPr element konkrétního runu.
            rpr_chains: Řetězce rPr elementů stylů.

        Returns:
            True pokud je velikost stejná jako ve stylu, jinak False.
        """
        run_sz = run_rpr.find("w:sz", self.NS)
        if run_sz is None:
            return True

        style_sz = self._first_style_child(rpr_chains, "sz")
        if style_sz is None:
            return False

        run_val = (run_sz.attrib.get(f"{{{self.NS['w']}}}val") or "").strip()
        style_val = (style_sz.attrib.get(f"{{{self.NS['w']}}}val") or "").strip()

        return bool(run_val and style_val and run_val == style_val)


    def _same_font(
        self, run_rpr: ET.Element, rpr_chains: list[list[ET.Element]]
    ) -> bool:
        """
        Ověří, zda font runu odpovídá fontu definovanému stylem.

        Args:
            run_rpr: rPr element konkrétního runu.
            rpr_chains: Řetězce rPr elementů stylů.

        Returns:
            True pokud font odpovídá stylu, jinak False.
        """
        run_fonts = run_rpr.find("w:rFonts", self.NS)
        if run_fonts is None:
            return True

        attrs = ["ascii", "hAnsi", "cs", "eastAsia"]

        run_values = {
            (run_fonts.attrib.get(f"{{{self.NS['w']}}}{attr}") or "").strip()
            for attr in attrs
        }
        run_values.discard("")

        if not run_values:
            return True

        style_values = set()

        for chain in rpr_chains:
            for rpr in chain:
                style_fonts = rpr.find("w:rFonts", self.NS)
                if style_fonts is None:
                    continue

                for attr in attrs:
                    val = (style_fonts.attrib.get(f"{{{self.NS['w']}}}{attr}") or "").strip()
                    if val:
                        style_values.add(val)

        if not style_values:
            return False

        return run_values.issubset(style_values)

    def _same_color(
        self, run_rpr: ET.Element, rpr_chains: list[list[ET.Element]]
    ) -> bool:
        """
        Ověří, zda je barva runu stejná jako ve stylu.

        Args:
            run_rpr: rPr element konkrétního runu.
            rpr_chains: Řetězce rPr elementů stylů.

        Returns:
            True pokud barva odpovídá stylu, jinak False.
        """
        run_color = run_rpr.find("w:color", self.NS)
        if run_color is None:
            return True

        style_color = self._first_style_child(rpr_chains, "color")
        if style_color is None:
            return False

        run_val = (run_color.attrib.get(f"{{{self.NS['w']}}}val") or "").strip().lower()
        style_val = (style_color.attrib.get(f"{{{self.NS['w']}}}val") or "").strip().lower()

        return bool(run_val and style_val and run_val == style_val)

    def find_inline_formatting(self) -> list[dict]:
        results = []

        for p in self.iter_paragraphs():
            if self._paragraph_is_toc_or_object_list(p):
                continue

            if self._paragraph_is_bibliography(p):
                continue

            paragraph_style_chain = self._paragraph_style_rpr_chain(p)
            paragraph_style = (self.paragraph_style_name(p) or "").lower()

            inside_field = False

            for r in p.findall(".//w:r", self.NS):
                fld = r.find("w:fldChar", self.NS)
                if fld is not None:
                    fld_type = fld.attrib.get(f"{{{self.NS['w']}}}fldCharType")
                    if fld_type == "begin":
                        inside_field = True
                    elif fld_type == "end":
                        inside_field = False
                    continue

                if inside_field:
                    continue

                rpr = r.find("w:rPr", self.NS)
                if rpr is None:
                    continue

                texts = []
                for t in r.findall("w:t", self.NS):
                    if t.text:
                        texts.append(t.text)

                run_text = "".join(texts).strip()
                if not run_text:
                    continue

                if len(run_text) < 3:
                    continue

                if not re.search(r"[A-Za-zÁ-Žá-ž]", run_text):
                    continue

                run_chain = self._run_style_rpr_chain(r)
                rpr_chains = [run_chain, paragraph_style_chain]

                problems = []

                is_heading_like = any(
                    k in paragraph_style
                    for k in ("heading", "nadpis", "title", "subtitle")
                )

                word_count = len(run_text.split())

                if is_heading_like:
                    if (
                        rpr.find("w:b", self.NS) is not None
                        or rpr.find("w:bCs", self.NS) is not None
                    ):
                        if not self._same_enabled_flag(rpr, rpr_chains, "b"):
                            if word_count >= 1 or len(run_text) >= 3:
                                problems.append("bold")

                    if (
                        rpr.find("w:i", self.NS) is not None
                        or rpr.find("w:iCs", self.NS) is not None
                    ):
                        if not self._same_enabled_flag(rpr, rpr_chains, "i"):
                            if word_count >= 1 or len(run_text) >= 3:
                                problems.append("italic")

                if rpr.find("w:sz", self.NS) is not None:
                    if not self._same_size(rpr, rpr_chains):
                        if is_heading_like:
                            if word_count >= 1 or len(run_text) >= 3:
                                problems.append("size")
                        else:
                            if word_count >= 2 or len(run_text) >= 5:
                                problems.append("size")

                if rpr.find("w:rFonts", self.NS) is not None:
                    if not self._same_font(rpr, rpr_chains):
                        if is_heading_like:
                            if word_count >= 1 or len(run_text) >= 3:
                                problems.append("font")
                        else:
                            if word_count >= 2 or len(run_text) >= 5:
                                problems.append("font")

                if rpr.find("w:color", self.NS) is not None:
                    if not self._same_color(rpr, rpr_chains):
                        if is_heading_like:
                            if word_count >= 1 or len(run_text) >= 3:
                                problems.append("color")
                        else:
                            if word_count >= 2 or len(run_text) >= 5:
                                problems.append("color")

                for problem in problems:
                    results.append({"text": run_text, "problem": problem})

        return results
    
    def _is_enabled(self, el: ET.Element | None) -> bool:
        """
        Vyhodnotí, zda je přepínací vlastnost XML elementu zapnutá.

        Args:
            el: XML element vlastnosti.

        Returns:
            True pokud je vlastnost aktivní, jinak False.
        """
        if el is None:
            return False

        val = el.attrib.get(f"{{{self.NS['w']}}}val")
        return val is None or val not in ("0", "false", "False")

    def iter_main_headings(self) -> Iterator[ET.Element]:
        for p in self.iter_paragraphs():
            text = self.paragraph_text(p)
            if not text:
                continue

            style_id = self.paragraph_style_id(p)
            if not style_id:
                continue

            level = self._style_level_from_styles_xml(style_id)
            if level == 1:
                yield p

    def heading_starts_on_new_page(self, p: ET.Element) -> bool:
        style_id = self.paragraph_style_id(p)
        return self.paragraph_has_page_break(p) or self._style_has_page_break(style_id)

    def get_visible_text(self, element: ET.Element) -> str:
        return self.paragraph_text(element)

    def paragraph_is_toc(self, p: ET.Element) -> bool:
        if self._is_inside_toc_sdt(p):
            return True

        ppr = p.find("w:pPr", self.NS)
        if ppr is None:
            return False

        ps = ppr.find("w:pStyle", self.NS)
        if ps is not None:
            val = ps.attrib.get(f"{{{self.NS['w']}}}val", "").lower()
            if "toc" in val or "obsah" in val:
                return True

        sid = (self.paragraph_style_id(p) or "").lower()

        toc_title_style_ids = {"nadpisobsahu", "toctitle"}
        if sid in toc_title_style_ids:
            return True

        for instr in p.findall(".//w:instrText", self.NS):
            if instr.text and instr.text.upper().startswith("TOC"):
                return True

        return False

    def paragraph_is_empty(self, p: ET.Element) -> bool:
        for t in p.findall(".//w:t", self.NS):
            if t.text and t.text.strip():
                return False
        return True

    def paragraph_has_text(self, p: ET.Element) -> bool:
        return not self.paragraph_is_empty(p)

    def paragraph_style_name(self, p: ET.Element) -> str:
        return self.paragraph_style_id(p) or "bez stylu"

    def paragraph_has_spacing_before(self, p: ET.Element) -> bool:
        ppr = p.find("w:pPr", self.NS)
        if ppr is None:
            return False
        spacing = ppr.find("w:spacing", self.NS)
        if spacing is None:
            return False
        before = spacing.attrib.get(f"{{{self.NS['w']}}}before")
        return before is not None and int(before) > 0

    def paragraph_is_generated(self, p: ET.Element) -> bool:
        if self._paragraph_is_generated_by_field(p):
            return True

        if self._paragraph_is_toc_or_object_list(p):
            return True

        return False

    def get_cover_style(self, key: str) -> StyleSpec | None:
        names = self.COVER_STYLES.get(key, [])
        return self.get_style_by_any_name(names, default_alignment="center")

    def paragraph_is_heading(self, p: ET.Element) -> bool:
        return self.paragraph_heading_level(p) is not None

    def _get_style_name_by_id(self, style_id: str | None) -> str | None:
        """
        Vrátí název stylu podle jeho interního ID.

        Args:
            style_id: Interní identifikátor stylu.

        Returns:
            Název stylu, nebo None pokud styl neexistuje.
        """
        style = self._find_style_by_id(style_id)
        if style is None:
            return None

        name_el = style.find("w:name", self.NS)
        if name_el is None:
            return None

        return name_el.attrib.get(f"{{{self.NS['w']}}}val")

    def _style_name_matches_list_level(self, style_id: str | None, level: int) -> bool:
        """
        Ověří, zda název stylu odpovídá seznamu dané úrovně.

        Args:
            style_id: Identifikátor stylu.
            level: Požadovaná úroveň seznamu.

        Returns:
            True pokud styl odpovídá dané úrovni seznamu, jinak False.
        """
        if not style_id:
            return False

        style_name = self._get_style_name_by_id(style_id)
        if not style_name:
            return False

        names = self.LIST_LEVEL_STYLE_NAMES.get(level, set())
        return style_name.strip() in names

    def _numpr_level(self, num_pr: ET.Element | None) -> int | None:
        """
        Vrátí úroveň seznamu z elementu numPr.

        Args:
            num_pr: XML element numPr.

        Returns:
            Úroveň seznamu od 0, nebo None pokud numPr neobsahuje platné číslování.
        """
        if num_pr is None:
            return None

        num_id_el = num_pr.find("w:numId", self.NS)
        if num_id_el is None:
            return None

        num_id_val = (num_id_el.attrib.get(f"{{{self.NS['w']}}}val") or "").strip()
        if not num_id_val.isdigit():
            return None

        if int(num_id_val) <= 0:
            return None

        ilvl_el = num_pr.find("w:ilvl", self.NS)
        if ilvl_el is None:
            return 0

        ilvl_val = (ilvl_el.attrib.get(f"{{{self.NS['w']}}}val") or "").strip()
        if not ilvl_val.isdigit():
            return 0

        return int(ilvl_val)

    def has_list_level(self, level: int) -> bool:
        wanted_ilvl = level - 1

        for p in self._xml.findall(".//w:p", self.NS):
            ppr = p.find("w:pPr", self.NS)
            if ppr is None:
                continue

            if self._paragraph_is_toc_or_object_list(p):
                continue

            if self._paragraph_is_bibliography(p):
                continue

            style_id = self.paragraph_style_id(p)
            style = self._find_style_by_id(style_id) if style_id else None

            direct_heading_level = self._style_heading_level_direct(style)
            if direct_heading_level is not None:
                continue

            para_num_pr = ppr.find("w:numPr", self.NS)
            para_level = self._numpr_level(para_num_pr)
            if para_level is not None and para_level == wanted_ilvl:
                return True

            if style is not None:
                style_num_pr = style.find("w:pPr/w:numPr", self.NS)
                style_level = self._numpr_level(style_num_pr)
                if style_level is not None and style_level == wanted_ilvl:
                    return True

            if self._style_name_matches_list_level(style_id, level):
                return True

        return False
        
    def toc_level_contains_numbers(self, level: int) -> bool | None:
        NUMBER_RE = re.compile(r"^\s*\d+(?:\.\d+)*\.?(?=\D)")

        items = []
        for p in self.iter_paragraphs():
            sid = (self.paragraph_style_id(p) or "").strip().lower()

            if sid not in (f"toc{level}", f"obsah{level}"):
                continue

            txt = (self.paragraph_text(p) or "").strip()
            if txt:
                items.append(txt)

        if not items:
            return None

        return any(NUMBER_RE.match(t) for t in items)
    
    def heading_level_is_numbered(self, level: int) -> bool:
        is_numbered, _, _ = self.get_heading_numbering_info(level)
        return is_numbered

    def section_has_header_text(self, index: int) -> bool:
        return bool(
            self._section_parts_have_content(
                index,
                "header",
                check_text=True,
            )
        )
    
    def _section_is_continuous(self, section_index: int) -> bool | None:
        """
        Ověří, zda je oddíl nastaven jako průběžný.

        Args:
            section_index: Index oddílu v dokumentu.

        Returns:
            True pokud má oddíl typ "continuous", False pokud má jiný typ,
            nebo None pokud oddíl neexistuje či nelze získat jeho vlastnosti.
        """
        if self.section_count() <= section_index:
            return None

        sect_pr = self._section_properties(section_index)
        if sect_pr is None:
            return None

        sect_type = sect_pr.find("w:type", self.NS)
        if sect_type is None:
            return False

        return sect_type.attrib.get(f"{{{self.NS['w']}}}val") == "continuous"

    def second_section_page_number_starts_at_one(self) -> bool | None:
        if self.section_count() < 2:
            return None

        sect_pr = self._section_properties(1)
        if sect_pr is None:
            return None

        pg_num = sect_pr.find("w:pgNumType", self.NS)
        if pg_num is None:
            return False

        start = pg_num.attrib.get(f"{{{self.NS['w']}}}start")
        if start is None:
            return False

        if self._section_is_continuous(1):
            return start in {"1","0"}

        return start == "1"

    def section_footer_is_empty(self, index: int) -> bool | None:
        has_content = self._section_parts_have_content(
            index,
            "footer",
            check_text=True,
            check_drawing=True,
            check_math=True,
        )
        if has_content is None:
            return None

        footer_refs = self._section_part_ref_elements(index, "footer")
        if not footer_refs:
            return True

        return not has_content

    def _section_has_title_page(self, sect_pr: ET.Element) -> bool:
        """
        Ověří, zda má oddíl nastavenou odlišnou první stránku.

        Args:
            sect_pr: XML element vlastností oddílu.

        Returns:
            True pokud oddíl používá title page, jinak False.
        """
        return sect_pr.find("w:titlePg", self.NS) is not None

    def _even_and_odd_headers_enabled(self) -> bool:
        """
        Ověří, zda dokument rozlišuje sudé a liché záhlaví nebo zápatí.

        Returns:
            True pokud jsou pro sudé a liché stránky použité odlišné hlavičky,
            jinak False.
        """
        settings = getattr(self, "settings", None)
        if settings is None:
            return False
        return settings.find("w:evenAndOddHeaders", self.NS) is not None

    def _doc_has_even_and_odd_headers(self) -> bool:
        """
        Ověří, zda má dokument zapnutou volbu „Jiné liché a sudé stránky“.

        Returns:
            True pokud dokument rozlišuje sudé a liché záhlaví nebo zápatí,
            jinak False.
        """
        try:
            settings = self._load("word/settings.xml")
        except KeyError:
            return False

        return settings.find(".//w:evenAndOddHeaders", self.NS) is not None

    def _footer_ref_is_active(self, ref: ET.Element, sect_pr: ET.Element) -> bool:
        """
        Ověří, zda je daná reference zápatí v oddílu skutečně použitá.

        Args:
            ref: XML element reference zápatí.
            sect_pr: XML element vlastností oddílu.

        Returns:
            True pokud je reference pro daný oddíl aktivní, jinak False.
        """
        ref_type = ref.attrib.get(f"{{{self.NS['w']}}}type", "default")

        if ref_type == "default":
            return True

        if ref_type == "first":
            return sect_pr.find("w:titlePg", self.NS) is not None

        if ref_type == "even":
            return self._doc_has_even_and_odd_headers()

        return True

    def _xml_has_page_field(self, xml: ET.Element) -> bool:
        """
        Ověří, zda XML část obsahuje pole PAGE pro číslo stránky.

        Args:
            xml: XML element záhlaví nebo zápatí.

        Returns:
            True pokud část obsahuje pole PAGE, jinak False.
        """
        for fld in xml.findall(".//w:fldSimple", self.NS):
            instr = fld.attrib.get(f"{{{self.NS['w']}}}instr", "") or ""
            if "PAGE" in instr.upper():
                return True

        instr_nodes = xml.findall(".//w:instrText", self.NS)
        has_page_instr = any(("PAGE" in ((n.text or "").upper())) for n in instr_nodes)
        if not has_page_instr:
            return False

        fld_chars = xml.findall(".//w:fldChar", self.NS)
        types = {c.attrib.get(f"{{{self.NS['w']}}}fldCharType") for c in fld_chars}
        return ("begin" in types) and ("end" in types)

    def section_footer_has_page_number(self, index: int) -> bool | None:
        if self.section_count() <= index:
            return None

        for i in range(index, -1, -1):
            sect_pr = self._section_properties(i)
            if sect_pr is None:
                continue

            footer_refs = sect_pr.findall("w:footerReference", self.NS)
            if not footer_refs:
                continue

            for ref in footer_refs:
                if not self._footer_ref_is_active(ref, sect_pr):
                    continue

                r_id = ref.attrib.get(f"{{{self.NS['r']}}}id")
                if not r_id:
                    continue

                part = self._rel_target_path(r_id)
                if not part:
                    continue

                try:
                    xml = self._load(part)
                except KeyError:
                    continue

                if self._xml_has_page_field(xml):
                    return True

            return False

        return False

    def _section_part_ref_map(self, sect: ET.Element, kind: str) -> dict[str, str]:
        """
        Vrátí mapu typů reference na relationship ID pro záhlaví nebo zápatí oddílu.

        Args:
            sect: XML element vlastností oddílu.
            kind: Typ části, například 'header' nebo 'footer'.

        Returns:
            Slovník ve tvaru typ reference -> r:id.
        """
        tag = f"w:{kind}Reference"
        refs = sect.findall(tag, self.NS)

        result: dict[str, str] = {}

        for ref in refs:
            ref_type = ref.attrib.get(f"{{{self.NS['w']}}}type", "default")
            r_id = ref.attrib.get(f"{{{self.NS['r']}}}id")
            if r_id:
                result[ref_type] = r_id

        return result

    def _part_is_linked_to_previous(self, index: int, kind: str) -> bool | None:
        """
        Ověří, zda je záhlaví nebo zápatí oddílu převzaté z předchozího oddílu.

        Args:
            index: Index oddílu.
            kind: Typ části, například 'header' nebo 'footer'.

        Returns:
            True pokud je část propojená s předchozím oddílem, False pokud ne,
            nebo None pokud to nelze určit.
        """
        if index <= 0:
            return None

        sect_prev = self._section_properties(index - 1)
        sect_curr = self._section_properties(index)

        if sect_prev is None or sect_curr is None:
            return None

        map_prev = self._section_part_ref_map(sect_prev, kind)
        map_curr = self._section_part_ref_map(sect_curr, kind)

        required_types = {"default"}

        if self._section_has_title_page(sect_curr):
            required_types.add("first")

        if self._even_and_odd_headers_enabled():
            required_types.add("even")

        for part_type in required_types:
            if part_type not in map_curr:
                return True

        for part_type in required_types:
            if part_type in map_prev and map_prev[part_type] == map_curr[part_type]:
                return True

        return False

    def footer_is_linked_to_previous(self, index: int) -> bool | None:
        return self._part_is_linked_to_previous(index, "footer")

    def header_is_linked_to_previous(self, index: int) -> bool | None:
        return self._part_is_linked_to_previous(index, "header")

    def has_any_table(self) -> bool:
        for obj in self.iter_objects():
            if obj.type == "table":
                return True
        return False

    def has_any_chart(self) -> bool:
        return any(o.type == "chart" for o in self.iter_objects())

    def has_any_equation(self) -> bool:
        return any(o.type == "equation" for o in self.iter_objects())

    def has_list_of_charts_in_section(self, section_index: int) -> bool:
        return self._has_list_in_section(section_index, ["graf", "chart"])

    def has_list_of_equations_in_section(self, section_index: int) -> bool:
        return self._has_list_in_section(section_index, ["rovnice", "equation"])

    def first_chapter_is_first_content_in_section(self, section_index: int) -> bool:
        section = self._section(section_index)

        first_h1 = None
        for el in section:
            if not el.tag.endswith("}p"):
                continue

            style_id = self.paragraph_style_id(el)
            if not style_id:
                continue

            if self._style_level_from_styles_xml(style_id) == 1:
                first_h1 = el
                break

        if first_h1 is None:
            return False

        for el in section:
            if el is first_h1:
                break

            if el.tag.endswith("}p") and self.paragraph_text(el):
                return False

            if el.tag.endswith("}tbl"):
                return False

        return True

    def section_header_is_empty(self, index: int) -> bool | None:
        has_content = self._section_parts_have_content(
            index,
            "header",
            check_text=True,
            check_drawing=True,
            check_math=True,
        )
        if has_content is None:
            return None

        header_refs = self._section_part_ref_elements(index, "header")
        if not header_refs:
            return True

        return not has_content

    def section_page_number_starts_at_one(self, section_index: int) -> bool | None:
        if self.section_count() <= section_index:
            return None

        sect_pr = self._section_properties(section_index)
        if sect_pr is None:
            return None

        pg_num = sect_pr.find("w:pgNumType", self.NS)
        if pg_num is None:
            return False

        start = pg_num.attrib.get(f"{{{self.NS['w']}}}start")
        if start is None:
            return False

        return start == "1"

    def _paragraph_starts_new_section(self, p: ET.Element) -> bool:
        """
        Ověří, zda odstavec začíná nový oddíl.

        Args:
            p: XML element odstavce.

        Returns:
            True pokud odstavec obsahuje vlastnosti oddílu, jinak False.
        """
        pPr = p.find("w:pPr", self.NS)
        if pPr is None:
            return False

        return pPr.find("w:sectPr", self.NS) is not None

    def iter_section_blocks(self, section_index: int) -> Iterator[ET.Element]:
        current_section = 0

        for p in self.iter_paragraphs():
            if self._paragraph_starts_new_section(p):
                if current_section > section_index:
                    return
                current_section += 1

            if current_section == section_index:
                yield p

    def iter_toc_paragraphs(self) -> Iterator[ET.Element]:
        for p in self.iter_paragraphs():
            style = self.paragraph_style_name(p).lower()

            if style.startswith(("toc", "obsah")):
                yield p
                continue

            for hl in p.findall(".//w:hyperlink", self.NS):
                anchor = hl.attrib.get(f"{{{self.NS['w']}}}anchor", "")
                if anchor.startswith("_Toc"):
                    yield p
                    break

    def normalize_heading_text(self, text: str) -> str:
        text = text.lower()

        text = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s*", "", text)

        text = re.sub(r"\s*\d+\s*$", "", text)

        text = re.sub(r"\t+", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def iter_toc_items(self) -> list[dict[str, str]]:
        items = []
        inside_toc = False

        for p in self.iter_paragraphs():
            for instr in p.findall(".//w:instrText", self.NS):
                if instr.text and instr.text.strip().upper().startswith("TOC"):
                    inside_toc = True
                    break

            if not inside_toc:
                continue

            if p.find("w:pPr/w:sectPr", self.NS) is not None:
                break

            ppr = p.find("w:pPr", self.NS)
            if ppr is None:
                continue

            ps = ppr.find("w:pStyle", self.NS)
            if ps is None:
                continue

            style = (ps.attrib.get(f"{{{self.NS['w']}}}val") or "").lower()
            if not (style.startswith("toc") or style.startswith("obsah")):
                continue

            hl = p.find("w:hyperlink", self.NS)

            if hl is not None:
                anchor = hl.attrib.get(f"{{{self.NS['w']}}}anchor", "")
                text = self.normalize_heading_text(self._visible_text(hl))
            else:
                anchor = ""
                text = self.normalize_heading_text(self._visible_text(p))

            if not text:
                continue

            items.append({"anchor": anchor, "text": text})

        return items


    def toc_missing_used_headings(
        self, max_level: int = 3
    ) -> tuple[bool | None, list[str]]:
        toc_items = self.iter_toc_items()
        if not toc_items:
            return (None, [])

        toc_texts = {
            self.normalize_heading_text(x["text"]) for x in toc_items if x.get("text")
        }
        toc_texts = {t for t in toc_texts if t}

        used_texts = set()
        for text, lvl in self.iter_headings():
            if 1 <= lvl <= max_level:
                t = self.normalize_heading_text(text)
                if t:
                    used_texts.add(t)

        missing = sorted(used_texts - toc_texts)
        return ((len(missing) == 0), missing)

    def _iter_toc_body_blocks(self, section_index: int) -> list[ET.Element]:
        """
        Vrátí bloky patřící do těla obsahu v daném oddílu.

        Args:
            section_index: Index oddílu, ve kterém se má obsah hledat.

        Returns:
            Seznam bloků patřících do obsahu.
        """
        section = self._section(section_index)
        if not section:
            return []

        toc_started = False
        blocks = []

        for el in section:
            tag = el.tag.split("}")[-1]

            if not toc_started and tag == "p":
                instr_parts = []
                for instr in el.findall(".//w:instrText", self.NS):
                    if instr.text:
                        instr_parts.append(instr.text)

                instr_joined = " ".join(instr_parts).upper()

                if "TOC" in instr_joined:
                    toc_started = True
                    blocks.append(el)
                    continue

            if not toc_started:
                continue

            if tag == "p":
                ppr = el.find("w:pPr", self.NS)
                if ppr is not None and ppr.find("w:sectPr", self.NS) is not None:
                    break

            blocks.append(el)

            if tag == "p":
                sid = (self.paragraph_style_id(el) or "").lower()
                lvl = self._style_level_from_styles_xml(
                    self.paragraph_style_id(el) or ""
                )
                if lvl == 1 and sid not in {
                    "nadpisobsahu",
                    "toctitle",
                    "obsah1",
                    "obsah2",
                    "obsah3",
                }:
                    blocks.pop()
                    break

        return blocks

    def _has_field_hyperlink(self, p) -> bool:
        for instr in p.findall(".//w:instrText", self.NS):
            text = (instr.text or "").upper()
            if "HYPERLINK" in text and "\\L" in text:
                return True
        return False


    def _has_pageref(self, p) -> bool:
        for instr in p.findall(".//w:instrText", self.NS):
            if "PAGEREF" in (instr.text or "").upper():
                return True
        return False


    def _extract_field_anchor(self, p) -> str | None:
        for instr in p.findall(".//w:instrText", self.NS):
            text = instr.text or ""
            match = re.search(
                r'HYPERLINK\s+\\l\s+"([^"]+)"',
                text,
                re.IGNORECASE,
            )
            if match:
                return match.group(1)
        return None


    def _norm_toc_text(self, text: str) -> str:
        text = normalize_spaces(text).strip().lower()
        text = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", text)
        text = re.sub(r"\s*\d+\s*$", "", text)
        return text.strip()


    def _get_toc_entry_info(self, p) -> dict[str, str | bool | None]:
        link = p.find("w:hyperlink", self.NS)

        if link is not None:
            return {
                "kind": "hyperlink",
                "text": normalize_spaces(self._visible_text(link)).strip(),
                "anchor": link.attrib.get(f"{{{self.NS['w']}}}anchor"),
                "has_pageref": self._has_pageref(link),
            }

        return {
            "kind": "field" if self._has_field_hyperlink(p) or self._has_pageref(p) else "manual",
            "text": normalize_spaces(self._visible_text(p)).strip(),
            "anchor": self._extract_field_anchor(p),
            "has_pageref": self._has_pageref(p),
        }

    def _paragraph_plain_text(self, p: ET.Element) -> str:
        """
        Vrátí viditelný text odstavce bez textu uvnitř vložených objektů
        (drawing, pict, textbox, AlternateContent).

        Args:
            p: XML element odstavce.

        Returns:
            Text odstavce po normalizaci mezer.
        """
        parts: list[str] = []

        for child in p:
            tag = child.tag

            if tag == f"{{{self.NS['w']}}}r":
                if child.find("w:drawing", self.NS) is not None:
                    continue

                if child.find("w:pict", self.NS) is not None:
                    continue

                rpr = child.find("w:rPr", self.NS)
                if rpr is not None and rpr.find("w:webHidden", self.NS) is not None:
                    continue

                for t in child.findall("w:t", self.NS):
                    if t.text:
                        parts.append(t.text)

            elif tag == f"{{{self.NS['w']}}}hyperlink":
                for r in child.findall("w:r", self.NS):
                    rpr = r.find("w:rPr", self.NS)
                    if rpr is not None and rpr.find("w:webHidden", self.NS) is not None:
                        continue

                    if r.find("w:drawing", self.NS) is not None:
                        continue

                    if r.find("w:pict", self.NS) is not None:
                        continue

                    for t in r.findall("w:t", self.NS):
                        if t.text:
                            parts.append(t.text)

        return normalize_spaces("".join(parts)).strip()

    def _find_bookmark_paragraph(self, bookmark_name: str) -> ET.Element | None:
        """
        Najde odstavec, ve kterém se nachází bookmark se zadaným názvem.

        Args:
            bookmark_name: Název bookmarku.

        Returns:
            Odstavec obsahující daný bookmark, nebo None.
        """
        for p in self._xml.findall(".//w:body/w:p", self.NS):
            for bm in p.findall(".//w:bookmarkStart", self.NS):
                name = bm.attrib.get(f"{{{self.NS['w']}}}name")
                if name == bookmark_name:
                    return p

        return None

    def get_toc_illegal_content_errors(
        self,
    ) -> tuple[bool, list[TocIllegalContentError], str | None]:
        toc_section = None
        for i in range(self.section_count()):
            if self.has_toc_in_section(i):
                toc_section = i
                break

        if toc_section is None:
            return False, [], "no_toc"

        toc_sdt = None
        for el in self._section(toc_section):
            if el.tag.endswith("}sdt"):
                pr = el.find("w:sdtPr", self.NS)
                if pr is not None and pr.find("w:docPartObj", self.NS) is not None:
                    toc_sdt = el.find("w:sdtContent", self.NS)
                    break

        heading_by_bookmark: dict[str, str] = {}

        for p in self._xml.findall(".//w:body/w:p", self.NS):
            sid = self.paragraph_style_id(p)
            if not sid:
                continue

            lvl = self._style_level_from_styles_xml(sid)
            if lvl is None or not (1 <= lvl <= 3):
                continue

            if self._find_ancestor(p, f"{{{self.NS['w']}}}txbxContent") is not None:
                continue

            heading_text = self._paragraph_plain_text(p)
            if not heading_text:
                continue

            if re.match(
                r"^\s*(obrázek|figure|graf|chart|tabulka|table)\b",
                heading_text,
                re.IGNORECASE,
            ):
                continue

            for bm in p.findall(".//w:bookmarkStart", self.NS):
                name = bm.attrib.get(f"{{{self.NS['w']}}}name")
                if name:
                    heading_by_bookmark[name] = heading_text

        errors: list[TocIllegalContentError] = []

        if toc_sdt is not None:
            toc_elements = list(toc_sdt)
        else:
            toc_elements = list(self._iter_toc_body_blocks(toc_section))

        for el in toc_elements:
            if el.tag.endswith("}tbl"):
                errors.append(TocIllegalContentError("toc_has_table", {}))
                continue

            if el.findall(".//w:drawing", self.NS):
                errors.append(TocIllegalContentError("toc_has_drawing", {}))
                continue

            if el.findall(".//m:oMath", self.NS) or el.findall(
                ".//m:oMathPara", self.NS
            ):
                errors.append(TocIllegalContentError("toc_has_equation", {}))
                continue

            if not el.tag.endswith("}p"):
                errors.append(TocIllegalContentError("toc_has_forbidden_object", {}))
                continue

            full_text = normalize_spaces(self._visible_text(el)).strip()
            if not full_text:
                continue

            style_id = (self.paragraph_style_id(el) or "").lower()
            if full_text.lower() == "obsah" or style_id == "nadpisobsahu":
                continue

            entry = self._get_toc_entry_info(el)

            text = str(entry.get("text") or "").strip()
            anchor_raw = entry.get("anchor")
            has_pageref = bool(entry.get("has_pageref"))
            kind = str(entry.get("kind") or "")
            anchor = str(anchor_raw) if anchor_raw else None

            if not text:
                continue

            if kind == "manual":
                errors.append(TocIllegalContentError("manual_text", {"text": text}))
                continue

            if not has_pageref:
                errors.append(TocIllegalContentError("missing_page_ref", {"text": text}))
                continue

            if not anchor:
                errors.append(TocIllegalContentError("missing_anchor", {"text": text}))
                continue

            clean_text = self._norm_toc_text(text)

            if clean_text in self.ALLOWED_BIBLIOGRAPHY_TOC_ITEMS:
                if self.has_bibliography():
                    continue

            matched_heading_text = heading_by_bookmark.get(anchor)

            if not matched_heading_text:
                bookmark_p = self._find_bookmark_paragraph(anchor)
                if bookmark_p is not None:
                    matched_heading_text = self._paragraph_plain_text(bookmark_p)

            if not matched_heading_text:
                errors.append(
                    TocIllegalContentError("missing_matching_heading", {"text": text})
                )
                continue

            clean_heading = self._norm_toc_text(matched_heading_text)

            if clean_text != clean_heading:
                errors.append(
                    TocIllegalContentError(
                        "modified_toc_item",
                        {
                            "text": text,
                            "expected": matched_heading_text,
                        },
                    )
                )
                continue

        return True, errors, None

    def has_toc(self) -> bool:
        for instr in self._xml.findall(".//w:instrText", self.NS):
            if instr.text and "TOC" in instr.text.upper():
                return True
        return False

    def _image_name_by_rid(self, rid: str) -> str | None:
        """
        Vrátí název obrázku podle relationship ID.

        Args:
            rid: Relationship ID, například 'rId14'.

        Returns:
            Název souboru obrázku nebo None.
        """
        target = self._rels.get(rid)
        if not target:
            return None

        return target.split("/")[-1]

    def iter_image_bytes(self) -> Iterator[tuple[str | None, bytes]]:
        for obj in self.iter_objects():
            if obj.type != "image":
                continue

            element = obj.element
            for rid in self._object_image_rids(element):
                img = self._get_image_bytes(rid)
                if img:
                    yield self._image_name_by_rid(rid), img

    def _neighbor_paragraphs_same_parent(
        self,
        element: ET.Element,
    ) -> tuple[ET.Element | None, ET.Element | None]:
        """
        Najde nejbližší odstavce před a za elementem ve stejném rodiči.

        Args:
            element: XML element, kolem kterého se hledají sousední odstavce.

        Returns:
            Dvojice (předchozí odstavec, následující odstavec), kde chybějící
            hodnota je None.
        """
        parent = self._parent_map.get(element)
        if parent is None:
            return None, None

        children = list(parent)
        try:
            idx = children.index(element)
        except ValueError:
            return None, None

        before = None
        after = None
        p_tag = f"{{{self.NS['w']}}}p"

        for i in range(idx - 1, -1, -1):
            if children[i].tag == p_tag:
                before = children[i]
                break

        for i in range(idx + 1, len(children)):
            if children[i].tag == p_tag:
                after = children[i]
                break

        return before, after

    def _try_caption_paragraph(
        self,
        p: ET.Element,
        *,
        source: str,
        only_seq: bool = False,
    ) -> dict | None:
        """
        Zkusí vyhodnotit odstavec jako titulek objektu.

        Args:
            p: Odstavec, který se má zkontrolovat.
            source: Popis místa, odkud odstavec pochází.
            only_seq: Pokud je True, uznávají se jen titulky
                založené na SEQ poli.

        Returns:
            Slovník s informacemi o titulku, nebo None pokud
            odstavec titulku neodpovídá.
        """
        p_text = (self.paragraph_text(p) or "").strip()
        seq_label = self._paragraph_has_seq_caption(p)

        if seq_label:
            result = self._make_result(p, seq_label, True)
            return result

        if not only_seq:
            st_name = self._style_name_of(p)
            manual = self._is_manual_caption_text(p, st_name)
            if manual:
                result = self._make_result(p, None, False)
                return result

        return None

    def _find_object_caption(
        self,
        obj: DocumentObject,
        *,
        only_seq: bool = False,
        include_textbox: bool = True,
        include_neighbors: bool = True,
    ) -> dict | None:
        """
        Najde titulek objektu v textovém poli nebo v okolních odstavcích.

        Args:
            obj: Objekt, ke kterému se hledá titulek.
            only_seq: Pokud je True, uznávají se jen titulky
                založené na SEQ poli.
            include_textbox: Pokud je True, prohledávají se
                i textová pole objektu.
            include_neighbors: Pokud je True, prohledávají se
                i sousední odstavce.

        Returns:
            Slovník s informacemi o titulku, nebo None pokud
            nebyl nalezen.
        """
        element = obj.element
        if element is None:
            return None

        obj_type = (obj.type or "").lower()

        if obj_type in ("image", "chart", "table") and include_textbox:
            drawing = obj.drawing

            if drawing is not None:
                txbxs = drawing.findall(".//w:txbxContent", self.NS)

                for i, txbx in enumerate(txbxs, 1):
                    ps = txbx.findall(".//w:p", self.NS)
                    for p in ps:
                        result = self._try_caption_paragraph(
                            p,
                            source=f"drawing.txbx[{i}]",
                            only_seq=only_seq,
                        )
                        if result is not None:
                            return result

            txbxs = element.findall(".//w:txbxContent", self.NS)

            for i, txbx in enumerate(txbxs, 1):
                ps = txbx.findall(".//w:p", self.NS)
                for p in ps:
                    result = self._try_caption_paragraph(
                        p,
                        source=f"element.txbx[{i}]",
                        only_seq=only_seq,
                    )
                    if result is not None:
                        return result

        if include_neighbors:
            before, after = self._neighbor_paragraphs_same_parent(element)

            if after is not None:
                result = self._try_caption_paragraph(
                    after,
                    source="same_parent.after",
                    only_seq=only_seq,
                )
                if result is not None:
                    return result

            if before is not None:
                result = self._try_caption_paragraph(
                    before,
                    source="same_parent.before",
                    only_seq=only_seq,
                )
                if result is not None:
                    return result

            before, after = self._body_neighbor_paragraphs(element)

            if after is not None:
                result = self._try_caption_paragraph(
                    after,
                    source="body.after",
                    only_seq=only_seq,
                )
                if result is not None:
                    return result

            if before is not None:
                result = self._try_caption_paragraph(
                    before,
                    source="body.before",
                    only_seq=only_seq,
                )
                if result is not None:
                    return result

        host_p = (
            element
            if element.tag == f"{{{self.NS['w']}}}p"
            else self._find_ancestor(element, f"{{{self.NS['w']}}}p")
        )

        if host_p is not None:
            result = self._try_caption_paragraph(
                host_p,
                source="host_paragraph",
                only_seq=only_seq,
            )
            if result is not None:
                return result

        return None

    def _find_ancestor(
        self,
        element: ET.Element,
        tag_name: str,
    ) -> ET.Element | None:
        """
        Najde nejbližšího předka se zadaným tagem.

        Args:
            element: Výchozí XML element.
            tag_name: Hledaný tag včetně namespace.

        Returns:
            Odpovídající předek, nebo None.
        """
        current: ET.Element | None = element
        depth = 0

        while current is not None:
            if current.tag == tag_name:
                return current

            current = self._parent_map.get(current)
            depth += 1

        return None
    
    def _get_textbox_content_ancestor(self, element: ET.Element) -> ET.Element | None:
        """
        Vrátí nadřazený element textového pole.

        Args:
            element: XML element objektu nebo titulku.

        Returns:
            Element w:txbxContent, nebo None.
        """
        return self._find_ancestor(element, f"{{{self.NS['w']}}}txbxContent")

    def _get_group_from_drawing(self, drawing: ET.Element | None) -> ET.Element | None:
        """
        Najde group element uvnitř drawingu.

        Args:
            drawing: XML element drawingu.

        Returns:
            Nalezený group element (`wpg:wgp` nebo `v:group`),
            jinak None.
        """
        if drawing is None:
            return None

        wpg_ns = self.NS.get("wpg")
        if wpg_ns:
            group = drawing.find(f".//{{{wpg_ns}}}wgp")
            if group is not None:
                return group

        v_ns = self.NS.get("v")
        if v_ns:
            group = drawing.find(f".//{{{v_ns}}}group")
            if group is not None:
                return group

        return None


    def _get_group_ancestor(self, element: ET.Element) -> ET.Element | None:
        """
        Vrátí nejbližší nadřazený group element.

        Args:
            element: XML element objektu nebo titulku.

        Returns:
            Group element, nebo None.
        """
        if element is None:
            return None

        wpg_ns = self.NS.get("wpg")
        if wpg_ns:
            group = self._find_ancestor(element, f"{{{wpg_ns}}}wgp")
            if group is not None:
                return group

        v_ns = self.NS.get("v")
        if v_ns:
            group = self._find_ancestor(element, f"{{{v_ns}}}group")
            if group is not None:
                return group

        return None

    def _get_alternate_content_ancestor(self, el: ET.Element | None) -> ET.Element | None:
        """
        Najde nejbližšího předka typu mc:AlternateContent.

        Args:
            el: Výchozí XML element.

        Returns:
            Nalezený ancestor typu AlternateContent, jinak None.
        """
        if el is None:
            return None

        current = el
        depth = 0
        wanted = f"{{{self.NS['mc']}}}AlternateContent"

        while current is not None:
            if current.tag == wanted:
                return current
            current = self._parent_map.get(current)
            depth += 1

        return None


    def object_has_caption(
        self,
        obj: DocumentObject,
        expected_labels: str | Iterable[str] | None = None,
    ) -> bool:
        if expected_labels is None:
            return False

        obj_type = (obj.type or "").lower()

        if obj_type == "table":
            found = self._find_object_caption(
                obj,
                only_seq=False,
                include_textbox=False,
                include_neighbors=True,
            )
        elif obj_type in ("image", "chart"):
            found = self._find_object_caption(
                obj,
                only_seq=False,
                include_textbox=True,
                include_neighbors=False,
            )
        else:
            return False

        if found is None:
            return False

        caption_el = found.get("paragraph")
        if caption_el is None:
            return False

        if obj_type == "table":
            return True

        if obj_type in ("image", "chart"):
            obj_group = self._get_group_ancestor(obj.element)
            if obj_group is None:
                obj_group = self._get_group_from_drawing(obj.drawing)

            caption_group = self._get_group_ancestor(caption_el)

            if (
                obj_group is not None
                and caption_group is not None
                and obj_group is caption_group
            ):
                return True

            obj_alt = self._get_alternate_content_ancestor(obj.element)
            if obj_alt is None:
                obj_alt = self._get_alternate_content_ancestor(obj.drawing)

            caption_alt = self._get_alternate_content_ancestor(caption_el)

            if (
                obj_alt is not None
                and caption_alt is not None
                and obj_alt is caption_alt
            ):
                return True

            if obj.element is not None:
                obj_txbx = self._get_textbox_content_ancestor(obj.element)
                caption_txbx = self._get_textbox_content_ancestor(caption_el)

                if (
                    obj_txbx is not None
                    and caption_txbx is not None
                    and obj_txbx is caption_txbx
                ):
                    return True

            return False

        return False

    def get_object_caption_text(
        self,
        obj: DocumentObject,
        *,
        accept_manual: bool = False,
    ) -> str | None:
        """
        Vrátí textovou část titulku objektu bez návěští a čísla.

        Args:
            obj: Objekt, jehož titulek se má získat.
            accept_manual: Určuje, zda se mají uznat i ručně vytvořené titulky.

        Returns:
            Text popisu titulku, nebo None pokud titulek nebyl nalezen.
        """
        found = self.get_object_caption_info(obj, accept_manual=accept_manual)
        if found is None:
            return None

        text = found.text
        if not text:
            return None

        text = re.sub(
            r"^(Obrázek|Tabulka|Graf|Figure|Table|Chart)\s+\d+\s*[:\-]?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        return text or None

    def _body_neighbor_paragraphs(
        self, element: ET.Element, max_steps: int = 30
    ) -> tuple[ET.Element | None, ET.Element | None]:
        """
        Vrátí nejbližší vhodné odstavce před a za zadaným elementem v těle dokumentu.

        Args:
            element: Element, kolem kterého se mají hledat sousední odstavce.
            max_steps: Maximální počet bloků prohledaných na každou stranu.

        Returns:
            Dvojici (předchozí odstavec, následující odstavec),
            kde každý prvek může být None.
        """
        body = self._xml.find("w:body", self.NS)
        if body is None:
            return (None, None)

        children = list(body)
        try:
            idx = children.index(element)
        except ValueError:
            return (None, None)

        WP = f"{{{self.NS['w']}}}p"

        def is_candidate_p(node: ET.Element) -> bool:
            if node.tag != WP:
                return False

            has_seq = bool(self._paragraph_has_seq_caption(node))

            has_text = bool((self.paragraph_text(node) or "").strip())

            return has_seq or has_text

        before = None
        steps = 0
        for j in range(idx - 1, -1, -1):
            steps += 1
            if steps > max_steps:
                break
            node = children[j]
            if is_candidate_p(node):
                before = node
                break

        after = None
        steps = 0
        for j in range(idx + 1, len(children)):
            steps += 1
            if steps > max_steps:
                break
            node = children[j]
            if is_candidate_p(node):
                after = node
                break

        return (before, after)

    def _style_name_of(self, p: ET.Element) -> str:
        """
        Vrátí název stylu odstavce v malých písmenech.

        Args:
            p: XML element odstavce.

        Returns:
            Název stylu, nebo prázdný řetězec pokud styl není dostupný.
        """
        sid = self.paragraph_style_id(p)
        name = self._get_style_name_by_id(sid)
        return (name or "").lower()

    def _is_manual_caption_text(self, p: ET.Element, style_name: str) -> bool:
        """
        Ověří, zda odstavec vypadá jako ručně zapsaný titulek objektu.

        Args:
            p: XML element odstavce.
            style_name: Název stylu odstavce.

        Returns:
            True pokud text odpovídá ručnímu titulku objektu, jinak False.
        """
        txt = (self.paragraph_text(p) or "").strip().lower()
        if not txt:
            return False

        style = (style_name or "").strip().lower()

        allowed_prefixes = (
            "obrázek",
            "figure",
            "graf",
            "chart",
            "tabulka",
            "table",
        )

        if "caption" in style or "titulek" in style:
            return txt.startswith(allowed_prefixes)

        return False

    def _make_result(
        self,
        p: ET.Element | None,
        label: str | None,
        is_seq: bool,
    ) -> dict[str, ET.Element | str | bool | None]:
        """
        Vrátí slovník s informacemi o nalezeném titulku objektu.

        Args:
            p: Odstavec titulku.
            label: Návěští titulku.
            is_seq: Informace, zda byl titulek rozpoznán přes SEQ pole.

        Returns:
            Slovník s informacemi o nalezeném titulku.
        """
        text = self.paragraph_text(p) if p is not None else None
        return {
            "paragraph": p,
            "label": label,
            "is_seq": is_seq,
            "text": text,
        }

    def get_object_caption_info(
        self,
        obj: DocumentObject,
        *,
        accept_manual: bool = False,
    ) -> ObjectCaptionInfo | None:
        found = self._find_object_caption(
            obj,
            only_seq=not accept_manual,
            include_textbox=True,
            include_neighbors=False,
        )

        if found is None and obj.type in ("image", "chart"):
            found = self._find_object_caption(
                obj,
                only_seq=not accept_manual,
                include_textbox=False,
                include_neighbors=True,
            )

        if found is None and obj.type in ("image", "chart"):
            found = self._find_object_caption(
                obj,
                only_seq=not accept_manual,
                include_textbox=True,
                include_neighbors=True,
            )

        if found is None and obj.type == "table":
            found = self._find_object_caption(
                obj,
                only_seq=not accept_manual,
                include_textbox=False,
                include_neighbors=True,
            )

        if found is None:
            return None

        is_seq = found.get("is_seq", False)

        return ObjectCaptionInfo(
            label=found.get("label"),
            is_seq=is_seq,
            text=found.get("text"),
            is_manual=not is_seq,
        )

    def _is_object_ref(self, name: str) -> bool:
        """
        Ověří, zda název reference pravděpodobně odkazuje na objekt.

        Args:
            name: Název reference nebo bookmarku.

        Returns:
            True pokud název odpovídá odkazu na obrázek, tabulku nebo graf,
            jinak False.
        """
        low = name.lower()
        return (
            low.startswith("_ref")
            or "figure" in low
            or "obrázek" in low
            or "tabulka" in low
            or "graf" in low
        )

    def iter_object_crossref_ids(self) -> set[str]:
        refs: set[str] = set()

        for fld in self._xml.findall(".//w:fldSimple", self.NS):
            instr_text = fld.attrib.get(f"{{{self.NS['w']}}}instr", "")
            if "REF" not in instr_text.upper():
                continue

            parts = instr_text.split()
            if len(parts) < 2:
                continue

            ref = parts[1]
            if self._is_object_ref(ref):
                refs.add(ref)

        for instr_el in self._xml.findall(".//w:instrText", self.NS):
            if not instr_el.text or "REF" not in instr_el.text.upper():
                continue

            parts = instr_el.text.split()
            if len(parts) < 2:
                continue

            ref = parts[1]
            if self._is_object_ref(ref):
                refs.add(ref)

        return refs

    def get_object_caption_ref_ids(self, obj: DocumentObject) -> set[str]:
        element = obj.element

        caption_p = self._paragraph_after(element) or self._paragraph_before(element)
        if caption_p is None:
            return set()

        ids: set[str] = set()

        for bm in caption_p.findall(".//w:bookmarkStart", self.NS):
            name = bm.attrib.get(f"{{{self.NS['w']}}}name")
            if name:
                ids.add(name)

        return ids

    def get_bibliography_style(self) -> StyleSpec | None:
        return self.get_style_by_any_name(
            ["Bibliography", "Bibliografie"], default_alignment="start"
        )

    def get_content_heading_style(self) -> StyleSpec | None:
        return self.get_style_by_any_name(
            ["Content Heading", "TOC Heading", "Nadpis obsahu"],
            default_alignment="start",
        )

    def section_missing_styles(
        self, section_index: int, styles: set[str]
    ) -> tuple[bool, list[str]]:
        if section_index >= len(self._sections):
            return (False, sorted(styles))

        found = set()

        for el in self._sections[section_index]:
            if not isinstance(el.tag, str) or not el.tag.endswith("}p"):
                continue

            style_id = self.paragraph_style_id(el)
            if not style_id:
                continue

            lvl = self._style_level_from_styles_xml(style_id)
            if lvl == 1:
                break

            if style_id in styles:
                found.add(style_id)

        missing = sorted(styles - found)
        return (len(missing) == 0, missing)

    def paragraph_heading_level(self, p: ET.Element) -> int | None:
        sid = self.paragraph_style_id(p)
        if sid:
            lvl = self._style_level_from_styles_xml(sid)
            if lvl is not None:
                return lvl

        for rstyle in p.findall(".//w:rStyle", self.NS):
            char_style_id = rstyle.attrib.get(f"{{{self.NS['w']}}}val")
            if not char_style_id:
                continue

            char_style = self._find_style_by_id(char_style_id)
            if char_style is None:
                continue

            link = char_style.find("w:link", self.NS)
            if link is None:
                continue

            linked_para_style_id = link.attrib.get(f"{{{self.NS['w']}}}val")
            if not linked_para_style_id:
                continue

            lvl = self._style_level_from_styles_xml(linked_para_style_id)
            if lvl is not None:
                return lvl

        return None
    
    def paragraph_has_numbering(self, p: ET.Element) -> bool:
        ppr = p.find("w:pPr", self.NS)
        if ppr is None:
            return False

        numpr = ppr.find("w:numPr", self.NS)
        if numpr is not None:
            num_id_el = numpr.find("w:numId", self.NS)
            if num_id_el is None:
                return False

            num_id = (num_id_el.attrib.get(f"{{{self.NS['w']}}}val") or "").strip()

            if not num_id.isdigit():
                return False

            return int(num_id) > 0

        sid = self.paragraph_style_id(p)
        if not sid:
            return False

        style = self._find_style_by_id(sid)
        if style is None:
            return False

        numpr_style = style.find("w:pPr/w:numPr", self.NS)
        if numpr_style is None:
            return False

        num_id_el = numpr_style.find("w:numId", self.NS)
        if num_id_el is None:
            return False

        num_id = (num_id_el.attrib.get(f"{{{self.NS['w']}}}val") or "").strip()

        if not num_id.isdigit():
            return False

        return int(num_id) > 0

    def _paragraph_plain_text_without_xrefs(self, p: ET.Element) -> str:
        """
        Vrátí text odstavce bez výsledků křížových odkazů.

        Args:
            p: XML element odstavce.

        Returns:
            Text odstavce bez zobrazených hodnot polí REF a PAGEREF.
        """
        REF_INSTR_RE = re.compile(r"\b(REF|PAGEREF)\b", re.IGNORECASE)
        parts: list[str] = []
        inside_field = False
        instr_buf: list[str] = []
        skip_field_result = False

        for r in p.findall(".//w:r", self.NS):
            instr_el = r.find("w:instrText", self.NS)
            if instr_el is not None:
                if inside_field:
                    instr_buf.append(instr_el.text or "")
                continue

            fld = r.find("w:fldChar", self.NS)
            if fld is not None:
                t = fld.attrib.get(f"{{{self.NS['w']}}}fldCharType", "")
                if t == "begin":
                    inside_field = True
                    instr_buf = []
                    skip_field_result = False
                    continue

                if t == "separate":
                    instr = " ".join(x.strip() for x in instr_buf if x).strip()
                    if REF_INSTR_RE.search(instr):
                        skip_field_result = True
                    continue

                if t == "end":
                    inside_field = False
                    instr_buf = []
                    skip_field_result = False
                    continue

            if inside_field and skip_field_result:
                continue

            for t_el in r.findall("w:t", self.NS):
                if t_el.text:
                    parts.append(t_el.text)

        txt = "".join(parts)
        txt = normalize_spaces(txt)
        return txt

    def _strip_dangling_xref_words(self, s: str) -> str:
        """
        Odstraní z konce textu osamocená slova navazující na křížový odkaz.

        Args:
            s: Vstupní text.

        Returns:
            Očištěný text bez zbytků typu 'viz' nebo 'see'.
        """
        XREF_DANGLING_RE = re.compile(r"(?i)\b(viz|viz\.|vizte|see)\b[\s:–-]*$")
        if not s:
            return ""

        s = re.sub(r"\s{2,}", " ", s).strip()
        s = XREF_DANGLING_RE.sub("", s).strip()

        s = re.sub(r"[ \t]+([.,;:])", r"\1", s).strip()
        s = re.sub(r"[.,;:]\s*$", "", s).strip()

        return s

    def get_text_of_section(self, section_index: int) -> str:
        parts: list[str] = []

        for block in self.iter_section_blocks(section_index):
            if block.tag != f"{{{self.NS['w']}}}p":
                continue

            plain = self._paragraph_plain_text_without_xrefs(block)
            plain = self._strip_dangling_xref_words(plain)

            if self._paragraph_is_generated_by_field(block) and not plain:
                continue

            label = self._paragraph_has_seq_caption(block)
            if label and label.strip().lower() in (
                "obrázek",
                "tabulka",
                "graf",
                "figure",
                "table",
                "chart",
            ):
                continue

            style_id = self.paragraph_style_id(block)
            if style_id and style_id.strip().lower() in (
                "caption",
                "popisek",
                "titulek",
            ):
                continue

            if plain:
                parts.append(plain)

        return "\n".join(parts)

    def get_full_text(self) -> str:
        parts: list[str] = []
        for p in self._xml.findall(".//w:body/w:p", self.NS):
            text = self._paragraph_plain_text_without_xrefs(p)
            text = self._strip_dangling_xref_words(text)
            if text:
                parts.append(text)
        return "\n".join(parts)
