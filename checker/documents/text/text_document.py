import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable, Iterator

from assignment.text.text_assignment_model import StyleSpec
from models.text_models import (
    BibliographySource,
    DocumentObject,
    ObjectCaptionInfo,
    TocIllegalContentError,
)


class TextDocument(ABC):
    BUILTIN_STYLE_NAMES = {
        "normal",
        "heading 1",
        "heading 2",
        "heading 3",
        "heading 4",
        "caption",
        "bibliography",
        "toc heading",
        "table of contents",
        "content heading",
    }

    @staticmethod
    def from_path(path: str | Path) -> "TextDocument":
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix == ".docx":
            from documents.text.word_document import WordDocument

            return WordDocument(str(path))

        if suffix == ".odt":
            from documents.text.writer_document import WriterDocument

            return WriterDocument(str(path))

        raise ValueError(f"Nepodporovaný textový formát: {path}")

    def _norm(self, name: str) -> str:
        return name.strip().lower()

    def split_assignment_styles(self, assignment):
        custom = {}
        builtin = {}

        for name, spec in assignment.styles.items():
            if self._norm(name) in self.BUILTIN_STYLE_NAMES:
                builtin[name] = spec
            else:
                custom[name] = spec

        return custom, builtin

    @abstractmethod
    def save_debug_xml(self, out_dir: str | Path = "debug"):
        """
        Uloží interní XML strukturu dokumentu do debug složky.

        Args:
            out_dir: Výstupní složka pro uložení debug souborů.
        """
        ...

    @abstractmethod
    def get_bibliography_style(self):
        """
        Vrátí styl používaný pro bibliografii.

        Returns:
            Styl bibliografie, nebo None pokud není v dokumentu dostupný.
        """
        ...

    @abstractmethod
    def get_doc_default_font_size(self) -> int | None:
        """
        Vrátí výchozí velikost písma dokumentu.

        Returns:
            Výchozí velikost písma v bodech, nebo None pokud ji nelze zjistit.
        """
        ...

    @abstractmethod
    def get_style_by_any_name(
        self, names: list[str], *, default_alignment: str | None = None
    ):
        """
        Najde první existující styl ze zadaného seznamu názvů.

        Args:
            names: Kandidátní názvy stylu.
            default_alignment: Výchozí zarovnání použité při sestavení stylu.

        Returns:
            Odpovídající styl, nebo None pokud žádný z názvů neexistuje.
        """
        ...

    @abstractmethod
    def get_content_heading_style(self):
        """
        Vrátí styl používaný pro nadpis obsahu.

        Returns:
            Styl nadpisu obsahu, nebo None pokud není v dokumentu dostupný.
        """
        ...

    @abstractmethod
    def get_cover_style(self, key: str) -> StyleSpec | None:
        """
        Vrátí styl pro zadanou část desek nebo titulní strany.

        Args:
            key: Klíč určující, který styl desek se má načíst.

        Returns:
            Odpovídající styl, nebo None pokud není definovaný.
        """
        ...

    @abstractmethod
    def get_style_parent(self, style_name: str) -> str | None:
        """
        Vrátí název rodičovského stylu pro zadaný styl.

        Args:
            style_name: Název stylu, jehož rodič se má zjistit.

        Returns:
            Název rodičovského stylu, nebo None pokud styl rodiče nemá.
        """
        ...

    @abstractmethod
    def get_used_paragraph_styles(self) -> set[str]:
        """
        Vrátí množinu názvů odstavcových stylů použitých v dokumentu.

        Returns:
            Množina názvů stylů použitých v odstavcích.
        """
        ...

    @abstractmethod
    def style_exists(self, style_name: str) -> bool:
        """
        Ověří, zda v dokumentu existuje styl s daným názvem.

        Args:
            style_name: Název hledaného stylu.

        Returns:
            True, pokud styl existuje, jinak False.
        """
        ...

    @abstractmethod
    def get_custom_style(self, style_name: str) -> StyleSpec | None:
        """
        Vrátí specifikaci vlastního stylu podle názvu.

        Args:
            style_name: Název stylu.

        Returns:
            Styl ve formě StyleSpec, nebo None pokud styl neexistuje.
        """
        ...

    @abstractmethod
    def get_heading_numbering_info(self, level: int) -> tuple[bool, bool, int | None]:
        """
        Vrátí informace o číslování nadpisu na zadané úrovni.

        Args:
            level: Úroveň nadpisu.

        Returns:
            Trojici hodnot určující, zda je číslování definované, zda je hierarchické,
            a jaká je úroveň číslování.
        """

    ...

    @abstractmethod
    def get_heading_styles(self, level: int) -> list[StyleSpec]:
        """
        Vrátí seznam stylů nadpisů pro zadanou úroveň.

        Args:
            level: Úroveň nadpisu.

        Returns:
            Seznam odpovídajících stylů, případně prázdný seznam.
        """
        ...

    @abstractmethod
    def iter_headings(self) -> list[tuple[str, int]]:
        """
        Vrátí všechny nadpisy v dokumentu spolu s jejich úrovní.

        Returns:
            Seznam dvojic ve tvaru (text nadpisu, úroveň).
        """
        ...

    @abstractmethod
    def find_inline_formatting(self) -> list[dict]:
        """
        Najde ruční přímé formátování použité uvnitř textu.

        Returns:
            Seznam nalezených problémů s přímým formátováním.
        """
        ...

    @abstractmethod
    def has_list_level(self, level: int) -> bool:
        """
        Ověří, zda dokument obsahuje seznam na zadané úrovni.

        Args:
            level: Hledaná úroveň seznamu.

        Returns:
            True, pokud je daná úroveň seznamu použita, jinak False.
        """
        ...

    @abstractmethod
    def iter_main_headings(self) -> Iterable[Any]:
        """
        Iteruje hlavní nadpisy dokumentu.

        Returns:
            Iterátor prvků odpovídajících nadpisům první úrovně.
        """
        ...

    @abstractmethod
    def get_visible_text(self, element: Any) -> str:
        """
        Vrátí viditelný text z předaného prvku dokumentu.

        Args:
            element: Prvek dokumentu, ze kterého se má text získat.

        Returns:
            Viditelný text prvku.
        """
        ...

    @abstractmethod
    def heading_starts_on_new_page(self, h: Any) -> bool:
        """
        Ověří, zda nadpis začíná na nové stránce.

        Args:
            h: Prvek reprezentující nadpis.

        Returns:
            True, pokud nadpis začíná na nové stránce, jinak False.
        """
        ...

    @abstractmethod
    def iter_paragraphs(self) -> Iterable[Any]:
        """
        Iteruje všechny odstavce dokumentu.

        Returns:
            Iterátor odstavců dokumentu.
        """
        ...

    @abstractmethod
    def paragraph_is_toc(self, p: Any) -> bool:
        """
        Ověří, zda odstavec patří do obsahu dokumentu.

        Args:
            p: Odstavec k ověření.

        Returns:
            True, pokud odstavec patří do obsahu, jinak False.
        """
        ...

    @abstractmethod
    def paragraph_text_raw(self, p: Any) -> str:
        """
        Vrátí surový text odstavce bez další normalizace.

        Args:
            p: Odstavec, ze kterého se má text získat.

        Returns:
            Surový text odstavce.
        """
        ...

    @abstractmethod
    def paragraph_is_empty(self, p: Any) -> bool:
        """
        Ověří, zda je odstavec prázdný.

        Args:
            p: Odstavec k ověření.

        Returns:
            True, pokud odstavec neobsahuje žádný text, jinak False.
        """
        ...

    @abstractmethod
    def paragraph_has_text(self, p: Any) -> bool:
        """
        Ověří, zda odstavec obsahuje nějaký text.

        Args:
            p: Odstavec k ověření.

        Returns:
            True, pokud odstavec obsahuje text, jinak False.
        """
        ...

    @abstractmethod
    def paragraph_text(self, p: Any) -> str:
        """
        Vrátí text odstavce v běžně používané podobě.

        Args:
            p: Odstavec, ze kterého se má text získat.

        Returns:
            Text odstavce.
        """
        ...

    @abstractmethod
    def paragraph_style_name(self, p: Any) -> str:
        """
        Vrátí název stylu použitého na odstavci.

        Args:
            p: Odstavec, jehož styl se má zjistit.

        Returns:
            Název stylu odstavce.
        """
        ...

    @abstractmethod
    def paragraph_is_generated(self, p: Any) -> bool:
        """
        Ověří, zda je odstavec generovaný automaticky.

        Args:
            p: Odstavec k ověření.

        Returns:
            True, pokud je odstavec generovaný, jinak False.
        """
        ...

    @abstractmethod
    def paragraph_has_spacing_before(self, p: Any) -> bool:
        """
        Ověří, zda má odstavec nastavené odsazení před odstavcem.

        Args:
            p: Odstavec k ověření.

        Returns:
            True, pokud má odstavec spacing before, jinak False.
        """
        ...

    @abstractmethod
    def paragraph_is_heading(self, p: Any) -> bool:
        """
        Ověří, zda odstavec představuje nadpis.

        Args:
            p: Odstavec k ověření.

        Returns:
            True, pokud je odstavec nadpis, jinak False.
        """
        ...

    @abstractmethod
    def get_normal_style(self):
        """
        Vrátí výchozí styl běžného odstavce.

        Returns:
            Výchozí styl odstavce, nebo None pokud není dostupný.
        """
        ...

    @abstractmethod
    def find_html_artifacts(self) -> list[tuple[int, str]]:
        """
        Najde stopy po HTML nebo HTML entitách vložených do textu.

        Returns:
            Seznam dvojic obsahujících číslo odstavce a nalezený text.
        """
        ...

    @abstractmethod
    def find_txt_artifacts(self) -> list[tuple[int, str]]:
        """
        Najde textové artefakty typické pro nečistý import nebo ruční formátování.

        Returns:
            Seznam dvojic obsahujících číslo odstavce a problematický text.
        """
        ...

    @abstractmethod
    def find_pdf_artifacts(self) -> list[tuple[int, str]]:
        """
        Najde stopy po vložení textu z PDF, například tvrdé zalomení řádků.

        Returns:
            Seznam dvojic obsahujících číslo odstavce a problematický text.
        """
        ...

    @abstractmethod
    def toc_level_contains_numbers(self, level: int) -> bool | None:
        """
        Ověří, zda položky obsahu na dané úrovni obsahují číslování.

        Args:
            level: Úroveň obsahu.

        Returns:
            True pokud obsahují čísla, False pokud ne, nebo None pokud úroveň neexistuje.
        """
        ...

    @abstractmethod
    def heading_level_is_numbered(self, level: int) -> bool:
        """
        Ověří, zda je styl nadpisu na dané úrovni číslovaný.

        Args:
            level: Úroveň nadpisu.

        Returns:
            True, pokud je daná úroveň číslovaná, jinak False.
        """
        ...

    @abstractmethod
    def paragraph_has_page_break(self, p: ET.Element) -> bool:
        """
        Ověří, zda má odstavec nastaveno zalomení stránky před odstavcem.

        Args:
            p: XML element odstavce (<w:p>).

        Returns:
            True pokud je zalomení přítomno, jinak False.
        """
        ...

    @abstractmethod
    def paragraph_style_id(self, p: Any) -> str | None:
        """
        Vrátí interní identifikátor stylu odstavce.

        Args:
            p: Odstavec, jehož styl se má zjistit.

        Returns:
            Identifikátor stylu, nebo None pokud odstavec styl nemá.
        """
        ...

    @abstractmethod
    def paragraph_heading_level(self, p: Any) -> int | None:
        """
        Vrátí úroveň nadpisu pro daný odstavec.

        Args:
            p: Odstavec, jehož úroveň se má zjistit.

        Returns:
            Úroveň nadpisu, nebo None pokud odstavec není nadpis.
        """
        ...

    @abstractmethod
    def paragraph_has_numbering(self, p: Any) -> bool:
        """
        Ověří, zda má odstavec číslování nebo odrážky.

        Args:
            p: Odstavec k ověření.

        Returns:
            True, pokud má odstavec číslování, jinak False.
        """
        ...

    @abstractmethod
    def section_count(self) -> int:
        """
        Vrátí počet oddílů v dokumentu.

        Returns:
            Počet oddílů dokumentu.
        """
        ...

    @abstractmethod
    def section_has_header_or_footer_content(self, index: int) -> bool:
        """
        Ověří, zda oddíl obsahuje text nebo pole v záhlaví či zápatí.

        Args:
            index: Index oddílu.

        Returns:
            True, pokud záhlaví nebo zápatí obsahuje nějaký obsah, jinak False.
        """
        ...

    @abstractmethod
    def section_has_header_text(self, index: int) -> bool:
        """
        Ověří, zda oddíl obsahuje text v záhlaví.

        Args:
            index: Index oddílu.

        Returns:
            True, pokud záhlaví obsahuje text, jinak False.
        """
        ...

    @abstractmethod
    def second_section_page_number_starts_at_one(self) -> bool | None:
        """
        Ověří, zda číslování stránek ve druhém oddílu začíná od jedničky.

        Returns:
            True pokud ano, False pokud ne, nebo None pokud druhý oddíl neexistuje.
        """
        ...

    @abstractmethod
    def section_footer_is_empty(self, index: int) -> bool | None:
        """
        Ověří, zda je zápatí oddílu prázdné.

        Args:
            index: Index oddílu.

        Returns:
            True pokud je zápatí prázdné, False pokud obsahuje obsah,
            nebo None pokud oddíl neexistuje.
        """
        ...

    @abstractmethod
    def section_header_is_empty(self, index: int) -> bool | None:
        """
        Ověří, zda je záhlaví oddílu prázdné.

        Args:
            index: Index oddílu.

        Returns:
            True pokud je záhlaví prázdné, False pokud obsahuje obsah,
            nebo None pokud oddíl neexistuje.
        """
        ...

    @abstractmethod
    def footer_is_linked_to_previous(self, index: int) -> bool | None:
        """
        Ověří, zda je zápatí oddílu propojené s předchozím oddílem.

        Args:
            index: Index oddílu.

        Returns:
            True pokud je zápatí propojené, False pokud ne,
            nebo None pokud propojení nelze určit.
        """
        ...

    @abstractmethod
    def header_is_linked_to_previous(self, index: int) -> bool | None:
        """
        Ověří, zda je záhlaví oddílu propojené s předchozím oddílem.

        Args:
            index: Index oddílu.

        Returns:
            True pokud je záhlaví propojené, False pokud ne,
            nebo None pokud propojení nelze určit.
        """
        ...

    @abstractmethod
    def section_footer_has_page_number(self, index: int) -> bool | None:
        """
        Ověří, zda zápatí oddílu obsahuje číslo stránky.

        Args:
            index: Index oddílu.

        Returns:
            True pokud zápatí obsahuje číslo stránky, False pokud ne,
            nebo None pokud oddíl neexistuje.
        """
        ...

    @abstractmethod
    def iter_image_bytes(self) -> Iterator[tuple[str | None, bytes]]:
        """
        Iteruje binární obsah všech obrázků v dokumentu.

        Returns:
            Iterátor bajtů jednotlivých obrázků.
        """
        ...

    @abstractmethod
    def iter_figure_caption_texts(self) -> list[str]:
        """
        Vrátí texty titulků všech obrázků v dokumentu.

        Returns:
            Seznam textů titulků obrázků.
        """
        ...

    @abstractmethod
    def iter_list_of_figures_texts(self) -> list[str]:
        """
        Vrátí texty položek ze seznamu obrázků.

        Returns:
            Seznam textů položek ze seznamu obrázků.
        """
        ...

    @abstractmethod
    def iter_objects(self) -> Iterable[DocumentObject]:
        """
        Iteruje všechny rozpoznané objekty v dokumentu.

        Returns:
            Iterátor objektů dokumentu, například obrázků, tabulek, grafů nebo rovnic.
        """
        ...

    @abstractmethod
    def has_list_of_figures_in_section(self, section_index: int) -> bool:
        """
        Ověří, zda oddíl obsahuje seznam obrázků.

        Args:
            section_index: Index oddílu.

        Returns:
            True, pokud oddíl obsahuje seznam obrázků, jinak False.
        """
        ...

    @abstractmethod
    def object_has_caption(self, obj: DocumentObject, expected_labels=None) -> bool:
        """
        Ověří, zda má objekt titulek s očekávaným návěštím.

        Args:
            obj: Objekt, který se má zkontrolovat.
            expected_labels: Očekávané názvy návěští titulku.

        Returns:
            True, pokud objekt má odpovídající titulek, jinak False.
        """
        ...

    @abstractmethod
    def get_object_caption_text(
        self,
        obj: DocumentObject,
        *,
        accept_manual: bool = False,
    ) -> str | None:
        """
        Vrátí text titulku objektu bez čísla a návěští.

        Args:
            obj: Objekt, jehož titulek se má získat.

        Returns:
            Text titulku, nebo None pokud objekt titulek nemá.
        """
        ...

    @abstractmethod
    def get_object_caption_info(
        self,
        obj,
        *,
        accept_manual: bool = False,
    ) -> ObjectCaptionInfo | None:
        """
        Vrátí informace o titulku zadaného objektu.

        Args:
            obj: Objekt, pro který se má titulek dohledat.
            accept_manual: Určuje, zda se mají uznat i ručně vytvořené titulky.

        Returns:
            Slovník s informacemi o titulku, nebo None pokud titulek nebyl nalezen.
        """
        ...

    @abstractmethod
    def iter_object_crossref_ids(self) -> set[str]:
        """
        Vrátí identifikátory křížových odkazů na objekty v dokumentu.

        Returns:
            Množina identifikátorů odkazů na objekty.
        """
        ...

    @abstractmethod
    def get_object_caption_ref_ids(self, obj: DocumentObject) -> set[str]:
        """
        Vrátí identifikátory bookmarků nebo referencí spojených s titulkem objektu.

        Args:
            obj: Objekt, jehož reference se mají zjistit.

        Returns:
            Množina identifikátorů referencí k titulku objektu.
        """
        ...

    @abstractmethod
    def has_toc_in_section(self, section_index: int) -> bool:
        """
        Ověří, zda oddíl obsahuje obsah dokumentu.

        Args:
            section_index: Index oddílu.

        Returns:
            True, pokud oddíl obsahuje obsah, jinak False.
        """
        ...

    @abstractmethod
    def has_text_in_section(self, section_index: int, min_words: int = 1) -> bool:
        """
        Ověří, zda oddíl obsahuje alespoň minimální množství textu.

        Args:
            section_index: Index oddílu.
            min_words: Minimální počet slov, který se považuje za textový obsah.

        Returns:
            True, pokud oddíl obsahuje dostatek textu, jinak False.
        """
        ...

    @abstractmethod
    def section_missing_styles(
        self, section_index: int, styles: set[str]
    ) -> tuple[bool, list[str]]:
        """
        Ověří, zda jsou v oddílu použité požadované styly.

        Args:
            section_index: Index oddílu.
            styles: Množina očekávaných stylů.

        Returns:
            Dvojici určující, zda jsou všechny styly přítomné, a seznam chybějících stylů.
        """
        ...

    @abstractmethod
    def has_bibliography_in_section(self, section_index: int) -> bool:
        """
        Ověří, zda oddíl obsahuje bibliografii.

        Args:
            section_index: Index oddílu.

        Returns:
            True, pokud oddíl obsahuje bibliografii, jinak False.
        """
        ...

    @abstractmethod
    def has_any_table(self) -> bool:
        """
        Ověří, zda dokument obsahuje alespoň jednu tabulku.

        Returns:
            True, pokud dokument obsahuje tabulku, jinak False.
        """
        ...

    @abstractmethod
    def has_list_of_tables_in_section(self, section_index: int) -> bool:
        """
        Ověří, zda oddíl obsahuje seznam tabulek.

        Args:
            section_index: Index oddílu.

        Returns:
            True, pokud oddíl obsahuje seznam tabulek, jinak False.
        """
        ...

    @abstractmethod
    def section_page_number_starts_at_one(self, section_index: int) -> bool | None:
        """
        Ověří, zda číslování stránek v oddílu začíná od jedničky.

        Args:
            section_index: Index oddílu.

        Returns:
            True pokud číslování začíná od jedničky, False pokud ne,
            nebo None pokud oddíl neexistuje nebo to nelze zjistit.
        """
        ...

    @abstractmethod
    def has_toc(self) -> bool:
        """
        Ověří, zda dokument obsahuje obsah.

        Returns:
            True, pokud dokument obsahuje obsah, jinak False.
        """
        ...

    @abstractmethod
    def iter_toc_items(self) -> Iterable[dict]:
        """
        Iteruje položky obsahu včetně jejich textu a cílového odkazu.

        Returns:
            Iterátor slovníků reprezentujících jednotlivé položky obsahu.
        """
        ...

    @abstractmethod
    def iter_toc_paragraphs(self) -> Iterable[Any]:
        """
        Iteruje odstavce, které patří do obsahu dokumentu.

        Returns:
            Iterátor odstavců obsahu.
        """
        ...

    @abstractmethod
    def iter_section_blocks(self, section_index: int) -> Iterable[Any]:
        """
        Iteruje bloky patřící do zadaného oddílu dokumentu.

        Args:
            section_index: Index oddílu.

        Returns:
            Iterátor bloků z daného oddílu.
        """
        ...

    @abstractmethod
    def normalize_heading_text(self, text: str) -> str:
        """
        Normalizuje text nadpisu pro porovnávání s obsahem.

        Args:
            text: Původní text nadpisu.

        Returns:
            Normalizovaný text nadpisu.
        """
        ...

    @abstractmethod
    def toc_missing_used_headings(
        self, max_level: int = 3
    ) -> tuple[bool | None, list[str]]:
        """
        Ověří, zda obsah obsahuje všechny použité nadpisy do zadané úrovně.

        Args:
            max_level: Nejvyšší úroveň nadpisu, která se má kontrolovat.

        Returns:
            Dvojici určující výsledek kontroly a seznam chybějících nadpisů.
        """
        ...

    @abstractmethod
    def get_toc_illegal_content_errors(
        self,
    ) -> tuple[bool, list[TocIllegalContentError], str | None]:
        """
        Vrátí chyby způsobené nepovoleným obsahem uvnitř obsahu dokumentu.

        Returns:
            Trojici určující existenci obsahu, seznam chyb a doplňkovou zprávu nebo klíč chyby.
        """
        ...

    @abstractmethod
    def has_any_chart(self) -> bool:
        """
        Ověří, zda dokument obsahuje alespoň jeden graf.

        Returns:
            True, pokud dokument obsahuje graf, jinak False.
        """
        ...

    @abstractmethod
    def has_any_equation(self) -> bool:
        """
        Ověří, zda dokument obsahuje alespoň jednu rovnici.

        Returns:
            True, pokud dokument obsahuje rovnici, jinak False.
        """
        ...

    @abstractmethod
    def has_list_of_charts_in_section(self, section_index: int) -> bool:
        """
        Ověří, zda oddíl obsahuje seznam grafů.

        Args:
            section_index: Index oddílu.

        Returns:
            True, pokud oddíl obsahuje seznam grafů, jinak False.
        """
        ...

    @abstractmethod
    def has_list_of_equations_in_section(self, section_index: int) -> bool:
        """
        Ověří, zda oddíl obsahuje seznam rovnic.

        Args:
            section_index: Index oddílu.

        Returns:
            True, pokud oddíl obsahuje seznam rovnic, jinak False.
        """
        ...

    @abstractmethod
    def first_chapter_is_first_content_in_section(self, section_index: int) -> bool:
        """
        Ověří, zda je první nadpis první úrovně prvním skutečným obsahem oddílu.

        Args:
            section_index: Index oddílu.

        Returns:
            True pokud před prvním nadpisem úrovně 1 není žádný text ani tabulka,
            jinak False.
        """
        ...

    @abstractmethod
    def get_text_of_section(self, section_index: int) -> str:
        """
        Vrátí čistý text zadaného oddílu bez generovaných nebo pomocných prvků.

        Args:
            section_index: Index oddílu.

        Returns:
            Text oddílu vhodný pro další porovnávání nebo validaci.
        """
        ...

    @abstractmethod
    def has_bibliography(self) -> bool:
        """
        Ověří, zda dokument obsahuje bibliografii.

        Returns:
            True, pokud dokument obsahuje bibliografii, jinak False.
        """
        ...

    @abstractmethod
    def count_bibliography_items(self) -> int:
        """
        Spočítá počet položek bibliografie v dokumentu.

        Returns:
            Počet nalezených bibliografických položek.
        """
        ...

    @abstractmethod
    def get_unique_citation_tags(self) -> set[str]:
        """
        Vrátí množinu unikátních citačních tagů použitých v dokumentu.

        Returns:
            Množina unikátních citačních tagů.
        """
        ...

    @abstractmethod
    def iter_bibliography_source_tags(self) -> list[str]:
        """
        Vrátí tagy všech zdrojů uvedených v bibliografii.

        Returns:
            Seznam tagů bibliografických zdrojů.
        """
        ...

    @abstractmethod
    def find_duplicate_bibliography_tags(self) -> list[str]:
        """
        Najde duplicitní tagy v bibliografii.

        Returns:
            Seznam duplicitních tagů.
        """
        ...

    @abstractmethod
    def iter_citation_tags_in_order(self):
        """
        Vrátí citační tagy v pořadí jejich výskytu v dokumentu.

        Returns:
            Iterátor nebo seznam citačních tagů v pořadí použití.
        """
        ...

    @abstractmethod
    def iter_bibliography_sources(self) -> list[BibliographySource]:
        """
        Vrátí bibliografické zdroje ve strukturované podobě.

        Returns:
            Seznam bibliografických zdrojů.
        """
        ...

    @abstractmethod
    def find_citations_in_wrong_places(self) -> list[dict]:
        """
        Najde citace umístěné na nevhodných místech dokumentu.

        Returns:
            Seznam nalezených problémů s umístěním citací.
        """
        ...

    @abstractmethod
    def get_object_data_id(self, obj: DocumentObject) -> str | None:
        """
        Vrátí datový identifikátor objektu, pokud je k dispozici.

        Args:
            obj: Objekt, jehož identifikátor se má zjistit.

        Returns:
            Datový identifikátor objektu, nebo None pokud není dostupný.
        """
        ...

    @abstractmethod
    def get_object_image_bytes(self, obj: DocumentObject) -> bytes | None:
        """
        Vrátí binární obsah obrázku pro zadaný objekt.

        Args:
            obj: Objekt typu image.

        Returns:
            Bajty obrázku, nebo None pokud je nelze získat.
        """
        ...

    @abstractmethod
    def get_object_qr_data(self, obj: DocumentObject) -> str | None:
        """
        Pokusí se najít a dekódovat QR kód v zadaném obrázku.

        Args:
            obj: Objekt dokumentu (očekává se obrázek).

        Returns:
            Dekódovaný text z QR kódu, nebo None při neúspěchu (nenalezeno, chyba čtení, chybějící knihovny).
        """
        ...

    @abstractmethod
    def get_full_text(self) -> str:
        """
        Vrátí čistý text celého dokumentu bez křížových odkazů.

        Returns:
            Text všech odstavců dokumentu spojený po řádcích.
        """
        ...
  
    @abstractmethod
    def iter_rendered_bibliography_tags_in_order(self) -> list[str]:
            """
            Vrátí tagy zdrojů v pořadí zobrazené bibliografie.

            Returns:
                Tagy zdrojů v pořadí bibliografie.
            """
            ...

    @abstractmethod
    def iter_bibliography_source_tags_in_order(self) -> list[str]:
            """
            Vrátí tagy zdrojů v pořadí bibliografie.

            Returns:
                Tagy zdrojů v pořadí bibliografie.
            """
            ...

