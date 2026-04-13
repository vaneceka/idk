from dataclasses import dataclass
from xml.etree.ElementTree import Element

@dataclass
class BibliographySource:
    """
    Uchovává bibliografický zdroj ve strukturované podobě.

    Attributes:
        tag: Identifikátor nebo značka zdroje.
        type: Typ bibliografického zdroje.
        author: Autor zdroje.
        title: Název zdroje.
        year: Rok vydání.
        publisher: Vydavatel zdroje.
        address: Místo vydání nebo adresa zdroje.
        isbn: ISBN identifikátor zdroje.
        ref_order: Pořadí zdroje v seznamu referencí.
        url: Internetová adresa zdroje.
        journal: Název časopisu.
        volume: Označení svazku.
        number: Číslo vydání.
        pages: Rozsah stran.
        note: Doplňující poznámka ke zdroji.
        access_date: Datum přístupu k online zdroji.
    """

    tag: str
    type: str
    author: str
    title: str
    year: str
    publisher: str
    address: str
    isbn: str
    ref_order: str
    url: str
    journal: str
    volume: str
    number: str
    pages: str
    note: str
    access_date: str


@dataclass
class DocumentObject:
    """
    Reprezentuje rozpoznaný objekt dokumentu, například obrázek, tabulku nebo graf.

    Attributes:
        type: Typ objektu dokumentu.
        element: XML element reprezentující objekt.
        drawing: XML element kresby navázaný na objekt.
        href: Odkaz na externí nebo vložený obsah objektu.
    """

    type: str
    element: Element
    drawing: Element | None = None
    href: str | None = None


@dataclass
class TocIllegalContentError:
    """
    Reprezentuje chybu nalezenou v nepovoleném obsahu uvnitř obsahu dokumentu.

    Attributes:
        code: Kód identifikující typ chyby.
        params: Parametry použité pro sestavení chybové zprávy.
    """

    code: str
    params: dict[str, str]

@dataclass
class ObjectCaptionInfo:
    """
    Uchovává informace o titulku objektu.

    Attributes:
        label: Návěští titulku, například Obrázek, Graf nebo Tabulka.
        text: Viditelný text titulku.
        is_seq: Určuje, zda je titulek vytvořen pomocí pole SEQ.
        is_manual: Určuje, zda je titulek vytvořen ručně.
    """

    label: str | None
    text: str | None
    is_seq: bool
    is_manual: bool