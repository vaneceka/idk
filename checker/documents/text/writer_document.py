import io
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import unquote

from assignment.text.text_assignment_model import StyleSpec
from documents.text.text_document import TextDocument
from models.text_models import (
    BibliographySource,
    DocumentObject,
    ObjectCaptionInfo,
    TocIllegalContentError,
)
from utils.text_utils import normalize_spaces, replace_nbsp
from utils.xml_debug import dump_zip_structure_pretty


class WriterDocument(TextDocument):
    NS = {
        "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
        "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
        "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
        "loext": "urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0",
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
        "xlink": "http://www.w3.org/1999/xlink",
        "mathml": "http://www.w3.org/1998/Math/MathML",
    }

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
            "List 1",
            "List Bullet",
            "List Number",
            "Numbering",
            "Numbering 1",
            "Seznam",
            "Seznam 1",
        },
        2: {
            "List 2",
            "List Bullet 2",
            "List Number 2",
            "Numbering 2",
            "Seznam 2",
        },
    }

    _CIT_MARK_NUM_RE = re.compile(r"\(?\s*(\d+)\s*\)?")

    def __init__(self, path: str):
        self.path = path
        self._zip = zipfile.ZipFile(path)
        self.content = self._load("content.xml")
        self.styles = self._load("styles.xml")
        self._style_by_name = self._build_style_map()
        self._parent_map = self._build_parent_map()

    def _build_parent_map(self) -> dict[ET.Element, ET.Element]:
        return {
            child: parent
            for parent in self.content.iter()
            for child in list(parent)
        }

    def _load(self, name: str) -> ET.Element:
        """
        Načte XML soubor z archivu dokumentu.

        Args:
            name: Vnitřní cesta k souboru v archivu.

        Returns:
            Kořenový XML element načteného souboru.
        """
        with self._zip.open(name) as f:
            return ET.fromstring(f.read())

    def save_debug_xml(self, out_dir: str | Path = "debug") -> None:
        dump_zip_structure_pretty(self.path, Path(out_dir) / "writer")

    def _build_style_map(self) -> dict[str, ET.Element]:
        """
        Vytvoří mapu stylů podle interního i zobrazovaného názvu.

        Returns:
            Slovník mapující názvy stylů na jejich XML elementy.
        """
        out = {}
        for root in (self.styles, self.content):
            for st in root.findall(".//style:style", self.NS):
                internal = st.attrib.get(f"{{{self.NS['style']}}}name", "")
                display = st.attrib.get(f"{{{self.NS['style']}}}display-name", "")
                if internal:
                    out[internal.strip()] = st
                if display:
                    out[display.strip()] = st
        return out

    def _find_style(self, name: str | None) -> ET.Element | None:
        """
        Najde styl podle názvu.

        Args:
            name: Interní nebo zobrazovaný název stylu.

        Returns:
            XML element stylu, nebo None pokud styl neexistuje.
        """
        if not name:
            return None
        return self._style_by_name.get(name.strip())

    def _iter_style_chain(self, style_el: ET.Element | None) -> Iterator[ET.Element]:
        """
        Iteruje styl a jeho rodičovské styly.

        Args:
            style_el: Výchozí XML element stylu.

        Yields:
            XML elementy stylu od aktuálního po nadřazené styly.
        """
        visited: set[int] = set()

        while style_el is not None and id(style_el) not in visited:
            visited.add(id(style_el))
            yield style_el

            parent = style_el.attrib.get(f"{{{self.NS['style']}}}parent-style-name")
            if not parent:
                break

            style_el = self._find_style(parent)

    def _resolve_style_attr(
        self, style_el: ET.Element | None, child_tag: str, attr_qname: str
    ) -> str | None:
        """
        Najde hodnotu atributu ve stylu nebo v jeho rodičích.

        Args:
            style_el: Výchozí XML element stylu.
            child_tag: Cesta k podřízenému elementu stylu.
            attr_qname: Plně kvalifikovaný název atributu.

        Returns:
            Hodnota atributu, nebo None pokud není nalezena.
        """
        for st in self._iter_style_chain(style_el):
            child = st.find(child_tag, self.NS)
            if child is not None:
                val = child.attrib.get(attr_qname)
                if val is not None:
                    return val
        return None

    def _resolve_paragraph_prop(
        self, style_el: ET.Element | None, attr_qname: str
    ) -> str | None:
        """
        Vrátí hodnotu vlastnosti odstavce ze stylu nebo jeho rodičů.

        Args:
            style_el: XML element stylu.
            attr_qname: Plně kvalifikovaný název atributu.

        Returns:
            Hodnota atributu, nebo None pokud není nalezena.
        """
        return self._resolve_style_attr(
            style_el, "style:paragraph-properties", attr_qname
        )

    def _resolve_alignment(
        self, style: ET.Element, default_alignment: str | None = None
    ) -> str | None:
        """
        Zjistí výsledné zarovnání odstavce pro styl.

        Args:
            style: XML element stylu.
            default_alignment: Výchozí zarovnání použité při absenci explicitní hodnoty.

        Returns:
            Hodnota zarovnání, nebo None pokud ji nelze určit.
        """
        alignment = (
            self._resolve_paragraph_prop(style, f"{{{self.NS['fo']}}}text-align")
            or default_alignment
        )

        if alignment and alignment.lower() == "justify":
            return "both"

        return alignment

    def _resolve_color(self, style: ET.Element) -> str:
        """
        Zjistí výslednou barvu textu pro styl.

        Args:
            style: XML element stylu.

        Returns:
            Barva ve formátu hex bez znaku #.
        """
        color_val = self._resolve_text_prop(style, f"{{{self.NS['fo']}}}color")
        if color_val is None:
            return "000000"
        return color_val.lstrip("#").upper()

    def _resolve_all_caps(self, style: ET.Element) -> bool:
        """
        Ověří, zda styl používá psaní textu verzálkami.

        Args:
            style: XML element stylu.

        Returns:
            True pokud styl nastavuje uppercase, jinak False.
        """
        text_transform = self._resolve_text_prop(
            style,
            f"{{{self.NS['fo']}}}text-transform",
        )
        return text_transform == "uppercase"

    def _resolve_page_break_before(self, style: ET.Element) -> bool | None:
        """
        Zjistí, zda styl vynucuje zalomení stránky před odstavcem.

        Args:
            style: XML element stylu.

        Returns:
            True pokud styl obsahuje zalomení stránky před odstavcem,
            False pokud je tato vlastnost explicitně nastavena jinak,
            nebo None pokud není určena.
        """
        para_props = style.find("style:paragraph-properties", self.NS)
        if para_props is None:
            return None

        br = para_props.attrib.get(f"{{{self.NS['fo']}}}break-before")
        if br == "page":
            return True
        if br is not None:
            return False
        return None

    def _resolve_num_level(self, style: ET.Element) -> int | None:
        """
        Zjistí úroveň osnovy definovanou u stylu.

        Args:
            style: XML element stylu.

        Returns:
            Úroveň osnovy převedenou na číslování od nuly,
            nebo None pokud ji nelze určit.
        """
        outline_level = style.attrib.get(f"{{{self.NS['style']}}}default-outline-level")
        if not outline_level:
            return None

        try:
            return int(outline_level) - 1
        except ValueError:
            return None

    def _resolve_line_height(self, style_el: ET.Element | None) -> float | None:
        """
        Vrátí výšku řádku definovanou ve stylu.

        Args:
            style_el: XML element stylu.

        Returns:
            Výšku řádku jako číslo, nebo None pokud ji nelze určit.
        """
        val = self._resolve_paragraph_prop(style_el, f"{{{self.NS['fo']}}}line-height")

        if not val:
            return None

        val = val.strip().lower()

        if val.endswith("%"):
            try:
                return float(val[:-1]) / 100
            except ValueError:
                return None

        if val.endswith("pt"):
            try:
                return float(val[:-2])
            except ValueError:
                return None

        return None

    def _resolve_text_prop(
        self, style_el: ET.Element | None, attr_qname: str
    ) -> str | None:
        """
        Vrátí hodnotu textové vlastnosti ze stylu nebo jeho rodičů.

        Args:
            style_el: XML element stylu.
            attr_qname: Plně kvalifikovaný název atributu.

        Returns:
            Hodnota atributu, nebo None pokud není nalezena.
        """
        return self._resolve_style_attr(style_el, "style:text-properties", attr_qname)

    def _resolve_bold(self, style_el: ET.Element | None) -> bool:
        """
        Ověří, zda má styl nastavené tučné písmo.

        Args:
            style_el: XML element stylu.

        Returns:
            True pokud je tučné písmo aktivní, jinak False.
        """
        for st in self._iter_style_chain(style_el):
            tp = st.find("style:text-properties", self.NS)
            if tp is None:
                continue

            fw = tp.attrib.get(f"{{{self.NS['fo']}}}font-weight")
            if fw is not None:
                return fw.lower() == "bold"

            fsn = tp.attrib.get(f"{{{self.NS['style']}}}font-style-name")
            if fsn is not None and "bold" in fsn.lower():
                return True

        return False

    def _parse_font_size_pt(self, value: str | None) -> float | None:
        """
        Převede textovou velikost písma na hodnotu v bodech.

        Args:
            value: Textová hodnota velikosti písma.

        Returns:
            Velikost písma v bodech, nebo None pokud ji nelze převést.
        """
        if not value:
            return None

        s = value.strip().lower().replace(",", ".")

        if s.endswith("pt"):
            s = s[:-2].strip()

        try:
            return float(s)
        except ValueError:
            return None

    def _resolve_font_size_pt(self, style_el: ET.Element) -> float | None:
        """
        Vrátí velikost písma stylu v bodech.

        Args:
            style_el: XML element stylu.

        Returns:
            Velikost písma v bodech, nebo None pokud ji nelze zjistit.
        """
        val = self._resolve_text_prop(style_el, f"{{{self.NS['fo']}}}font-size")
        return self._parse_font_size_pt(val)

    def _cm_to_twips(self, cm: str) -> int | None:
        """
        Převede délku v centimetrech na twips.

        Args:
            cm: Délka zapsaná v centimetrech.

        Returns:
            Hodnota v twips, nebo None pokud převod selže.
        """
        try:
            return int(float(cm.replace("cm", "")) * 567)
        except Exception:
            return None

    def _resolve_font_name(self, style_el: ET.Element) -> str | None:
        """
        Vrátí název písma definovaný ve stylu.

        Args:
            style_el: XML element stylu.

        Returns:
            Název písma, nebo None pokud není dostupný.
        """
        val = self._resolve_text_prop(style_el, f"{{{self.NS['style']}}}font-name")

        if not val:
            return None

        val = re.sub(r"\d+$", "", val)

        return val.strip()

    def _resolve_tabs(
        self, style_el: ET.Element | None
    ) -> list[tuple[str, int]] | None:
        """
        Vrátí tabulátory definované ve stylu nebo jeho rodičích.

        Args:
            style_el: XML element stylu.

        Returns:
            Seznam dvojic (typ tabulátoru, pozice v twips), nebo None pokud nejsou definované.
        """
        for st in self._iter_style_chain(style_el):
            para = st.find("style:paragraph-properties", self.NS)
            if para is None:
                continue

            tabs_el = para.find("style:tab-stops", self.NS)
            if tabs_el is None:
                continue

            tabs = []
            for t in tabs_el.findall("style:tab-stop", self.NS):
                pos = t.attrib.get(f"{{{self.NS['style']}}}position")
                typ = t.attrib.get(f"{{{self.NS['style']}}}type", "left")

                if pos and pos.endswith("cm"):
                    cm = float(pos.replace("cm", ""))
                    twips = int(round(cm * 567))
                    tabs.append((typ, twips))

            return tabs if tabs else None

        return None

    def _build_style_spec(
        self, style: ET.Element, *, default_alignment: str | None = None
    ) -> StyleSpec:
        """
        Sestaví objekt StyleSpec z XML reprezentace stylu.

        Args:
            style: XML element stylu.
            default_alignment: Výchozí zarovnání použité při absenci explicitní hodnoty.

        Returns:
            Styl převedený do struktury StyleSpec.
        """
        font = self._resolve_font_name(style)
        size = self._resolve_font_size_pt(style)
        bold = self._resolve_bold(style)

        fs = self._resolve_text_prop(style, f"{{{self.NS['fo']}}}font-style")
        italic = fs is not None and fs.lower() == "italic"

        alignment = self._resolve_alignment(style, default_alignment)
        color = self._resolve_color(style)
        all_caps = self._resolve_all_caps(style)
        based_on = style.attrib.get(f"{{{self.NS['style']}}}parent-style-name")

        mt = self._resolve_paragraph_prop(style, f"{{{self.NS['fo']}}}margin-top")
        space_before = self._cm_to_twips(mt) if mt else None

        tabs = self._resolve_tabs(style)
        page_break_before = self._resolve_page_break_before(style)
        num_level = self._resolve_num_level(style)
        line_height = self._resolve_line_height(style)

        return StyleSpec(
            name=style.attrib.get(f"{{{self.NS['style']}}}name") or "",
            font=font,
            size=size,
            bold=bold,
            italic=italic,
            alignment=alignment,
            color=color,
            allCaps=all_caps,
            basedOn=based_on,
            spaceBefore=space_before,
            tabs=tabs,
            pageBreakBefore=page_break_before,
            numLevel=num_level,
            lineHeight=line_height,
        )

    def get_style_by_any_name(
        self, names: list[str], *, default_alignment: str | None = None
    ) -> StyleSpec | None:
        for name in names:
            style = self._find_style(name)
            if style is not None:
                return self._build_style_spec(
                    style, default_alignment=default_alignment
                )
        return None

    def get_doc_default_font_size(self) -> int | None:
        for root in (self.styles, self.content):
            default = root.find(".//style:default-style", self.NS)
            if default is None:
                continue

            tp = default.find("style:text-properties", self.NS)
            if tp is None:
                continue

            fs = tp.attrib.get(f"{{{self.NS['fo']}}}font-size")
            parsed = self._parse_font_size_pt(fs)
            if parsed is not None:
                return int(round(parsed))

        return None

    def get_cover_style(self, key: str) -> StyleSpec | None:
        names = self.COVER_STYLES.get(key, [])
        return self.get_style_by_any_name(names, default_alignment="center")

    def get_style_parent(self, style_name: str) -> str | None:
        style_el = self._find_style(style_name)
        if style_el is None:
            return None

        parent = style_el.attrib.get(f"{{{self.NS['style']}}}parent-style-name")

        return parent

    def get_used_paragraph_styles(self) -> set[str]:
        used = set()

        for p in self.content.findall(".//text:p", self.NS):
            style_name = p.attrib.get(f"{{{self.NS['text']}}}style-name")
            if style_name:
                used.add(style_name)

        return used

    def style_exists(self, style_name: str) -> bool:
        return self._find_style(style_name) is not None

    def get_custom_style(self, style_name: str) -> StyleSpec | None:
        return self.get_style_by_any_name([style_name])

    def _style_outline_level(self, style: ET.Element | None) -> str | None:
        """
        Vrátí úroveň osnovy definovanou ve stylu nebo jeho rodičích.

        Args:
            style: XML element stylu.

        Returns:
            Hodnota outline level, nebo None pokud není definovaná.
        """
        for st in self._iter_style_chain(style):
            outline = st.attrib.get(f"{{{self.NS['style']}}}default-outline-level")
            if outline:
                return outline
        return None

    def _find_heading_styles_by_outline_level(self, level: int) -> list[ET.Element]:
        """
        Najde všechny styly odstavců s danou úrovní osnovy.

        Args:
            level: Hledaná úroveň nadpisu.

        Returns:
            Seznam stylů odpovídajících zadané úrovni osnovy.
        """
        wanted = str(level)
        out: list[ET.Element] = []
        seen_ids: set[int] = set()

        for root in (self.styles, self.content):
            for st in root.findall(".//style:style", self.NS):
                family = st.attrib.get(f"{{{self.NS['style']}}}family")
                if family != "paragraph":
                    continue

                if self._style_outline_level(st) == wanted and id(st) not in seen_ids:
                    out.append(st)
                    seen_ids.add(id(st))

        return out

    def _iter_heading_elements(self) -> Iterator[ET.Element]:
        """
        Iteruje všechny elementy nadpisů v dokumentu.

        Yields:
            XML elementy nadpisů.
        """
        yield from self.content.findall(".//text:h", self.NS)

    def _heading_level(self, h: ET.Element) -> int | None:
        """
        Vrátí úroveň nadpisu z jeho XML atributu.

        Args:
            h: XML element nadpisu.

        Returns:
            Úroveň nadpisu, nebo None pokud ji nelze určit.
        """
        lvl = h.attrib.get(f"{{{self.NS['text']}}}outline-level")
        if not lvl:
            return None
        try:
            return int(lvl)
        except ValueError:
            return None

    def _heading_text(self, h: ET.Element) -> str:
        """
        Vrátí text nadpisu bez okolních mezer.

        Args:
            h: XML element nadpisu.

        Returns:
            Text nadpisu.
        """
        return (self.paragraph_text(h) or "").strip()

    def _find_used_heading_styles_by_outline_level(
        self, level: int
    ) -> list[ET.Element]:
        """
        Najde styly skutečně použitých nadpisů na zadané úrovni.

        Args:
            level: Hledaná úroveň nadpisu.

        Returns:
            Seznam použitých stylů odpovídajících zadané úrovni.
        """
        out: list[ET.Element] = []
        seen_names: set[str] = set()

        for h in self._iter_heading_elements():
            if self._heading_level(h) != level:
                continue

            if not self._heading_text(h):
                continue

            style_name = h.attrib.get(f"{{{self.NS['text']}}}style-name")
            if not style_name or style_name in seen_names:
                continue

            st = self._find_style(style_name)
            if st is None:
                continue

            family = st.attrib.get(f"{{{self.NS['style']}}}family")
            if family != "paragraph":
                continue

            out.append(st)
            seen_names.add(style_name)

        return out

    def get_heading_styles(self, level: int) -> list[StyleSpec]:
        styles = self._find_used_heading_styles_by_outline_level(level)

        if not styles:
            styles = self._find_heading_styles_by_outline_level(level)

        return [
            self._build_style_spec(style, default_alignment="start") for style in styles
        ]

    def _find_outline_style(self) -> ET.Element | None:
        """
        Najde definici outline stylu v dokumentu.

        Returns:
            XML element outline stylu, nebo None pokud není k dispozici.
        """
        roots = [self.styles, self.content]

        for root in roots:
            if root is None:
                continue

            outline = root.find(".//text:outline-style", self.NS)
            if outline is not None:
                return outline

            outline = root.find(f"{{{self.NS['text']}}}outline-style")
            if outline is not None:
                return outline

        return None

    def get_heading_numbering_info(self, level: int) -> tuple[bool, bool, int | None]:
        outline = self._find_outline_style()
        if outline is None:
            return False, False, None

        lvl = outline.find(
            f".//{{{self.NS['text']}}}outline-level-style[@{{{self.NS['text']}}}level='{level}']"
        )
        if lvl is None:
            return False, False, None

        num_format = lvl.attrib.get(f"{{{self.NS['style']}}}num-format")
        if not num_format:
            return False, False, None

        num_list = (
            lvl.attrib.get(f"{{{self.NS['loext']}}}num-list-format")
            or lvl.attrib.get(f"{{{self.NS['text']}}}num-list-format")
            or ""
        )

        required = [f"%{i}%" for i in range(1, level + 1)]
        is_hierarchical = True
        for r in required:
            if r not in num_list:
                is_hierarchical = False
                break

        return True, is_hierarchical, level - 1

    def iter_headings(self) -> list[tuple[str, int]]:
        items = []

        for h in self._iter_heading_elements():
            txt = self._heading_text(h)
            if not txt:
                continue

            level = self._heading_level(h)
            if level is None:
                continue

            items.append((txt, level))

        return items

    def _writer_is_auto_style_name(self, style_name: str | None, family: str) -> bool:
        """
        Určí, zda název stylu odpovídá automaticky generovanému stylu Writeru.

        Args:
            style_name: Název stylu.
            family: Očekávaná rodina stylu ("paragraph" nebo "text").

        Returns:
            True, pokud jde o automatický styl dané rodiny, jinak False.
        """
        if not style_name:
            return False

        if family == "paragraph":
            return bool(re.fullmatch(r"P\d+", style_name))

        if family == "text":
            return bool(re.fullmatch(r"T\d+", style_name))

        return False


    def _writer_get_style_attr(
        self, style: ET.Element | None, ns_name: str, attr_name: str
    ) -> str:
        """
        Vrátí hodnotu atributu z elementu style:text-properties.

        Args:
            style: XML element stylu.
            ns_name: Klíč namespace v self.NS.
            attr_name: Název atributu bez namespace.

        Returns:
            Hodnota atributu nebo prázdný řetězec, pokud atribut neexistuje.
        """
        if style is None:
            return ""

        tp = style.find("style:text-properties", self.NS)
        if tp is None:
            return ""

        ns_uri = self.NS[ns_name]
        return (tp.attrib.get(f"{{{ns_uri}}}{attr_name}") or "").strip()


    def _writer_get_style_attr_lower(
        self, style: ET.Element | None, ns_name: str, attr_name: str
    ) -> str:
        """
        Vrátí hodnotu atributu stylu převedenou na malá písmena.

        Args:
            style: XML element stylu.
            ns_name: Klíč namespace v self.NS.
            attr_name: Název atributu bez namespace.

        Returns:
            Hodnota atributu převedená na lowercase nebo prázdný řetězec.
        """
        return self._writer_get_style_attr(style, ns_name, attr_name).lower()


    def _writer_find_style_with_family(
        self, style_name: str | None, family: str
    ) -> ET.Element | None:
        """
        Najde styl podle názvu a ověří jeho rodinu.

        Args:
            style_name: Název stylu.
            family: Očekávaná rodina stylu.

        Returns:
            XML element stylu, pokud existuje a má očekávanou rodinu, jinak None.
        """
        if not style_name:
            return None

        style = self._find_style(style_name)
        if style is None:
            return None

        style_family = style.attrib.get(f"{{{self.NS['style']}}}family")
        if style_family != family:
            return None

        return style


    def _writer_parent_style(self, style: ET.Element | None, family: str) -> ET.Element | None:
        """
        Vrátí nadřazený styl daného stylu v rámci zadané rodiny.

        Args:
            style: XML element stylu.
            family: Očekávaná rodina parent stylu.

        Returns:
            XML element parent stylu nebo None.
        """
        if style is None:
            return None

        parent_name = style.attrib.get(f"{{{self.NS['style']}}}parent-style-name")
        return self._writer_find_style_with_family(parent_name, family)


    def _writer_style_differs(
        self,
        style: ET.Element | None,
        parent_style: ET.Element | None,
        ns_name: str,
        attr_name: str,
    ) -> bool:
        """
        Ověří, zda se hodnota atributu stylu liší od parent stylu.

        Args:
            style: Aktuální styl.
            parent_style: Nadřazený styl.
            ns_name: Klíč namespace v self.NS.
            attr_name: Název atributu bez namespace.

        Returns:
            True, pokud styl atribut má a jeho hodnota se liší od parent stylu.
        """
        cur = self._writer_get_style_attr_lower(style, ns_name, attr_name)
        par = self._writer_get_style_attr_lower(parent_style, ns_name, attr_name)
        return bool(cur and cur != par)


    def _writer_has_font_override(
        self, style: ET.Element | None, parent_style: ET.Element | None
    ) -> bool:
        """
        Ověří, zda styl přepisuje font oproti parent stylu.

        Args:
            style: Aktuální styl.
            parent_style: Nadřazený styl.

        Returns:
            True, pokud se některý fontový atribut liší od parent stylu.
        """
        font_keys = [
            ("style", "font-name"),
            ("style", "font-name-asian"),
            ("style", "font-name-complex"),
            ("fo", "font-family"),
        ]

        for ns_name, key in font_keys:
            if self._writer_style_differs(style, parent_style, ns_name, key):
                return True

        return False


    def _writer_has_meaningful_color_override(
        self, style: ET.Element | None, parent_style: ET.Element | None
    ) -> bool:
        """
        Ověří, zda styl přepisuje barvu smysluplným způsobem.

        Ignoruje běžné výchozí hodnoty jako černá nebo auto.

        Args:
            style: Aktuální styl.
            parent_style: Nadřazený styl.

        Returns:
            True, pokud je nastavena jiná než výchozí barva a liší se od parent stylu.
        """
        cur_color = self._writer_get_style_attr_lower(style, "fo", "color")
        par_color = self._writer_get_style_attr_lower(parent_style, "fo", "color")

        if not cur_color:
            return False

        if cur_color in ("#000000", "black", "auto"):
            return False

        return cur_color != par_color


    def _writer_direct_text_overrides(self, style: ET.Element | None, family: str) -> list[str]:
        """
        Vrátí seznam přímých textových přepisů stylu oproti jeho parent stylu.

        Sleduje tučné písmo, kurzívu, velikost písma, font a barvu.

        Args:
            style: XML element stylu.
            family: Rodina stylu ("paragraph" nebo "text").

        Returns:
            Seznam názvů problémů bez duplicit.
        """
        if style is None:
            return []

        tp = style.find("style:text-properties", self.NS)
        if tp is None:
            return []

        parent_style = self._writer_parent_style(style, family)
        problems = []

        cur_weight = self._writer_get_style_attr_lower(style, "fo", "font-weight")
        par_weight = self._writer_get_style_attr_lower(parent_style, "fo", "font-weight")
        if cur_weight and cur_weight != par_weight:
            if cur_weight in ("bold", "normal"):
                problems.append("tučné písmo")

        cur_style = self._writer_get_style_attr_lower(style, "fo", "font-style")
        par_style = self._writer_get_style_attr_lower(parent_style, "fo", "font-style")
        if cur_style and cur_style != par_style:
            if cur_style in ("italic", "normal"):
                problems.append("kurzíva")

        cur_size = self._writer_get_style_attr_lower(style, "fo", "font-size")
        par_size = self._writer_get_style_attr_lower(parent_style, "fo", "font-size")
        if cur_size and cur_size != par_size:
            problems.append("změna velikosti písma")

        if self._writer_has_font_override(style, parent_style):
            problems.append("změna fontu")

        if self._writer_has_meaningful_color_override(style, parent_style):
            problems.append("změna barvy")

        return list(dict.fromkeys(problems))


    def find_inline_formatting(self) -> list[dict]:
        results = []

        paragraphs = self.content.findall(".//text:p", self.NS) + self.content.findall(".//text:h", self.NS)

        for p in paragraphs:
            paragraph_text = "".join(p.itertext()).strip()
            if not paragraph_text:
                continue

            if len(paragraph_text) < 3:
                continue

            if not re.search(r"[A-Za-zÁ-Žá-ž]", paragraph_text):
                continue

            word_count = len(paragraph_text.split())

            p_style_name = p.attrib.get(f"{{{self.NS['text']}}}style-name")
            p_style = self._writer_find_style_with_family(p_style_name, "paragraph")

            if self._writer_is_auto_style_name(p_style_name, "paragraph"):
                p_problems = self._writer_direct_text_overrides(p_style, "paragraph")
                for problem in p_problems:
                    if p.tag.endswith("h"):
                        if word_count >= 1 or len(paragraph_text) >= 3:
                            results.append({"text": paragraph_text, "problem": problem})
                    else:
                        if word_count >= 2 or len(paragraph_text) >= 5:
                            results.append({"text": paragraph_text, "problem": problem})

            for span in p.findall(".//text:span", self.NS):
                span_text = "".join(span.itertext()).strip()
                if not span_text:
                    continue

                if len(span_text) < 3:
                    continue

                if not re.search(r"[A-Za-zÁ-Žá-ž]", span_text):
                    continue

                span_word_count = len(span_text.split())

                span_style_name = span.attrib.get(f"{{{self.NS['text']}}}style-name")
                span_style = self._writer_find_style_with_family(span_style_name, "text")

                if not self._writer_is_auto_style_name(span_style_name, "text"):
                    continue

                span_problems = self._writer_direct_text_overrides(span_style, "text")
                for problem in span_problems:
                    if problem in ("tučné písmo", "kurzíva"):
                        if span_word_count >= 3 or len(span_text) >= 20:
                            results.append({"text": span_text, "problem": problem})
                    else:
                        if p.tag.endswith("h"):
                            if span_word_count >= 1 or len(span_text) >= 3:
                                results.append({"text": span_text, "problem": problem})
                        else:
                            if span_word_count >= 2 or len(span_text) >= 5:
                                results.append({"text": span_text, "problem": problem})

        return results


    def iter_main_headings(self) -> Iterator[ET.Element]:
        for h in self._iter_heading_elements():
            if self._heading_level(h) == 1:
                yield h

    def heading_starts_on_new_page(self, h: ET.Element) -> bool:
        style_name = h.attrib.get(f"{{{self.NS['text']}}}style-name")
        if not style_name:
            return False

        style = self._find_style(style_name)
        if style is None:
            return False

        for st in self._iter_style_chain(style):
            pprops = st.find("style:paragraph-properties", self.NS)
            if (
                pprops is not None
                and pprops.attrib.get(f"{{{self.NS['fo']}}}break-before") == "page"
            ):
                return True

        return False

    def get_visible_text(self, element: ET.Element) -> str:
        return "".join(element.itertext()).strip()

    def paragraph_text_raw(self, p: ET.Element) -> str:
        parts = []

        for el in p.iter():
            if el.text:
                parts.append(el.text)

            if el.tag == f"{{{self.NS['text']}}}s":
                c = el.attrib.get(f"{{{self.NS['text']}}}c")
                parts.append(" " * (int(c) if c and c.isdigit() else 1))

            elif el.tag == f"{{{self.NS['text']}}}tab":
                parts.append("\t")

        return "".join(parts)

    def paragraph_is_toc(self, p: ET.Element) -> bool:
        style = p.attrib.get(f"{{{self.NS['text']}}}style-name", "").lower()
        return "toc" in style or "obsah" in style

    def iter_paragraphs(self) -> Iterator[ET.Element]:
        parent_map = {c: p for p in self.content.iter() for c in list(p)}

        elements = []
        for el in self.content.iter():
            if el.tag in {
                f"{{{self.NS['text']}}}p",
                f"{{{self.NS['text']}}}h",
            }:
                elements.append(el)

        skip_next_empty = 0

        for el in elements:
            cur = el
            inside_table = False

            while cur in parent_map:
                cur = parent_map[cur]
                tag = cur.tag.split("}")[-1]

                if tag in ("table", "frame", "text-box"):
                    inside_table = True
                    break

            if inside_table:
                skip_next_empty = 2
                continue

            text = self.paragraph_text(el).strip()

            if skip_next_empty > 0 and not text:
                skip_next_empty -= 1
                continue

            if text:
                skip_next_empty = 0

            yield el

    def _odt_walk_text(self, node: ET.Element, out: list[str]) -> None:
        """
        Rekurzivně projde textový XML uzel a uloží jeho textový obsah do seznamu.

        Zohledňuje i speciální ODT prvky pro mezery, tabulátory a zalomení řádku.

        Args:
            node: XML uzel, který se má projít.
            out: Výstupní seznam částí textu.
        """
        if node.text:
            out.append(node.text)

        for ch in list(node):
            if ch.tag == f"{{{self.NS['text']}}}s":
                c = ch.attrib.get(f"{{{self.NS['text']}}}c")
                out.append(" " * (int(c) if c and c.isdigit() else 1))

            elif ch.tag == f"{{{self.NS['text']}}}tab":
                out.append("\t")

            elif ch.tag == f"{{{self.NS['text']}}}line-break":
                out.append("\n")

            else:
                self._odt_walk_text(ch, out)

            if ch.tail:
                out.append(ch.tail)

    def _odt_text_with_specials(self, el: ET.Element) -> str:
        """
        Vrátí text elementu včetně speciálních ODT znaků.

        Args:
            el: XML element, ze kterého se má získat text.

        Returns:
            Text elementu včetně mezer, tabulátorů a zalomení řádků.
        """
        out: list[str] = []
        self._odt_walk_text(el, out)
        return "".join(out)

    def paragraph_is_empty(self, p: ET.Element) -> bool:
        return not self.paragraph_text(p).strip()

    def paragraph_has_text(self, p: ET.Element) -> bool:
        return bool(self.paragraph_text(p).strip())

    def paragraph_text(self, p: ET.Element) -> str:
        return self._odt_text_with_specials(p).strip()

    def paragraph_style_name(self, p: ET.Element) -> str:
        return p.attrib.get(f"{{{self.NS['text']}}}style-name", "bez stylu")

    def paragraph_has_spacing_before(self, p: ET.Element) -> bool:
        style_name = self.paragraph_style_name(p)
        style = self._find_style(style_name)
        if style is None:
            return False

        pp = style.find("style:paragraph-properties", self.NS)
        if pp is None:
            return False

        mt = pp.attrib.get(f"{{{self.NS['fo']}}}margin-top")
        return mt is not None and mt != "0cm"

    def paragraph_is_generated(self, p) -> bool:
        return False

    def paragraph_has_page_break(self, p) -> bool:
        return False

    def _style_display_or_name(self, style_name: str | None) -> str | None:
        """
        Vrátí zobrazovaný název stylu nebo jeho interní název.

        Args:
            style_name: Název stylu pro vyhledání.

        Returns:
            Display name stylu, případně interní name, nebo None pokud styl neexistuje.
        """
        st = self._find_style(style_name)
        if st is None:
            return None

        display = st.attrib.get(f"{{{self.NS['style']}}}display-name")
        if display:
            return display.strip()

        name = st.attrib.get(f"{{{self.NS['style']}}}name")
        if name:
            return name.strip()

        return None

    def _resolved_style_display_or_name(self, style_name: str | None) -> str | None:
        """
        Vrátí zobrazovaný název stylu nebo název prvního stylu v dědičné řadě.

        Args:
            style_name: Výchozí název stylu.

        Returns:
            Display name nebo name nalezené ve stylu či jeho rodičích,
            případně původní název pokud styl nelze dohledat.
        """
        current = style_name.strip() if style_name else None
        if not current:
            return None

        st = self._find_style(current)
        if st is None:
            return current

        for chain_style in self._iter_style_chain(st):
            display = chain_style.attrib.get(f"{{{self.NS['style']}}}display-name")
            if display:
                return display.strip()

            name = chain_style.attrib.get(f"{{{self.NS['style']}}}name")
            if name:
                return name.strip()

        return current

    def has_list_level(self, level: int) -> bool:
        wanted = self.LIST_LEVEL_STYLE_NAMES.get(level, set())

        for p in self.iter_paragraphs():
            style_name = p.attrib.get(f"{{{self.NS['text']}}}style-name")
            effective_name = self._resolved_style_display_or_name(style_name)

            if effective_name and effective_name in wanted:
                return True

        return False

    def get_normal_style(self) -> StyleSpec | None:
        style = self._find_style("Standard")
        if style is None:
            return None

        return self._build_style_spec(style)

    def toc_level_contains_numbers(self, level: int) -> bool | None:
        NUMBER_RE = re.compile(r"^\s*\d+(\.\d+)*\s+")

        toc = self.content.find(".//text:table-of-content", self.NS)
        if toc is None:
            return None

        body = toc.find("text:index-body", self.NS)
        if body is None:
            return None

        found_any = False
        wanted_parent = f"Contents_20_{level}"

        for p in body.findall("text:p", self.NS):
            style_name = p.attrib.get(f"{{{self.NS['text']}}}style-name")
            if not style_name:
                continue

            style = self._find_style(style_name)
            if style is None:
                continue

            parent = style.attrib.get(f"{{{self.NS['style']}}}parent-style-name")
            if parent != wanted_parent:
                continue

            found_any = True
            txt = self.paragraph_text(p).strip()

            if NUMBER_RE.match(txt):
                return True

        return None if not found_any else False

    def heading_level_is_numbered(self, level: int) -> bool:
        exists, _, _ = self.get_heading_numbering_info(level)
        return exists

    def section_has_header_or_footer_content(self, index: int) -> bool:
        masters = self.styles.findall(".//style:master-page", self.NS)

        if index >= len(masters):
            return False

        master = masters[index]

        for tag in ("header", "footer"):
            el = master.find(f"style:{tag}", self.NS)
            if el is None:
                continue

            if self.get_visible_text(el):
                return True

        return False

    def _used_page_styles_in_order(self) -> list[str]:
        """
        Vrátí názvy použitých master page stylů v pořadí jejich výskytu.

        Returns:
            Seznam názvů použitých master page stylů bez duplicit.
        """
        used = []

        for el in self.content.iter():
            ps = el.attrib.get(f"{{{self.NS['style']}}}master-page-name")
            if ps and ps not in used:
                used.append(ps)

        return used

    def _section_master_page(self, index: int) -> ET.Element | None:
        """
        Vrátí master page odpovídající zadanému oddílu.

        Args:
            index: Index oddílu.

        Returns:
            XML element master page, nebo None pokud pro oddíl neexistuje.
        """
        pages = self._used_page_styles_in_order()
        if index >= len(pages):
            return None

        page_name = pages[index]
        return self.styles.find(
            f".//style:master-page[@style:name='{page_name}']", self.NS
        )

    def _section_header_footer_text(self, index: int, kind: str) -> str | None:
        """
        Vrátí text záhlaví nebo zápatí zadaného oddílu.

        Args:
            index: Index oddílu.
            kind: Typ části, například 'header' nebo 'footer'.

        Returns:
            Text záhlaví nebo zápatí, prázdný řetězec pokud část neexistuje,
            nebo None pokud nelze určit master page oddílu.
        """
        master = self._section_master_page(index)
        if master is None:
            return None

        part = master.find(f"style:{kind}", self.NS)
        if part is None:
            return ""

        return "".join(part.itertext()).strip()

    def section_has_header_text(self, index: int) -> bool:
        text = self._section_header_footer_text(index, "header")
        if text is None:
            return False
        return bool(text)

    def second_section_page_number_starts_at_one(self) -> bool | None:
        return self.section_page_number_starts_at_one(1)

    def _section_part_is_empty(self, index: int, kind: str) -> bool | None:
        """
        Ověří, zda je záhlaví nebo zápatí oddílu prázdné.

        Args:
            index: Index oddílu.
            kind: Typ části, například 'header' nebo 'footer'.

        Returns:
            True pokud je část prázdná, False pokud obsahuje text,
            nebo None pokud ji nelze zjistit.
        """
        text = self._section_header_footer_text(index, kind)
        if text is None:
            return None
        return not bool(text)

    def section_footer_is_empty(self, index: int) -> bool | None:
        return self._section_part_is_empty(index, "footer")

    def section_header_is_empty(self, index: int) -> bool | None:
        return self._section_part_is_empty(index, "header")

    def footer_is_linked_to_previous(self, index: int) -> bool | None:
        # Writer nemá koncept "propojení s předchozím oddílem"
        return None

    def header_is_linked_to_previous(self, index: int) -> bool | None:
        # Writer nemá koncept "propojení s předchozím oddílem"
        return None

    def has_bibliography(self) -> bool:
        return self.content.find(".//text:bibliography", self.NS) is not None

    def _count_bibliography_items_from_field(self) -> int | None:
        """
        Spočítá položky bibliografie vložené jako bibliografické pole.

        Returns:
            Počet položek bibliografie, 0 pokud je pole prázdné,
            nebo None pokud bibliografické pole v dokumentu není.
        """
        bib = self.content.find(".//text:bibliography", self.NS)
        if bib is None:
            return None

        body = bib.find("text:index-body", self.NS)
        if body is None:
            return 0

        title = body.find("text:index-title", self.NS)

        count = 0
        for p in body.findall(".//text:p", self.NS):
            if title is not None and self._is_descendant_of(p, title):
                continue

            txt = self._extract_text(p)
            if txt:
                count += 1

        return count

    def _is_descendant_of(self, node: ET.Element, ancestor: ET.Element) -> bool:
        """
        Ověří, zda je uzel potomkem zadaného nadřazeného elementu.

        Args:
            node: XML element, který se má ověřit.
            ancestor: Možný nadřazený element.

        Returns:
            True pokud je node uvnitř ancestor, jinak False.
        """
        for el in ancestor.iter():
            if el is node:
                return True
        return False

    def count_bibliography_items(self) -> int:
        cnt = self._count_bibliography_items_from_field()
        return int(cnt or 0)

    def _iter_citations_tag_and_number(self) -> Iterator[tuple[str, int]]:
        for mark in self.content.findall(".//text:bibliography-mark", self.NS):
            ident = (mark.get(f"{{{self.NS['text']}}}identifier") or "").strip()
            if not ident:
                continue

            rendered = self._extract_text(mark)
            m = self._CIT_MARK_NUM_RE.search(rendered or "")
            if not m:
                continue

            yield (ident, int(m.group(1)))

    def iter_bibliography_source_tags(self) -> list[str]:
        BIB_ITEM_NUM_RE = re.compile(r"^\s*(\d{1,3})\s*[:.)]\s*")
        T = self.NS["text"]

        bib = self.content.find(f".//{{{T}}}bibliography")
        if bib is None:
            return []

        body = bib.find(f"{{{T}}}index-body")
        if body is None:
            return []

        num_to_idents: dict[int, list[str]] = {}
        for ident, num in self._iter_citations_tag_and_number():
            if not ident:
                continue
            n = int(num)
            num_to_idents.setdefault(n, [])
            if ident not in num_to_idents[n]:
                num_to_idents[n].append(ident)

        tags: list[str] = []

        for p in body.findall(f"{{{T}}}p"):
            txt = self._extract_text(p)
            if not txt:
                continue

            m = BIB_ITEM_NUM_RE.match(txt)
            if not m:
                tags.append(f"BIB#{len(tags) + 1}")
                continue

            n = int(m.group(1))
            idents = num_to_idents.get(n, [])

            if len(idents) >= 1:
                tags.append(idents[0])
            else:
                tags.append(f"BIB#{n}")

        return tags

    def find_duplicate_bibliography_tags(self) -> list[str]:
        tags = self.iter_bibliography_source_tags()
        seen: set[str] = set()
        dup: set[str] = set()
        for t in tags:
            if t in seen:
                dup.add(t)
            else:
                seen.add(t)
        return sorted(dup)

    def get_unique_citation_tags(self) -> set[str]:
        return set(self.iter_citation_tags_in_order())

    def iter_citation_tags_in_order(self) -> list[str]:
        seen = set()
        out = []
        for ident, _num in self._iter_citations_tag_and_number():
            if ident not in seen:
                seen.add(ident)
                out.append(ident)
        return out

    

    def _source_match_tokens(self, src) -> list[str]:
        """
        Vrátí tokeny pro párování zdroje s vyrenderovanou bibliografií.

        Returns:
            Rozpoznávací tokeny zdroje.
        """
        tokens: list[str] = []

        author = str(getattr(src, "author", "") or "").strip()
        title = str(getattr(src, "title", "") or "").strip()
        year = str(getattr(src, "year", "") or "").strip()

        if author:
            tokens.append(author.lower())

            first_author = author.split(" - ")[0].split(",")[0].strip().lower()
            if first_author and first_author not in tokens:
                tokens.append(first_author)

        if title:
            tokens.append(title.lower())

        if year:
            tokens.append(year)

        return tokens   
    
    def _iter_rendered_bibliography_paragraphs(self) -> list[str]:
        """
        Vrátí texty položek zobrazené bibliografie.

        Returns:
            Texty položek bibliografie v pořadí zobrazení.
        """
        paragraphs: list[str] = []

        for bib in self.content.findall(".//text:bibliography", self.NS):
            for body in bib.findall("text:index-body", self.NS):
                for p in body.findall("text:p", self.NS):
                    text = "".join(p.itertext()).strip()
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
                tokens = self._source_match_tokens(src)

                for token in tokens:
                    if token and token in paragraph_l:
                        score += 1

                if score > best_score:
                    best_score = score
                    best_tag = tag

            if best_tag and best_score > 0:
                used_tags.add(best_tag)
                ordered_tags.append(best_tag)

        return ordered_tags

    def iter_bibliography_source_tags_in_order(self) -> list[str]:
        ordered: list[str] = []
        seen: set[str] = set()

        text_ns = self.NS.get("text")
        if not text_ns:
            return ordered

        identifier_attr = f"{{{text_ns}}}identifier"

        for bib in self.content.findall(".//text:bibliography", self.NS):
            for el in bib.iter():
                if not el.tag.endswith("}bibliography-mark"):
                    continue

                tag = (el.attrib.get(identifier_attr) or "").strip()
                if not tag or tag in seen:
                    continue

                seen.add(tag)
                ordered.append(tag)

        if ordered:
            return ordered

        for el in self.content.iter():
            if not el.tag.endswith("}bibliography-mark"):
                continue

            tag = (el.attrib.get(identifier_attr) or "").strip()
            if not tag or tag in seen:
                continue

            seen.add(tag)
            ordered.append(tag)

        return ordered

    def _extract_text(self, el: ET.Element) -> str:
        """
        Získá text elementu a základně jej normalizuje.

        Args:
            el: XML element, ze kterého se má text získat.

        Returns:
            Očištěný text bez nadbytečných mezer.
        """
        t = "".join(el.itertext())
        t = replace_nbsp(t)
        t = re.sub(r"[ \t]+", " ", t)
        t = re.sub(r"\s*\n\s*", "\n", t)
        return t.strip()

    def iter_bibliography_sources(self) -> list[BibliographySource]:
        by_tag: dict[str, BibliographySource] = {}

        for mark in self.content.findall(".//text:bibliography-mark", self.NS):
            ident = (mark.get(f"{{{self.NS['text']}}}identifier") or "").strip()
            if not ident:
                continue

            typ = (
                (mark.get(f"{{{self.NS['text']}}}bibliography-type") or "")
                .strip()
                .lower()
            )

            author = (mark.get(f"{{{self.NS['text']}}}author") or "").strip()
            title = (mark.get(f"{{{self.NS['text']}}}title") or "").strip()
            year = (mark.get(f"{{{self.NS['text']}}}year") or "").strip()

            publisher = (mark.get(f"{{{self.NS['text']}}}publisher") or "").strip()
            address = (mark.get(f"{{{self.NS['text']}}}address") or "").strip()

            isbn = (mark.get(f"{{{self.NS['text']}}}isbn") or "").strip()

            journal = (mark.get(f"{{{self.NS['text']}}}journal") or "").strip()
            volume = (mark.get(f"{{{self.NS['text']}}}volume") or "").strip()
            number = (mark.get(f"{{{self.NS['text']}}}number") or "").strip()
            pages = (mark.get(f"{{{self.NS['text']}}}pages") or "").strip()

            url = (mark.get(f"{{{self.NS['text']}}}url") or "").strip()
            if not url:
                url = (mark.get(f"{{{self.NS['xlink']}}}href") or "").strip()

            note = (mark.get(f"{{{self.NS['text']}}}note") or "").strip()
            annotation = (mark.get(f"{{{self.NS['text']}}}annotation") or "").strip()

            access_date = annotation or note

            type_map = {
                "book": "book",
                "article": "article",
                "journal": "article",
                "www": "online",
                "web": "online",
                "internet": "online",
                "online": "online",
            }
            typ = type_map.get(typ, typ)

            if ident not in by_tag:
                by_tag[ident] = BibliographySource(
                    tag=ident,
                    type=typ,
                    author=author,
                    title=title,
                    year=year,
                    publisher=publisher,
                    address=address,
                    isbn=isbn,
                    ref_order="",
                    url=url,
                    journal=journal,
                    volume=volume,
                    number=number,
                    pages=pages,
                    note=note,
                    access_date=access_date,
                )

        return list(by_tag.values())

    def _extract_citations_from_block(
        self, el: ET.Element
    ) -> list[tuple[str, int | None]]:
        """
        Získá citace z bloku textu včetně jejich identifikátoru a čísla.

        Args:
            el: XML element bloku.

        Returns:
            Seznam dvojic ve tvaru (identifikátor citace, číslo nebo None).
        """
        out: list[tuple[str, int | None]] = []
        for mark in el.findall(".//text:bibliography-mark", self.NS):
            ident = (mark.get(f"{{{self.NS['text']}}}identifier") or "").strip()
            if not ident:
                continue

            rendered = self._extract_text(mark)
            m = self._CIT_MARK_NUM_RE.search(rendered or "")
            num = int(m.group(1)) if m else None

            out.append((ident, num))
        return out

    def _block_is_citation_only(self, el: ET.Element) -> bool:
        """
        Ověří, zda blok obsahuje pouze samotnou citaci nebo její číslo.

        Args:
            el: XML element bloku.

        Returns:
            True pokud blok představuje jen citaci, jinak False.
        """
        CIT_ONLY_NUM_RE = re.compile(r"^[\(\[\s]*\d+[\)\]\s]*$")

        if not el.findall(".//text:bibliography-mark", self.NS):
            return False

        visible = (self.paragraph_text(el) or "").strip()
        if not visible:
            return True

        if not CIT_ONLY_NUM_RE.fullmatch(visible):
            return False

        return True

    def _build_section_index_map(self) -> dict[int, int | None]:
        """
        Vytvoří mapu bloků na indexy oddílů podle použitých master page stylů.

        Returns:
            Slovník ve tvaru id(bloku) -> index oddílu nebo None.
        """
        page_styles = self._used_page_styles_in_order()
        index_by_master = {name: i for i, name in enumerate(page_styles)}

        out: dict[int, int | None] = {}
        for el, mp in self._iter_blocks_with_page_style():
            out[id(el)] = index_by_master.get(mp) if mp else None
        return out

    def find_citations_in_wrong_places(self) -> list[dict]:
        problems: list[dict] = []

        sec_map = self._build_section_index_map()

        blocks: list[ET.Element] = []
        blocks.extend(self.content.findall(".//text:p", self.NS))
        blocks.extend(self.content.findall(".//text:h", self.NS))

        first_h1_section: int | None = None
        for h in self.content.findall(".//text:h", self.NS):
            lvl = h.attrib.get(f"{{{self.NS['text']}}}outline-level")
            if lvl == "1":
                first_h1_section = sec_map.get(id(h))
                break

        for el in blocks:
            cites = self._extract_citations_from_block(el)
            if not cites:
                continue

            sec_idx = sec_map.get(id(el))

            is_heading = self.paragraph_is_heading(el)

            in_cover_part = (
                sec_idx is not None
                and first_h1_section is not None
                and sec_idx < first_h1_section
            )
            in_first_section = sec_idx == 0

            empty_or_only_cit = self.paragraph_is_empty(
                el
            ) or self._block_is_citation_only(el)

            reason_key = None
            if is_heading:
                reason_key = "reason_in_heading"
            elif in_first_section or in_cover_part:
                reason_key = "reason_in_cover"
            elif empty_or_only_cit:
                reason_key = "reason_citation_only_or_empty"

            if not reason_key:
                continue

            snippet = (
                self.paragraph_text(el) or self.paragraph_text_raw(el) or ""
            ).strip()
            snippet = snippet[:120] if snippet else ""

            for tag, num in cites:
                problems.append(
                    {
                        "tag": tag,
                        "num": num if num is not None else "?",
                        "reason_key": reason_key,
                        "snippet": snippet,
                        "section": sec_idx,
                    }
                )

        return problems

    def section_count(self) -> int:
        page_styles = self._used_page_styles_in_order()
        return len(page_styles)

    def _section_page_style(self, section_index: int) -> str | None:
        """
        Vrátí název page stylu použitého pro zadaný oddíl.

        Args:
            section_index: Index oddílu.

        Returns:
            Název page stylu, nebo None pokud oddíl neexistuje.
        """
        page_styles = self._used_page_styles_in_order()
        if section_index < 0 or section_index >= len(page_styles):
            return None
        return page_styles[section_index]

    def _find_first_block_by_tag_with_page_style(
        self, tag: str
    ) -> tuple[ET.Element, str] | None:
        """
        Najde první blok se zadaným tagem a vrátí i jeho page styl.

        Args:
            tag: Hledaný XML tag.

        Returns:
            Dvojici (element, page style), nebo None pokud blok neexistuje.
        """
        for el, page_style in self._iter_blocks_with_page_style():
            if el.tag == tag:
                return el, page_style
        return None

    def _has_index_tag_in_section(self, section_index: int, tag: str) -> bool:
        """
        Ověří, zda oddíl obsahuje blok se zadaným indexovým tagem.

        Args:
            section_index: Index oddílu.
            tag: Hledaný XML tag indexu.

        Returns:
            True pokud se blok s daným tagem nachází v oddílu, jinak False.
        """
        target = self._section_page_style(section_index)
        if target is None:
            return False

        for el, page_style in self._iter_blocks_with_page_style():
            if el.tag == tag:
                return page_style == target

        return False

    def has_toc_in_section(self, section_index: int) -> bool:
        return self._has_index_tag_in_section(
            section_index, f"{{{self.NS['text']}}}table-of-content"
        )

    def _iter_blocks_with_page_style(self) -> Iterator[tuple[ET.Element, str | None]]:
        """
        Iteruje důležité bloky dokumentu spolu s aktuálním page stylem.

        Returns:
            Iterátor dvojic ve tvaru (XML element bloku, název page stylu nebo None).
        """
        current = None
        interesting = {
            f"{{{self.NS['text']}}}p",
            f"{{{self.NS['text']}}}h",
            f"{{{self.NS['text']}}}table-of-content",
            f"{{{self.NS['text']}}}bibliography",
            f"{{{self.NS['text']}}}illustration-index",
            f"{{{self.NS['text']}}}table-index",
            f"{{{self.NS['text']}}}object-index",
        }

        for el in self.content.iter():
            if el.tag not in interesting:
                continue

            style_name = el.attrib.get(f"{{{self.NS['text']}}}style-name")
            if style_name:
                st = self._find_style(style_name)
                if st is not None:
                    mp = st.attrib.get(f"{{{self.NS['style']}}}master-page-name")
                    if mp:
                        current = mp

            yield el, current

    def has_text_in_section(self, section_index: int, min_words: int = 1) -> bool:
        page_styles = self._used_page_styles_in_order()
        if section_index < 0 or section_index >= len(page_styles):
            return False

        target = page_styles[section_index]
        word_count = 0

        for el, page_style in self._iter_blocks_with_page_style():
            if page_style != target:
                continue

            text = " ".join(el.itertext()).strip()
            if not text:
                continue

            word_count += len(text.split())
            if word_count >= min_words:
                return True

        return False

    def _is_bibliography_block(self, el: ET.Element) -> bool:
        """
        Ověří, zda element představuje bibliografii nebo její část.

        Args:
            el: XML element bloku.

        Returns:
            True pokud jde o bibliografický blok, jinak False.
        """
        if el.tag == f"{{{self.NS['text']}}}bibliography":
            return True

        style_name = el.attrib.get(f"{{{self.NS['text']}}}style-name", "")
        low = style_name.lower()
        return "bibliography" in low or "literatura" in low

    def has_bibliography_in_section(self, section_index: int) -> bool:
        target = self._section_page_style(section_index)
        if target is None:
            return False

        for el, page_style in self._iter_blocks_with_page_style():
            if page_style != target:
                continue

            if self._is_bibliography_block(el):
                return True

        return False

    def _index_inner_master_page(self, el: ET.Element) -> str | None:
        """
        Zjistí page style použitý uvnitř indexového bloku.

        Args:
            el: XML element indexu.

        Returns:
            Název vnitřního master page stylu, nebo None pokud jej nelze určit.
        """
        for child in el.iter():
            if child.tag not in {
                f"{{{self.NS['text']}}}p",
                f"{{{self.NS['text']}}}h",
            }:
                continue

            sn = child.attrib.get(f"{{{self.NS['text']}}}style-name")
            if not sn:
                continue

            st = self._find_style(sn)
            if st is None:
                continue

            mp = st.attrib.get(f"{{{self.NS['style']}}}master-page-name")
            if mp:
                return mp

        return None

    def has_list_of_figures_in_section(self, section_index: int) -> bool:
        target = self._section_page_style(section_index)
        if target is None:
            return False

        for el, page_style in self._iter_blocks_with_page_style():
            if el.tag != f"{{{self.NS['text']}}}illustration-index":
                continue

            if page_style == target:
                return True

            return self._index_inner_master_page(el) == target

        return False

    def has_list_of_tables_in_section(self, section_index: int) -> bool:
        return self._has_index_tag_in_section(
            section_index, f"{{{self.NS['text']}}}table-index"
        )

    def has_any_table(self) -> bool:
        return self.content.find(f".//{{{self.NS['table']}}}table") is not None

    def has_any_chart(self) -> bool:
        return any(o.type == "chart" for o in self.iter_objects())

    def has_any_equation(self) -> bool:
        return any(o.type == "equation" for o in self.iter_objects())

    def has_list_of_charts_in_section(self, section_index: int) -> bool:
        text_ns = self.NS["text"]
        tag_illustration_index = f"{{{text_ns}}}illustration-index"

        for el in self.iter_section_blocks(section_index):
            if el.tag != tag_illustration_index:
                continue

            src = el.find("text:illustration-index-source", self.NS)
            seq = None
            if src is not None:
                seq = (
                    src.attrib.get(f"{{{text_ns}}}caption-sequence-name", "")
                    .strip()
                    .lower()
                )

            if seq in {"chart", "graf", "grafy"}:
                return True

            name = el.attrib.get(f"{{{text_ns}}}name", "").lower()
            if "graf" in name or "chart" in name:
                return True

        return False

    def has_list_of_equations_in_section(self, section_index: int) -> bool:
        text_ns = self.NS["text"]
        tag_object_index = f"{{{text_ns}}}object-index"
        tag_illustration_index = f"{{{text_ns}}}illustration-index"

        for el in self.iter_section_blocks(section_index):
            if el.tag == tag_object_index:
                return True

            if el.tag == tag_illustration_index:
                src = el.find("text:illustration-index-source", self.NS)
                seq = ""
                if src is not None:
                    seq = (
                        src.attrib.get(f"{{{text_ns}}}caption-sequence-name", "")
                        .strip()
                        .lower()
                    )

                if seq in {"equation", "rovnice"}:
                    return True

                name = el.attrib.get(f"{{{text_ns}}}name", "").lower()
                if "rovnic" in name or "equation" in name:
                    return True

        return False

    def first_chapter_is_first_content_in_section(self, section_index: int) -> bool:
        page_styles = self._used_page_styles_in_order()
        if section_index < 0 or section_index >= len(page_styles):
            return False

        target = page_styles[section_index]

        for el, page_style in self._iter_blocks_with_page_style():
            if page_style != target:
                continue

            if self._is_chapter_heading(el):
                return True

            if self.get_visible_text(el):
                return False

        return False

    def paragraph_is_heading(self, el) -> bool:
        if el.tag == f"{{{self.NS['text']}}}h":
            return True

        if el.tag == f"{{{self.NS['text']}}}p":
            style = self.paragraph_style_name(el).lower()
            return style.startswith("heading") or style.startswith("nadpis")

        return False

    def _is_inside_index(self, element: ET.Element) -> bool:
        """
        Ověří, zda je element umístěný uvnitř obsahu nebo jiného indexu.

        Args:
            element: XML element pro kontrolu.

        Returns:
            True pokud je element součástí obsahu, bibliografie nebo jiného indexu,
            jinak False.
        """
        parent_map = self._parent_map
        cur = element
        while cur in parent_map:
            cur = parent_map[cur]
            local = cur.tag.split("}")[-1] if "}" in cur.tag else cur.tag
            if local in {
                "table-of-content",
                "index-body",
                "bibliography",
                "illustration-index",
                "table-index",
                "object-index",
                "user-index",
                "alphabetical-index",
            }:
                return True
        return False

    def find_html_artifacts(self) -> list[tuple[int, str]]:
        results = []

        ENTITY_RE = re.compile(
            r"&(?:nbsp|amp|lt|gt|quot|apos);|&#\d+;|&#x[0-9a-fA-F]+;"
        )
        TAG_LIKE_RE = re.compile(
            r"<\s*/?\s*[A-Za-z][A-Za-z0-9:_-]*[^>]*>"
        )  # <div>, </p>, <br>

        for i, p in enumerate(self.iter_paragraphs(), start=1):
            if self._is_inside_index(p):
                continue

            text = self.paragraph_text(p)
            if not text:
                continue

            if ENTITY_RE.search(text) or TAG_LIKE_RE.search(text):
                results.append((i, text.strip()))
                continue

            if "<" in text and ">" in text:
                results.append((i, text.strip()))

        return results

    def _paragraph_has_tab_stops(self, p: ET.Element) -> bool:
        """
        Ověří, zda má odstavec ve svém stylu definované tabulátory.

        Args:
            p: XML element odstavce.

        Returns:
            True pokud styl odstavce obsahuje tab stop pozice, jinak False.
        """
        style_name = self.paragraph_style_name(p)
        st = self._find_style(style_name)
        if st is None:
            return False
        return bool(self._resolve_tabs(st))

    def find_txt_artifacts(self) -> list[tuple[int, str]]:
        WEIRD_SPACES_RE = re.compile(r"[ ]{4,}")
        ASCII_RULE_RE = re.compile(r"^(?:\s*[-=*_]{6,}\s*)$")
        PSEUDO_BULLET_RE = re.compile(r"^\s*(?:[\*\-•]|o)\s+")
        COLUMNS_RE = re.compile(r"\S(?:\s{3,}|\t)\S")

        results = []

        for i, p in enumerate(self.iter_paragraphs(), start=1):
            if self._is_inside_index(p):
                continue

            text = self.paragraph_text(p)
            if not text:
                continue

            t = text.strip()

            if ASCII_RULE_RE.match(t):
                results.append((i, t))
                continue

            style = (self.paragraph_style_name(p) or "").lower()
            looks_like_real_list = any(
                k in style
                for k in (
                    "list",
                    "numbering",
                    "odraz",
                    "odráž",
                    "seznam",
                    "bullet",
                    "čísl",
                    "cisl",
                )
            )

            if PSEUDO_BULLET_RE.search(t) and not looks_like_real_list:
                results.append((i, t))
                continue

            if WEIRD_SPACES_RE.search(text):
                results.append((i, t))
                continue

            has_style_tabs = self._paragraph_has_tab_stops(p)

            if COLUMNS_RE.search(text):
                if "\t" in text and has_style_tabs:
                    continue

                if re.search(r"\S\s{3,}\S", text):
                    results.append((i, t))
                    continue

                if "\t" in text and not has_style_tabs:
                    results.append((i, t))
                    continue

        return results

    def _looks_like_pdf_line(self, s: str) -> bool:
        """
        Ověří, zda text vypadá jako krátký řádek vzniklý vložením z PDF.

        Args:
            s: Text jednoho odstavce nebo řádku.

        Returns:
            True pokud text odpovídá typickému řádku z PDF copy-paste,
            jinak False.
        """
        BULLET_LIKE_RE = re.compile(r"^\s*(?:[-•*]|[0-9]+\.)\s+")
        LABEL_LIKE_RE = re.compile(
            r"^\s*(vstup|výstup|poznámka|definice|příklad)\s*:\s*",
            re.I,
        )

        short_len = 55

        if not s:
            return False
        if len(s) > short_len:
            return False
        if BULLET_LIKE_RE.match(s) or LABEL_LIKE_RE.match(s):
            return False
        if s.endswith((".", "!", "?", ":", ";")):
            return False

        stripped = s.lstrip()
        if stripped and stripped[0].islower():
            return True
        if "," in s and len(s) >= 25:
            return True

        return False

    def _flush_pdf_short_run(
        self,
        results: list[tuple[int, str]],
        run: list[tuple[int, str]],
        *,
        run_threshold: int = 6,
        max_samples_per_run: int = 2,
    ) -> None:
        """
        Přidá do výsledků reprezentativní ukázky z detekovaného bloku krátkých řádků.

        Args:
            results: Výstupní seznam nalezených problémů.
            run: Blok po sobě jdoucích krátkých řádků.
            run_threshold: Minimální délka bloku, aby byl považován za problém.
            max_samples_per_run: Maximální počet ukázkových řádků přidaných do výsledků.
        """
        if len(run) < run_threshold:
            return

        for item in run[:max_samples_per_run]:
            results.append(item)

    def _is_probably_list(self, p_el: ET.Element, text: str) -> bool:
        """
        Odhadne, zda odstavec pravděpodobně představuje položku seznamu.

        Args:
            p_el: XML element odstavce.
            text: Text odstavce.

        Returns:
            True pokud text pravděpodobně představuje seznamovou položku, jinak False.
        """
        if not text:
            return False

        bullet_like_re = re.compile(
            r"^\s*(?:[-•*]|[0-9]+[.)]|[a-zA-Z][.)]|[ivxlcdmIVXLCDM]+[.)])\s+"
        )
        if bullet_like_re.match(text):
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

        parent = self._parent_map.get(p_el)
        while parent is not None:
            if parent.tag.endswith("}list-item") or parent.tag.endswith("}list"):
                return True
            parent = self._parent_map.get(parent)

        return False

    def find_pdf_artifacts(self) -> list[tuple[int, str]]:
        HYPHEN_BREAK_RE = re.compile(r"\w-\s*\n\s*\w")
        MANY_BREAKS_RE = re.compile(r"(?:\n\s*){2,}")

        results: list[tuple[int, str]] = []
        short_run: list[tuple[int, str]] = []

        for i, p in enumerate(self.iter_paragraphs(), start=1):
            if self._is_inside_index(p):
                self._flush_pdf_short_run(results, short_run)
                short_run.clear()
                continue

            if self.paragraph_is_heading(p):
                self._flush_pdf_short_run(results, short_run)
                short_run.clear()
                continue

            text = self.paragraph_text(p)
            if not text:
                self._flush_pdf_short_run(results, short_run)
                short_run.clear()
                continue

            raw = text.strip()

            if self._is_probably_list(p, raw):
                self._flush_pdf_short_run(results, short_run)
                short_run.clear()
                continue

            style = (self.paragraph_style_name(p) or "").lower()
            if any(k in style for k in ("caption", "titulek", "popis")):
                self._flush_pdf_short_run(results, short_run)
                short_run.clear()
                continue

            if re.match(
                r"^\s*(obrázek|graf|tabulka|figure|chart|table)\s+\d+",
                raw,
                re.IGNORECASE,
            ):
                self._flush_pdf_short_run(results, short_run)
                short_run.clear()
                continue

            if "\n" in raw:
                self._flush_pdf_short_run(results, short_run)
                short_run.clear()

                if HYPHEN_BREAK_RE.search(raw) or MANY_BREAKS_RE.search(raw):
                    results.append((i, raw))
                continue

            if len(raw) < 25:
                self._flush_pdf_short_run(results, short_run)
                short_run.clear()
                continue

            if self._looks_like_pdf_line(raw):
                short_run.append((i, raw))
                continue

            self._flush_pdf_short_run(results, short_run)
            short_run.clear()

        self._flush_pdf_short_run(results, short_run)
        short_run.clear()

        return results

    def _is_chapter_heading(self, el: ET.Element, level: int = 1) -> bool:
        """
        Ověří, zda element představuje nadpis kapitoly na zadané úrovni.

        Args:
            el: XML element odstavce nebo nadpisu.
            level: Očekávaná úroveň nadpisu.

        Returns:
            True pokud element odpovídá nadpisu dané úrovně, jinak False.
        """
        if el.tag == f"{{{self.NS['text']}}}h":
            lvl = el.attrib.get(f"{{{self.NS['text']}}}outline-level")
            if not lvl:
                return False
            try:
                return int(lvl) == level
            except ValueError:
                return False

        if el.tag == f"{{{self.NS['text']}}}p":
            style = (el.attrib.get(f"{{{self.NS['text']}}}style-name") or "").lower()
            if style.endswith("_heading") and level == 1:
                return True

        return False

    def _find_master_page(self, name: str) -> ET.Element | None:
        """
        Najde master page podle jejího názvu.

        Args:
            name: Název hledané master page.

        Returns:
            XML element master page, nebo None pokud neexistuje.
        """
        for mp in self.styles.findall(".//style:master-page", self.NS):
            if mp.get(f"{{{self.NS['style']}}}name") == name:
                return mp
        return None

    def section_footer_has_page_number(self, index: int) -> bool | None:
        page_styles = self._used_page_styles_in_order()
        if index < 0 or index >= len(page_styles):
            return None

        target_master = page_styles[index]
        current_master = None

        for el in self.content.iter():
            if el.tag not in {
                f"{{{self.NS['text']}}}p",
                f"{{{self.NS['text']}}}h",
            }:
                continue

            style_name = el.attrib.get(f"{{{self.NS['text']}}}style-name")
            if not style_name:
                continue

            style = self._find_style(style_name)
            if style is None:
                continue

            mp = style.attrib.get(f"{{{self.NS['style']}}}master-page-name")
            if mp:
                current_master = mp

            if current_master != target_master:
                continue

            master = self._find_master_page(current_master)
            if master is None:
                return False

            for footer_tag in (
                "footer",
                "footer-left",
                "footer-right",
                "footer-first",
            ):
                footer = master.find(f"style:{footer_tag}", self.NS)
                if footer is None:
                    continue

                if footer.find(".//text:page-number", self.NS) is not None:
                    return True

            return False

        return None

    def iter_toc_paragraphs(self) -> Iterator[ET.Element]:
        toc = self.content.find(".//text:table-of-content", self.NS)
        if toc is None:
            return

        body = toc.find("text:index-body", self.NS)
        if body is None:
            return

        for p in body.findall("text:p", self.NS):
            yield p

    def iter_section_blocks(self, section_index: int) -> Iterator[ET.Element]:
        page_styles = self._used_page_styles_in_order()
        if section_index < 0 or section_index >= len(page_styles):
            return
        target = page_styles[section_index]

        for el, page_style in self._iter_blocks_with_page_style():
            if page_style == target:
                yield el

    def normalize_heading_text(self, text: str) -> str:
        text = text.lower()

        text = re.sub(r"^\s*\d+(\.\d+)*\s*", "", text)

        text = re.sub(r"\s+\d+\s*$", "", text)

        text = re.sub(r"[.\t]+", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def paragraph_heading_level(self, el: ET.Element) -> int | None:
        if el.tag == f"{{{self.NS['text']}}}h":
            lvl = el.attrib.get(f"{{{self.NS['text']}}}outline-level")
            if lvl and lvl.isdigit():
                return int(lvl)

        if el.tag == f"{{{self.NS['text']}}}p":
            style = self.paragraph_style_name(el).lower()
            m = re.match(r"heading[_\s]*(\d+)", style)
            if m:
                return int(m.group(1))

        return None

    def _has_ancestor(self, parent_map: dict, el: ET.Element, tag_local: str) -> bool:
        """
        Ověří, zda má element mezi předky uzel se zadaným lokálním názvem tagu.

        Args:
            parent_map: Mapa potomků na jejich rodiče.
            el: XML element, od kterého se má hledat směrem nahoru.
            tag_local: Lokální název hledaného tagu.

        Returns:
            True pokud je mezi předky nalezen odpovídající element, jinak False.
        """
        target = f"{{{self.NS['text']}}}{tag_local}"
        cur = el
        while True:
            if cur.tag == target:
                return True
            nxt = parent_map.get(cur)
            if nxt is None:
                return False
            cur = nxt

    def _visible_text_for_compare(self, el: ET.Element) -> str:
        """
        Vrátí text elementu upravený pro porovnávání.

        Args:
            el: XML element, ze kterého se má text získat.

        Returns:
            Text s normalizovanými mezerami, tabulátory a zalomeními řádků.
        """
        txt = self._odt_text_with_specials(el)
        txt = txt.replace("\t", " ").replace("\n", " ")
        txt = normalize_spaces(txt)
        return txt

    def _is_inside_toc(self, parent_map: dict, el: ET.Element) -> bool:
        """
        Ověří, zda je element umístěný uvnitř obsahu.

        Args:
            parent_map: Mapa potomků na jejich rodiče.
            el: XML element pro kontrolu.

        Returns:
            True pokud je element uvnitř table-of-content, jinak False.
        """
        return self._has_ancestor(parent_map, el, "table-of-content")

    def toc_missing_used_headings(
        self, max_level: int = 3
    ) -> tuple[bool | None, list[str]]:
        parent_map = self._parent_map

        toc = self.content.find(".//text:table-of-content", self.NS)
        if toc is None:
            return (None, [])

        body = toc.find("text:index-body", self.NS)
        if body is None:
            return (None, [])

        toc_norm = set()
        for a in body.findall(".//text:a", self.NS):
            raw = self._visible_text_for_compare(a)
            key = self.normalize_heading_text(raw)
            if key:
                toc_norm.add(key)

        used_norm_to_pretty: dict[str, str] = {}

        for h in self.content.findall(".//text:h", self.NS):
            if self._is_inside_toc(parent_map, h):
                continue

            lvl = h.attrib.get(f"{{{self.NS['text']}}}outline-level")
            if not lvl:
                continue

            try:
                lvl_i = int(lvl)
            except ValueError:
                continue

            if not (1 <= lvl_i <= max_level):
                continue

            pretty = self._visible_text_for_compare(h)
            if not pretty:
                continue

            key = self.normalize_heading_text(pretty)
            if key and key not in used_norm_to_pretty:
                used_norm_to_pretty[key] = pretty

        missing_keys = sorted(set(used_norm_to_pretty.keys()) - toc_norm)
        missing = [used_norm_to_pretty[k] for k in missing_keys]

        return (len(missing) == 0, missing)

    def get_toc_illegal_content_errors(
        self,
    ) -> tuple[bool, list[TocIllegalContentError], str | None]:
        errors: list[TocIllegalContentError] = []

        ns = self.NS
        text_ns = ns["text"]
        xlink_ns = ns["xlink"]

        toc = self.content.find(".//text:table-of-content", ns)
        if toc is None:
            return False, [], "no_toc"

        index_body = toc.find("text:index-body", ns)
        if index_body is None:
            return True, [TocIllegalContentError("missing_index_body", {})], None

        if index_body.findall("./table:table", ns):
            errors.append(TocIllegalContentError("toc_has_table", {}))

        if (
            index_body.findall(".//draw:frame", ns)
            or index_body.findall(".//draw:object", ns)
            or index_body.findall(".//draw:g", ns)
        ):
            errors.append(TocIllegalContentError("toc_has_drawing", {}))

        heading_by_anchor: dict[str, str] = {}

        for h in self.content.findall(".//text:h", ns):
            outline = h.attrib.get(f"{{{text_ns}}}outline-level")
            if not outline:
                continue

            bm = h.find("text:bookmark-start", ns)
            if bm is None:
                continue

            name = bm.attrib.get(f"{{{text_ns}}}name")
            if not name:
                continue

            text = self.get_visible_text(h)
            if text:
                heading_by_anchor["#" + name] = self.normalize_heading_text(text)

        for p in index_body.findall("text:p", ns):
            link = p.find("text:a", ns)

            if link is None:
                text = self.get_visible_text(p)
                if text and text.lower() not in {"obsah", "table of contents"}:
                    errors.append(TocIllegalContentError("manual_text", {"text": text}))
                continue

            href = link.attrib.get(f"{{{xlink_ns}}}href")
            if not href:
                errors.append(TocIllegalContentError("missing_link", {}))
                continue

            href = unquote(href)

            toc_text = self.get_visible_text(link)
            norm_toc_text = self.normalize_heading_text(toc_text)

            expected = heading_by_anchor.get(href)

            if expected is None:
                errors.append(
                    TocIllegalContentError(
                        "missing_matching_heading", {"text": toc_text}
                    )
                )
                continue

            if expected not in norm_toc_text:
                errors.append(
                    TocIllegalContentError("modified_toc_item", {"text": toc_text})
                )

        return True, errors, None

    def has_toc(self) -> bool:
        return self.content.find(".//text:table-of-content", self.NS) is not None

    def iter_toc_items(self) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []

        toc = self.content.find(".//text:table-of-content", self.NS)
        if toc is None:
            return items

        index_body = toc.find("text:index-body", self.NS)
        if index_body is None:
            return items

        for p in index_body.findall("text:p", self.NS):
            link = p.find("text:a", self.NS)
            if link is None:
                continue

            href = link.attrib.get(f"{{{self.NS['xlink']}}}href")
            if not href or not href.startswith("#"):
                continue

            anchor = href[1:]

            raw_text = self.get_visible_text(link)
            if not raw_text:
                continue

            items.append(
                {
                    "anchor": anchor,
                    "text": self.normalize_heading_text(raw_text),
                }
            )

        return items

    def iter_image_bytes(self) -> Iterator[tuple[str, bytes]]:
        ns = self.NS
        xlink_ns = ns.get("xlink")
        if not xlink_ns:
            return

        href_attr = f"{{{xlink_ns}}}href"

        for el in self.content.iter():
            if not el.tag.endswith("}image"):
                continue

            href = el.attrib.get(href_attr)
            if not href:
                continue

            href = href.lstrip("./")
            name = href.split("/")[-1]

            try:
                with self._zip.open(href) as f:
                    yield name, f.read()
            except KeyError:
                continue
            except Exception:
                continue

    def _is_inside_illustration_index(self, p: ET.Element) -> bool:
        """
        Ověří, zda se odstavec nachází uvnitř seznamu obrázků.

        Args:
            p: XML element odstavce.

        Returns:
            True pokud je odstavec vnořený uvnitř elementu
            `text:illustration-index`, jinak False.
        """
        parent = self._parent_map.get(p)
        while parent is not None:
            if parent.tag == f"{{{self.NS['text']}}}illustration-index":
                return True
            parent = self._parent_map.get(parent)
        return False

    def iter_figure_caption_texts(self) -> list[str]:
        out = []
        seen = set()
        ns = self.NS

        for p in self.content.findall(".//text:p", ns):
            if self._is_inside_illustration_index(p):
                continue

            txt = self.get_visible_text(p)
            if not txt:
                continue

            txt = normalize_spaces(txt).strip()
            low = txt.lower()

            if low.startswith("obrázek") or low.startswith("figure"):
                if txt not in seen:
                    seen.add(txt)
                    out.append(txt)

        return out

    def iter_list_of_figures_texts(self) -> list[str]:
        items: list[str] = []

        ns = self.NS

        lof = self.content.find(".//text:illustration-index", ns)
        if lof is None:
            return items

        body = lof.find("text:index-body", ns)
        if body is None:
            return items

        for p in body.findall("text:p", ns):
            link = p.find("text:a", ns)
            if link is None:
                continue

            parts = []
            if link.text:
                parts.append(link.text)

            for child in link:
                if child.tag == f"{{{ns['text']}}}tab":
                    break

                if child.text:
                    parts.append(child.text)

                if child.tail:
                    parts.append(child.tail)

            txt = normalize_spaces("".join(parts)).strip()
            if not txt:
                continue

            low = txt.lower()
            if low.startswith("obrázek") or low.startswith("figure"):
                items.append(txt)

        return items

    def iter_objects(self) -> Iterator[DocumentObject]:
        for el in self.content.iter():
            if el.tag.endswith("image"):
                yield DocumentObject(type="image", element=el)

        for el in self.content.iter():
            if not el.tag.endswith("object"):
                continue

            href = None
            for k, v in el.attrib.items():
                if k.endswith("href"):
                    href = v
                    break

            if not href:
                continue

            href = href.lstrip("./").rstrip("/")
            content_path = f"{href}/content.xml"

            try:
                data = self._zip.read(content_path)
            except KeyError:
                continue

            if (
                b"<chart:chart" in data
                or b"xmlns:chart" in data
                or b'office:class="chart"' in data
                or b"opendocument.chart" in data
            ):
                yield DocumentObject(type="chart", element=el, href=href)
                continue

            is_equation = False

            if (
                b"<math:math" in data
                or b"xmlns:math" in data
                or b"opendocument.formula" in data
                or b"MathML" in data
                or b"mathml" in data
            ):
                is_equation = True
            else:
                try:
                    root = ET.fromstring(data)
                    mathml_ns = self.NS["mathml"]
                    for node in root.iter():
                        if node.tag.startswith(f"{{{mathml_ns}}}"):
                            is_equation = True
                            break
                except Exception:
                    pass

            if is_equation:
                yield DocumentObject(type="equation", element=el, href=href)
                continue


    def _closest_paragraph_ancestor(self, el: ET.Element) -> ET.Element | None:
        """
        Najde nejbližší nadřazený odstavec zadaného elementu.

        Args:
            el: XML element, od kterého se hledá směrem nahoru.

        Returns:
            Nejbližší nadřazený element text:p, nebo None pokud neexistuje.
        """
        parent_map = self._parent_map
        cur = el
        while cur in parent_map:
            cur = parent_map[cur]
            if cur.tag == f"{{{self.NS['text']}}}p":
                return cur
        return None

    def _get_ancestor_frames(self, el: ET.Element) -> list[ET.Element]:
        """
        Vrátí všechny nadřazené framy zadaného elementu.

        Args:
            el: XML element, od kterého se hledá směrem nahoru.

        Returns:
            Seznam nadřazených frame elementů od nejbližšího po nejvzdálenější.
        """
        frames = []
        cur = el

        while cur in self._parent_map:
            cur = self._parent_map[cur]
            if cur.tag == f"{{{self.NS['draw']}}}frame":
                frames.append(cur)

        return frames

    def object_has_caption(
        self,
        obj: DocumentObject,
        expected_labels: list[str] | None = None,
    ) -> bool:
        element = obj.element
        if element is None:
            return False

        ancestor_frames = self._get_ancestor_frames(element)
        if not ancestor_frames:
            return False
        
        for frame in reversed(ancestor_frames):
            paragraphs = frame.findall(".//text:p", self.NS)

            for p in paragraphs:
                info = self._parse_caption_paragraph(p)
                if info is None:
                    continue

                if expected_labels:
                    text = (info.text or "").strip().lower()

                    if info.label is not None:
                        if info.label.lower() not in [x.lower() for x in expected_labels]:
                            continue
                    else:
                        if not any(text.startswith(x.lower()) for x in expected_labels):
                            continue

                return True

        return False

    def get_object_caption_text(
        self,
        obj: DocumentObject,
        *,
        accept_manual: bool = False,
    ) -> str | None:
        info = self.get_object_caption_info(obj, accept_manual=accept_manual)
        if info is None:
            return None

        text = (info.text or "").strip()
        if not text:
            return None

        text = re.sub(
            r"^(obrázek|figure|tabulka|table|graf|chart)\s+\d+\s*[:\-]?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        return text or None

    def _parse_caption_paragraph(
        self,
        p: ET.Element,
        *,
        accept_manual: bool = False,
        manual_prefixes: tuple[str, ...] = (),
    ) -> ObjectCaptionInfo | None:
        """
        Zjistí, zda daný odstavec představuje titulek objektu.

        Args:
            p: Odstavec, který se má vyhodnotit.
            accept_manual: Určuje, zda se mají uznat i ručně
                vytvořené titulky.
            manual_prefixes: Povolené textové začátky ručního titulku.

        Returns:
            Informace o titulku objektu, nebo None pokud odstavec
            titulku neodpovídá.
        """
        text = normalize_spaces("".join(p.itertext())).strip()
        if not text:
            return None

        style = (
            p.attrib.get(f"{{{self.NS['text']}}}style-name") or ""
        ).lower()

        seq = p.find("text:sequence", self.NS)
        if seq is not None:
            seq_name = (
                seq.attrib.get(f"{{{self.NS['text']}}}name", "") or ""
            ).lower()

            if seq_name in ("figure", "illustration"):
                label = "Obrázek"
            elif seq_name == "table":
                label = "Tabulka"
            elif seq_name in ("drawing", "chart"):
                label = "Graf"
            else:
                label = None

            if label is not None:
                return ObjectCaptionInfo(
                    label=label,
                    is_seq=True,
                    text=text,
                    is_manual=False,
                )

        if accept_manual:
            low = text.lower()
            if any(x in style for x in ("figure", "caption", "titulek")):
                if low.startswith(manual_prefixes):
                    return ObjectCaptionInfo(
                        label=None,
                        is_seq=False,
                        text=text,
                        is_manual=True,
                    )

        return None


    def _find_nearest_frame(self, el: ET.Element) -> ET.Element | None:
        """
        Najde nejbližší nadřazený frame zadaného elementu.

        Args:
            el: XML element, od kterého se hledá směrem nahoru.

        Returns:
            Nejbližší nadřazený frame, nebo None pokud neexistuje.
        """
        cur = el
        while cur in self._parent_map:
            cur = self._parent_map[cur]
            if cur.tag == f"{{{self.NS['draw']}}}frame":
                return cur
        return None


    def get_object_caption_info(
        self,
        obj: DocumentObject,
        *,
        accept_manual: bool = False,
    ) -> ObjectCaptionInfo | None:
        """
        Vrátí informace o titulku objektu v Writer dokumentu.

        Args:
            obj: Objekt, pro který se má titulek dohledat.
            accept_manual: Určuje, zda se mají uznat i ručně
                vytvořené titulky.

        Returns:
            Informace o titulku objektu, nebo None pokud titulek
            nebyl nalezen.
        """
        element = obj.element
        if element is None:
            return None

        obj_type = (obj.type or "").lower()
        parent_map = {c: p for p in self.content.iter() for c in list(p)}

        manual_prefixes_by_type = {
            "image": ("obrázek", "figure"),
            "chart": ("graf", "chart"),
            "table": ("tabulka", "table"),
        }
        manual_prefixes = manual_prefixes_by_type.get(obj_type, ())

        host_paragraph = self._closest_paragraph_ancestor(element)
        if host_paragraph is not None:
            info = self._parse_caption_paragraph(
                host_paragraph,
                accept_manual=accept_manual,
                manual_prefixes=manual_prefixes,
            )
            if info is not None:
                return info

        nearest_frame = self._find_nearest_frame(element)
        if nearest_frame is not None:
            text_paragraphs = nearest_frame.findall(".//text:p", self.NS)
            for p in text_paragraphs:
                if p is host_paragraph:
                    continue

                info = self._parse_caption_paragraph(
                    p,
                    accept_manual=accept_manual,
                    manual_prefixes=manual_prefixes,
                )
                if info is not None:
                    return info

        return None
    
    def iter_object_crossref_ids(self) -> set[str]:
        refs = set()
        parent_map = self._parent_map

        from urllib.parse import unquote

        def is_inside_index(element):
            cur = element
            while cur in parent_map:
                cur = parent_map[cur]
                tag_name = cur.tag.split("}")[-1] if "}" in cur.tag else cur.tag
                if tag_name in (
                    "table-of-content",
                    "illustration-index",
                    "object-index",
                    "user-index",
                    "alphabetical-index",
                    "bibliography",
                    "index-body",
                ):
                    return True
            return False

        ref_tags = ["reference-ref", "sequence-ref", "bookmark-ref"]

        for tag in ref_tags:
            for node in self.content.findall(f".//text:{tag}", self.NS):
                if is_inside_index(node):
                    continue

                name = node.attrib.get(f"{{{self.NS['text']}}}ref-name")
                if name:
                    refs.add(name)
                    if tag == "sequence-ref" and "|" not in name:
                        import re

                        m = re.match(r"ref([A-Za-z]+)(\d+)", name)
                        if m:
                            n_name, n_num = m.groups()
                            refs.add(f"{n_name}!{n_num}|sequence")

        for a in self.content.findall(".//text:a", self.NS):
            if is_inside_index(a):
                continue

            href = a.attrib.get(f"{{{self.NS['xlink']}}}href")
            if href and href.startswith("#"):
                decoded_href = unquote(href[1:])
                refs.add(decoded_href)
        return refs

    def _normalize_writer_sequence_ref(self, ref: str) -> str | None:
        """
        Převede interní Writer reference na jednotný tvar pro sekvenční odkazy.

        Args:
            ref: Původní identifikátor reference.

        Returns:
            Normalizovaný identifikátor sekvence, nebo None pokud vstup neodpovídá očekávanému formátu.
        """
        m = re.match(r"ref([A-Za-z]+)(\d+)", ref)
        if not m:
            return None
        name, num = m.groups()
        return f"{name}!{num}|sequence"

    def get_object_caption_ref_ids(self, obj: DocumentObject) -> set[str]:
        element = obj.element
        if element is None:
            return set()

        parent_map = self._parent_map

        cur = element
        target_frame = None

        while cur in parent_map:
            cur = parent_map[cur]
            if cur.tag == f"{{{self.NS['draw']}}}frame":
                target_frame = cur

        if target_frame is None:
            return set()

        refs = set()
        for p in target_frame.findall(".//text:p", self.NS):
            for seq in p.findall(".//text:sequence", self.NS):
                raw = seq.attrib.get(f"{{{self.NS['text']}}}ref-name")
                if not raw:
                    continue

                refs.add(raw)

                norm = self._normalize_writer_sequence_ref(raw)
                if norm:
                    refs.add(norm)

        return refs

    def get_bibliography_style(self) -> StyleSpec | None:
        bib = self.content.find(".//text:bibliography", self.NS)
        if bib is None:
            bib = (
                self.content.find(".//text:bibliography-index", self.NS)
                or self.content.find(
                    ".//text:section[@text:name='Bibliography']", self.NS
                )
                or self.content.find(
                    ".//text:section[@text:name='Bibliografie']", self.NS
                )
            )

        if bib is not None:
            for p in bib.findall(".//text:p", self.NS):
                style_name = (
                    p.attrib.get(f"{{{self.NS['text']}}}style-name") or ""
                ).strip()
                if not style_name:
                    continue

                st = self._find_style(style_name)
                if st is not None:
                    return self._build_style_spec(st)

        for key in ("bibliography", "bibliografie"):
            st = self._find_style(key)
            if st is not None:
                return self._build_style_spec(st)

        for k, st in self._style_by_name.items():
            kl = (k or "").lower()
            if "bibliography" in kl or "bibliograf" in kl:
                return self._build_style_spec(st)

        return None

    def get_content_heading_style(self) -> StyleSpec | None:
        for style in self.styles.findall(".//style:style", self.NS):
            family = style.attrib.get(f"{{{self.NS['style']}}}family")
            if family != "paragraph":
                continue

            name = (
                style.attrib.get(f"{{{self.NS['style']}}}name", "").lower()
                + " "
                + style.attrib.get(f"{{{self.NS['style']}}}display-name", "").lower()
            )

            if "contents heading" in name or "obsah" in name:
                return self._build_style_spec(style, default_alignment="start")

        return None

    def section_page_number_starts_at_one(self, section_index: int) -> bool | None:
        page_styles = self._used_page_styles_in_order()

        if section_index < 0 or section_index >= len(page_styles):
            return None

        target_master = page_styles[section_index]

        for el in self.content.iter():
            style_name = el.attrib.get(f"{{{self.NS['text']}}}style-name")
            if not style_name:
                continue

            style = self._find_style(style_name)
            if style is None:
                continue

            mp = style.attrib.get(f"{{{self.NS['style']}}}master-page-name")
            if mp != target_master:
                continue

            pp = style.find("style:paragraph-properties", self.NS)
            if pp is None:
                return False

            start = pp.attrib.get(f"{{{self.NS['style']}}}page-number")

            if start == "1":
                return True

            return False

        return None

    def section_missing_styles(
        self, section_index: int, styles: set[str]
    ) -> tuple[bool, list[str]]:
        found = set()

        for el in self.iter_section_blocks(section_index):
            if el.tag not in {
                f"{{{self.NS['text']}}}p",
                f"{{{self.NS['text']}}}h",
            }:
                continue

            style_name = (self.paragraph_style_name(el) or "").strip()
            if not style_name:
                continue

            if style_name in styles:
                found.add(style_name)
                if found == styles:
                    return (True, [])

        missing = sorted(styles - found)
        return (len(missing) == 0, missing)

    def paragraph_style_id(self, p: ET.Element) -> str | None:
        return p.attrib.get(f"{{{self.NS['text']}}}style-name")

    def paragraph_has_numbering(self, el: ET.Element) -> bool:
        if el.attrib.get(f"{{{self.NS['text']}}}list-style-name"):
            return True

        style_name = el.attrib.get(f"{{{self.NS['text']}}}style-name")
        if style_name:
            st = self._find_style(style_name)
            if st is not None:
                val = self._resolve_para_attr(st, f"{{{self.NS['text']}}}list-style-name")
                if val:
                    return True

        level = self.paragraph_heading_level(el)
        if level is not None and self.heading_level_is_numbered(level):
            return True

        return False

    def _resolve_para_attr(self, style_el: ET.Element, attr_qname: str) -> str | None:
        """
        Vrátí hodnotu odstavcové vlastnosti ze stylu nebo jeho rodičů.

        Args:
            style_el: XML element stylu.
            attr_qname: Plně kvalifikovaný název atributu.

        Returns:
            Hodnota atributu, nebo None pokud není nalezena.
        """
        visited = set()

        while style_el is not None and id(style_el) not in visited:
            visited.add(id(style_el))

            pp = style_el.find("style:paragraph-properties", self.NS)
            if pp is not None:
                val = pp.attrib.get(attr_qname)
                if val is not None:
                    return val

            parent = style_el.attrib.get(f"{{{self.NS['style']}}}parent-style-name")
            if not parent:
                break

            style_el = self._find_style(parent)

        return None

    def _is_caption_style(self, el: ET.Element) -> bool:
        """
        Ověří, zda element používá styl, který vypadá jako styl titulku.

        Args:
            el: XML element odstavce.

        Returns:
            True pokud název stylu odpovídá titulku objektu, jinak False.
        """
        CAPTION_STYLE_HINTS = (
            "caption",
            "popisek",
            "titulek",
            "obrázek",
            "obrazek",
            "figure",
            "table",
            "graf",
            "chart",
            "equation",
            "rovnice",
            "illustration",
        )
        style_attr = f"{{{self.NS['text']}}}style-name"
        st = (el.get(style_attr) or "").strip().lower()
        if not st:
            return False
        return any(h in st for h in CAPTION_STYLE_HINTS)

    def _strip_inline_xrefs(self, s: str) -> str:
        """
        Odstraní z textu vložené odkazy na objekty a jejich zbytky.

        Args:
            s: Vstupní text.

        Returns:
            Očištěný text bez inline křížových odkazů.
        """
        XREF_VIZ_RE = re.compile(
            r"(?i)\b(viz|viz\.|vizte|see)\b(?:\s+\w+){0,2}\s*[:–-]?\s*\d+\b"
        )

        XREF_LABEL_RE = re.compile(
            r"(?i)\b(obrázek|obrazek|figure|fig\.?|tabulka|table|graf|chart|rovnice|equation)\s*\d+\b"
        )
        XREF_DANGLING_RE = re.compile(r"(?i)\b(viz|viz\.|vizte|see)\b[\s:–-]*$")

        if not s:
            return ""

        s = XREF_VIZ_RE.sub("", s)
        s = XREF_LABEL_RE.sub("", s)

        s = re.sub(r"\s{2,}", " ", s).strip()

        s = XREF_DANGLING_RE.sub("", s).strip()

        s = re.sub(r"[ \t]+([.,;:])", r"\1", s).strip()
        s = re.sub(r"[.,;:]\s*$", "", s).strip()

        return s

    def _should_skip_paragraph(self, el: ET.Element) -> bool:
        """
        Ověří, zda se má odstavec přeskočit při porovnávání textu.

        Args:
            el: XML element odstavce.

        Returns:
            True pokud odstavec představuje titulek objektu, jinak False.
        """
        CAPTION_LABELS = (
            "figure",
            "obrázek",
            "obrazek",
            "tabulka",
            "table",
            "graf",
            "chart",
            "rovnice",
            "equation",
        )

        CAPTION_LINE_RE = re.compile(
            rf"^\s*(?:{'|'.join(CAPTION_LABELS)})\s*\d+\s*[:.\-]?\s*",
            re.IGNORECASE,
        )
        if self._is_caption_style(el):
            return True

        t = self._extract_text(el)
        if CAPTION_LINE_RE.match(t):
            return True

        return False

    def _iter_text_blocks_for_compare(
        self, root_iter: Iterable[ET.Element]
    ) -> Iterator[str]:
        """
        Iteruje textové bloky vhodné pro porovnávání obsahu.

        Args:
            root_iter: Iterátor XML elementů.

        Yields:
            Očištěné texty odstavců, nadpisů nebo tabulek vhodné pro porovnání.
        """
        prev = None

        allowed = {
            f"{{{self.NS['text']}}}p",
            f"{{{self.NS['text']}}}h",
            f"{{{self.NS['table']}}}table",
        }

        for el in root_iter:
            if el.tag not in allowed:
                continue

            if self._should_skip_paragraph(el):
                continue

            t = self._extract_text(el)
            if not t:
                continue

            t = self._strip_inline_xrefs(t)
            if not t:
                continue

            if prev is not None and t == prev:
                continue

            yield t
            prev = t

    def get_text_of_section(self, section_index: int) -> str:
        blocks = list(
            self._iter_text_blocks_for_compare(self.iter_section_blocks(section_index))
        )
        return "\n".join(blocks)

    def get_full_text(self) -> str:
        blocks = list(self._iter_text_blocks_for_compare(self.content.iter()))
        return "\n".join(blocks)

    def get_object_image_bytes(self, obj: DocumentObject) -> bytes | None:
        if obj is None or obj.type != "image" or obj.element is None:
            return None

        href = obj.element.attrib.get(f"{{{self.NS['xlink']}}}href")
        if not href:
            return None

        href = href.lstrip("./")

        try:
            with self._zip.open(href) as f:
                return f.read()
        except KeyError:
            return None
        except Exception:
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
