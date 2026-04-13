from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class CheckMeta:
    code: str
    category: str
    title: str
    description: str
    penalty: int | None = None
    per_occurrence: bool = False


CHECKS: Dict[str, CheckMeta] = {
    # ------------
    # Spreadsheet
    # ------------
    # Obecné
    # NOTE: Není implementováno.
    "S_X01": CheckMeta(
        code="S_X01",
        category="Obecné",
        title="Téma není schváleno/zadáno",
        description="Téma není schváleno/zadáno.",
        penalty=-100,
    ),
    # NOTE: Není implementováno.
    "S_X02": CheckMeta(
        code="S_X02",
        category="Obecné",
        title="Duplicitní téma/data",
        description="Duplicitní téma/data s jiným studentem.",
        penalty=-100,
    ),
    # NOTE: Není implementováno.
    "S_X03": CheckMeta(
        code="S_X03",
        category="Obecné",
        title="Dokument neodpovídá zadání",
        description="Celkově dokument neodpovídá zadání SP2 nebo ZT2.",
        penalty=-100,
    ),
    # NOTE: Není implementováno.
    "S_X04": CheckMeta(
        code="S_X04",
        category="Obecné",
        title="Nedostatečný rozsah",
        description="Rozsah neodpovídá zadání - listy, počet datových řad, počet hodnot datové řady, výpočty/vzorce, funkce, grafy. Rozsah je nižší.",
        penalty=-100,
    ),
    "S_X05": CheckMeta(
        code="S_X05",
        category="Obecné",
        title="Odevzdán nesprávný soubor",
        description="Odevzdán jakýkoliv jiný soubor a nikoliv práce v MS Excel (xls, xlsx) nebo LibreOffice Calc (ods).",
        penalty=-100,
    ),
    # NOTE: Není implementováno.
    "S_X06": CheckMeta(
        code="S_X06",
        category="Obecné",
        title="Podvod / cizí práce / spolupráce",
        description="Odevzdána cizí práce nebo zjištěna jakákoliv forma a míra spolupráce včetně sdílení vlastní práce.",
        penalty=None,
    ),
    # Zpracování dat
    "S_D01": CheckMeta(
        code="S_D01",
        category="Zpracování dat",
        title='Chybí list "zdroj"',
        description='Požadovaný list "zdroj" zcela chybí.',
        penalty=-100,
    ),
    # NOTE: Není implementováno.
    "S_D02": CheckMeta(
        code="S_D02",
        category="Zpracování dat",
        title="Chybí bibliografický záznam",
        description='Chybí bibliografický záznam pramene s daty dle ISO 690 (očekáván je min. jeden) na listu "zdroj".',
        penalty=-100,
    ),
    "S_D03": CheckMeta(
        code="S_D03",
        category="Zpracování dat",
        title='Chybí list "data"',
        description='Požadovaný list "data" zcela chybí.',
        penalty=-100,
    ),
    "S_D04": CheckMeta(
        code="S_D04",
        category="Zpracování dat",
        title="Vzorce nelze kopírovat",
        description="Vzorce nelze kopírovat - relativní adresy buněk, maticové vzorce apod.",
        penalty=-100,
    ),
    "S_D05": CheckMeta(
        code="S_D05",
        category="Zpracování dat",
        title="Chybí výpočet / chybný výpočet",
        description="Zcela chybí výpočet/vzorec, je chybně nebo hodnota vypočtena není.",
        penalty=-10,
        per_occurrence=True,
    ),
    "S_D06": CheckMeta(
        code="S_D06",
        category="Zpracování dat",
        title="Použit maticový vzorec",
        description="Není použit klasický vzorec, ale vzorec maticový - jednobuňkový/vícebuňkový.",
        penalty=-10,
    ),
    "S_D07": CheckMeta(
        code="S_D07",
        category="Zpracování dat",
        title="Použity pojmenované oblasti místo adres",
        description="Nejsou použity adresy buněk nebo oblastí, ale názvem pojmenované oblasti.",
        penalty=-10,
    ),
    "S_D08": CheckMeta(
        code="S_D08",
        category="Zpracování dat",
        title="Nadbytečné absolutní adresy",
        description="Minimálně jedna absolutní část adresy v odkazu nebo vzorci je použita nadbytečně.",
        penalty=-10,
        per_occurrence=True,
    ),
    "S_D09": CheckMeta(
        code="S_D09",
        category="Zpracování dat",
        title="Chybí popisná charakteristika",
        description="Zcela chybí popisná charakteristika.",
        penalty=-100,
    ),
    # NOTE: Není implementováno.
    "S_D10": CheckMeta(
        code="S_D10",
        category="Zpracování dat",
        title="Záhlaví/hodnoty nejsou zkopírovány odkazem",
        description='Záhlaví nebo hodnoty na list "data" nejsou zkopírovány odkazem.',
        penalty=-5,
    ),
    "S_D11": CheckMeta(
        code="S_D11",
        category="Zpracování dat",
        title="Chybí popisná charakteristika datové řady",
        description="Chybí popisná charakteristika pro datovou řadu.",
        penalty=-5,
        per_occurrence=True,
    ),
    # Formátování
    "S_F01": CheckMeta(
        code="S_F01",
        category="Formátování",
        title="Chybné formátování číselných hodnot",
        description="Chybné formátování číselných hodnot - počet desetinných míst, oddělovač tisíců, zarovnání.",
        penalty=-2,
        per_occurrence=True,
    ),
    # NOTE: Není implementováno. Řeší S_F01.
    "S_F02": CheckMeta(
        code="S_F02",
        category="Formátování",
        title="Popisná charakteristika není na 2 desetinná místa",
        description="Hodnoty popisné charakteristiky nejsou formátovány na dvě desetinná místa.",
        penalty=-2,
    ),
    "S_F03": CheckMeta(
        code="S_F03",
        category="Formátování",
        title="Chybí ohraničení tabulky",
        description="Chybí vnitřní/vnější ohraničení tabulky.",
        penalty=-1,
        per_occurrence=True,
    ),
    "S_F04": CheckMeta(
        code="S_F04",
        category="Formátování",
        title="Chybné sloučení buněk",
        description="Chybné sloučení buněk.",
        penalty=-1,
        per_occurrence=True,
    ),
    "S_F05": CheckMeta(
        code="S_F05",
        category="Formátování",
        title="Neformátované záhlaví tabulky",
        description="Není formátováno záhlaví tabulky (řádek nebo sloupec).",
        penalty=-1,
        per_occurrence=True,
    ),
    "S_F06": CheckMeta(
        code="S_F06",
        category="Formátování",
        title="Není zalamování textu v buňce",
        description="Není zalamování textu v buňce.",
        penalty=-1,
        per_occurrence=True,
    ),
    "S_F07": CheckMeta(
        code="S_F07",
        category="Formátování",
        title="Chybí podmíněné formátování",
        description="Chybí podmíněné formátování.",
        penalty=-5,
        per_occurrence=True,
    ),
    "S_F08": CheckMeta(
        code="S_F08",
        category="Formátování",
        title="Podmíněné formátování nefunguje správně",
        description="Podmíněné formátování nefunguje správně.",
        penalty=-2,
        per_occurrence=True,
    ),
    # Graf
    "S_G01": CheckMeta(
        code="S_G01",
        category="Graf",
        title="Chybí požadovaný graf",
        description="Požadovaný graf zcela chybí.",
        penalty=-100,
    ),
    "S_G02": CheckMeta(
        code="S_G02",
        category="Graf",
        title="Použit 3D graf",
        description="Použit 3D graf.",
        penalty=-2,
    ),
    "S_G03": CheckMeta(
        code="S_G03",
        category="Graf",
        title="V grafu chybí popisky",
        description="V grafu chybí (a) název grafu, (b) název/jednotka na ose X, (c) název/jednotka na ose Y, (d) čitelně umístěné popisky dat a volitelně (e) legenda.",
        penalty=-2,
        per_occurrence=True,
    ),
    "S_G04": CheckMeta(
        code="S_G04",
        category="Graf",
        title="Nevhodný typ grafu",
        description="Nevhodný typ grafu.",
        penalty=-5,
        per_occurrence=True,
    ),
    # ------------
    # Text
    # ------------
    # Obecné
    # NOTE: Není implementováno.
    "T_X01": CheckMeta(
        code="T_X01",
        category="Obecné",
        title="Téma není schváleno/zadáno",
        description="Téma není schváleno/zadáno.",
        penalty=-100,
    ),
    # NOTE: Není implementováno.
    "T_X02": CheckMeta(
        code="T_X02",
        category="Obecné",
        title="Duplicitní téma/text s jiným studentem",
        description="Duplicitní téma/text s jiným studentem.",
        penalty=-100,
    ),
    # NOTE: Není implementováno.
    "T_X03": CheckMeta(
        code="T_X03",
        category="Obecné",
        title="Celkově dokument neodpovídá zadání SP1 nebo ZT1",
        description="Celkově dokument neodpovídá zadání SP1 nebo ZT1.",
        penalty=-100,
    ),
    "T_X04": CheckMeta(
        code="T_X04",
        category="Obecné",
        title="Rozsah neodpovídá zadání",
        description="Rozsah neodpovídá zadání - počet stran, nadpisů a jejich úrovní, vložených objektů. Rozsah je nižší, anebo výrazně větší, než požadovaný.",
        penalty=-100,
    ),
    "T_X05": CheckMeta(
        code="T_X05",
        category="Obecné",
        title="Odevzdán nesprávný soubor",
        description="Odevzdán jakýkoliv jiný soubor a nikoliv práce v MS Word (doc, docx) nebo LibreOffice Writer (odt).",
        penalty=-100,
    ),
    # NOTE: Není implementováno.
    "T_X06": CheckMeta(
        code="T_X06",
        category="Obecné",
        title="Podvod / cizí práce / spolupráce",
        description="Odevzdána cizí práce nebo zjištěna jakákoliv forma a míra spolupráce včetně sdílení vlastní práce.",
        penalty=None,
    ),
    # Části/oddíly dokumentu
    "T_C01": CheckMeta(
        code="T_C01",
        category="Části/oddíly dokumentu",
        title="Oddíly zcela chybí",
        description="Oddíly zcela chybí.",
        penalty=-100,
    ),
    "T_C02": CheckMeta(
        code="T_C02",
        category="Části/oddíly dokumentu",
        title="Neexistuje zadaný počet oddílů",
        description="Neexistuje zadaný počet (3) oddílů - je jich více nebo méně.",
        penalty=-10,
    ),
    # NOTE Není impementováno
    "T_C03": CheckMeta(
        code="T_C03",
        category="Části/oddíly dokumentu",
        title="Chybné hranice oddílů",
        description="Chybné hranice oddílů. Oddíl začíná nebo končí jinde než je zadáno.",
        penalty=-10,
    ),
    "T_C04": CheckMeta(
        code="T_C04",
        category="Části/oddíly dokumentu",
        title="V prvním oddílu chybí desky práce",
        description="V prvním oddílu chybí desky práce.",
        penalty=-5,
    ),
    "T_C05": CheckMeta(
        code="T_C05",
        category="Části/oddíly dokumentu",
        title="V prvním oddílu chybí úvodní list nebo zadání",
        description="V prvním oddílu chybí úvodní list nebo zadání.",
        penalty=-5,
    ),
    "T_C06": CheckMeta(
        code="T_C06",
        category="Části/oddíly dokumentu",
        title="V prvním oddílu chybí obsah dokumentu",
        description="V prvním oddílu chybí obsah dokumentu.",
        penalty=-5,
    ),
    "T_C07": CheckMeta(
        code="T_C07",
        category="Části/oddíly dokumentu",
        title="Ve druhém oddílu není celý text dokumentu",
        description="Ve druhém oddílu není celý text dokumentu od první po poslední kapitolu.",
        penalty=-5,
    ),
    "T_C08": CheckMeta(
        code="T_C08",
        category="Části/oddíly dokumentu",
        title="Ve třetím oddílu není seznam obrázků",
        description="Ve třetím oddílu není seznam obrázků.",
        penalty=-5,
    ),
    "T_C09": CheckMeta(
        code="T_C09",
        category="Části/oddíly dokumentu",
        title="Ve třetím oddílu není seznam dalších objektů",
        description="Ve třetím oddílu není seznam dalších objektů (grafy, tabulky, rovnice apod.), nachází-li se v dokumentu.",
        penalty=-5,
        per_occurrence=True,
    ),
    "T_C10": CheckMeta(
        code="T_C10",
        category="Části/oddíly dokumentu",
        title="Ve třetím oddílu není seznam literatury",
        description="Ve třetím oddílu není seznam literatury.",
        penalty=-5,
    ),
    # Formátování textu dokumentu, styly
    "T_F01": CheckMeta(
        code="T_F01",
        category="Formátování textu dokumentu, styly",
        title="Text obsahuje původní formátování / nevhodné zalamování",
        description="Text obsahuje původní formátování (HTML, TXT) nebo nevhodné zalamování řádek/odstavec (PDF) z původního zdroje.",
        penalty=-100,
    ),
    "T_F02": CheckMeta(
        code="T_F02",
        category="Formátování textu dokumentu, styly",
        title="Text je formátován přímo, ne styly",
        description="Text je ve velké míře formátován přímo a nikoliv prostřednictvím stylů.",
        penalty=-100,
    ),
    "T_F03": CheckMeta(
        code="T_F03",
        category="Formátování textu dokumentu, styly",
        title="Styly nejsou důsledně používány",
        description="Styly nejsou důsledně používány. Místy je nekonzistentní/přímé formátování textu (modré vlnovky pod textem, nebo použijte funkci kontrola stylů).",
        penalty=-5,
        per_occurrence=True,
    ),
    "T_F04": CheckMeta(
        code="T_F04",
        category="Formátování textu dokumentu, styly",
        title="Styl Normální není změněn dle zadání",
        description="Styl Normální není změněn dle zadání.",
        penalty=-5,
    ),
    "T_F05": CheckMeta(
        code="T_F05",
        category="Formátování textu dokumentu, styly",
        title="Styl Nadpis 1 není změněn dle zadání",
        description="Styl Nadpis 1 není změněn dle zadání.",
        penalty=-5,
    ),
    "T_F06": CheckMeta(
        code="T_F06",
        category="Formátování textu dokumentu, styly",
        title="Styl Nadpis 2 není změněn dle zadání",
        description="Styl Nadpis 2 není změněn dle zadání.",
        penalty=-5,
    ),
    "T_F07": CheckMeta(
        code="T_F07",
        category="Formátování textu dokumentu, styly",
        title="Styl Nadpis 3 není změněn dle zadání",
        description="Styl Nadpis 3 není změněn dle zadání.",
        penalty=-5,
    ),
    "T_F08": CheckMeta(
        code="T_F08",
        category="Formátování textu dokumentu, styly",
        title="Styl Nadpis obsahu není použit",
        description="Styl Nadpis obsahu není použit.",
        penalty=-1,
    ),
    "T_F09": CheckMeta(
        code="T_F09",
        category="Formátování textu dokumentu, styly",
        title="Styl Seznam s odrážkami  / Číslovaný seznam  není použit",
        description="Styl Seznam s odrážkami  nebo Číslovaný seznam  nejsou použity.",
        penalty=-1,
        per_occurrence=True,
    ),
    "T_F10": CheckMeta(
        code="T_F10",
        category="Formátování textu dokumentu, styly",
        title="Styl Seznam s odrážkami 2 / Číslovaný seznam 2 není použit",
        description="Styl Seznam s odrážkami 2 nebo Číslovaný seznam 2 nejsou použity.",
        penalty=-1,
        per_occurrence=True,
    ),
    "T_F11": CheckMeta(
        code="T_F11",
        category="Formátování textu dokumentu, styly",
        title="Styl Titulek není změněn",
        description="Styl Titulek není změněn.",
        penalty=-1,
    ),
    "T_F12": CheckMeta(
        code="T_F12",
        category="Formátování textu dokumentu, styly",
        title="Styl Bibliografie není změněn",
        description="Styl Bibliografie není změněn.",
        penalty=-1,
    ),
    # NOTE: Není implementováno.
    "T_F13": CheckMeta(
        code="T_F13",
        category="Formátování textu dokumentu, styly",
        title="Jiný požadovaný/existující styl není změněn nebo použit",
        description="Libovolný jiný požadovaný a již existující styl není změněn nebo použit.",
        penalty=-1,
        per_occurrence=True,
    ),
    "T_F14": CheckMeta(
        code="T_F14",
        category="Formátování textu dokumentu, styly",
        title="Nadpisy nemají aktivováno hierarchické číslování",
        description="Nadpisy nemají aktivováno automatické hierarchické číslování (např. 1.1.1.).",
        penalty=-5,
    ),
    "T_F15": CheckMeta(
        code="T_F15",
        category="Formátování textu dokumentu, styly",
        title="Čísla nadpisů se nezobrazují v obsahu (nebo naopak)",
        description="Čísla nadpisů se nezobrazují v obsahu (nebo naopak).",
        penalty=-5,
    ),
    "T_F16": CheckMeta(
        code="T_F16",
        category="Formátování textu dokumentu, styly",
        title="Číslovány jsou i kapitoly, které nemají být číslované",
        description="Číslovány jsou i kapitoly, které mají být bez čísla (obsah, seznamy apod.).",
        penalty=-1,
        per_occurrence=True,
    ),
    # NOTE: Není implementováno.
    "T_F17": CheckMeta(
        code="T_F17",
        category="Formátování textu dokumentu, styly",
        title="Chybí většina požadovaných vlastních stylů",
        description="Chybí většina požadovaných vlastních stylů. Není prokázána jejich znalost.",
        penalty=-100,
    ),
    "T_F18": CheckMeta(
        code="T_F18",
        category="Formátování textu dokumentu, styly",
        title="Chybí / je chybně / není použit požadovaný vlastní styl",
        description="Chybí, je chybně nebo není použit požadovaný vlastní styl.",
        penalty=-2,
        per_occurrence=True,
    ),
    "T_F19": CheckMeta(
        code="T_F19",
        category="Formátování textu dokumentu, styly",
        title="Chybí vlastní styl využívající dědičnost",
        description="Chybí vlastní styl využívající dědičnost vlastností z jiného stylu.",
        penalty=-5,
        per_occurrence=True,
    ),
    "T_F20": CheckMeta(
        code="T_F20",
        category="Formátování textu dokumentu, styly",
        title="Chybí vlastní styl s definovanými tabulátory",
        description="Chybí vlastní styl s definovanými tabulátory.",
        penalty=-2,
    ),
    "T_F21": CheckMeta(
        code="T_F21",
        category="Formátování textu dokumentu, styly",
        title="Hlavní kapitola nezačíná na nové straně",
        description="Hlavní kapitola nezačíná na nové straně.",
        penalty=-2,
        per_occurrence=True,
    ),
    "T_F22": CheckMeta(
        code="T_F22",
        category="Formátování textu dokumentu, styly",
        title="Horizontální přímé formátování textu (mezery/tečky)",
        description="V dokumentu je text horizontálně formátován/pozicován prostřednictvím opakování (mezera, tečky apod.).",
        penalty=-5,
        per_occurrence=True,
    ),
    "T_F23": CheckMeta(
        code="T_F23",
        category="Formátování textu dokumentu, styly",
        title="Vertikální formátování pomocí prázdných řádků",
        description="V dokumentu je text vertikálně formátován prostřednictvím prázdných řádků (např. na další stranu) nebo jsou použity před/za nadpisy/odstavci.",
        penalty=-5,
    ),
    # NOTE Navíc oproti seznamu.
    "T_F24": CheckMeta(
        code="T_F24",
        category="Formátování textu dokumentu, styly",
        title="Styly pro desky práce",
        description="Styly pro desky práce nejsou vytvořeny správne dle zadání",
        penalty=-5,
        per_occurrence=True,
    ),
    # NOTE Navíc oproti seznamu.
    "T_F25": CheckMeta(
        code="T_F25",
        category="Formátování textu dokumentu, styly",
        title="Styly pro úvodní list",
        description="Styly pro úvodní list nejsou vytvořeny správne dle zadání",
        penalty=-5,
        per_occurrence=True,
    ),
    # NOTE Navíc oproti seznamu.
    "T_F26": CheckMeta(
        code="T_F26",
        category="Formátování textu dokumentu, styly",
        title="Nadpisy nejsou použity správně dle seznamu",
        description="Nadpisy nejsou použity správně dle seznamu",
        penalty=-5,
        per_occurrence=True,
    ),
    # Obsah a struktura dokumentu
    "T_O01": CheckMeta(
        code="T_O01",
        category="Obsah a struktura dokumentu",
        title="Obsah zcela chybí",
        description="Obsah zcela chybí.",
        penalty=-100,
    ),
    "T_O02": CheckMeta(
        code="T_O02",
        category="Obsah a struktura dokumentu",
        title="Obsah není aktuální",
        description="Obsah není aktuální.",
        penalty=-5,
    ),
    "T_O03": CheckMeta(
        code="T_O03",
        category="Obsah a struktura dokumentu",
        title="Dokument je chybně strukturovaný",
        description="Dokument je chybně strukturovaný.",
        penalty=-5,
        per_occurrence=True,
    ),
    "T_O04": CheckMeta(
        code="T_O04",
        category="Obsah a struktura dokumentu",
        title="V obsahu chybí nadpisy prvních tří úrovní",
        description="Nadpis prvních tří úrovní v obsahu chybí.",
        penalty=-5,
        per_occurrence=True,
    ),
    "T_O05": CheckMeta(
        code="T_O05",
        category="Obsah a struktura dokumentu",
        title="V obsahu je text z prvního oddílu",
        description="V obsahu je jakýkoliv text z prvního oddílu.",
        penalty=-10,
        per_occurrence=True,
    ),
    "T_O06": CheckMeta(
        code="T_O06",
        category="Obsah a struktura dokumentu",
        title="V obsahu je text nebo objekt, který tam nepatří",
        description="V obsahu je jakýkoliv text nebo vložený objekt, který do obsahu nepatří.",
        penalty=-10,
        per_occurrence=True,
    ),
    "T_O07": CheckMeta(
        code="T_O07",
        category="Obsah a struktura dokumentu",
        title="První kapitola ve druhém oddílu nezačíná na straně 1",
        description="První kapitola ve druhém oddílu nezačíná na straně číslo 1.",
        penalty=-5,
    ),
    "T_O08": CheckMeta(
        code="T_O08",
        category="Obsah a struktura dokumentu",
        title="První kapitola ve třetím oddílu nepokračuje v číslování",
        description="První kapitola ve třetím oddílu nepokračuje v číslování z předchozího oddílu.",
        penalty=-5,
    ),
    # Vkládání objektů, seznam vložených objektů
    "T_V01": CheckMeta(
        code="T_V01",
        category="Vkládání objektů, seznam vložených objektů",
        title="Seznam obrázků zcela chybí",
        description="Seznam obrázků zcela chybí.",
        penalty=-100,
    ),
    "T_V02": CheckMeta(
        code="T_V02",
        category="Vkládání objektů, seznam vložených objektů",
        title="Seznam obrázků není aktuální",
        description="Seznam obrázků není aktuální.",
        penalty=-5,
    ),
    "T_V03": CheckMeta(
        code="T_V03",
        category="Vkládání objektů, seznam vložených objektů",
        title="Není vložen obrázek nebo nemá dostatečné rozlišení",
        description="Není vložen obrázek nebo nemá dostatečné rozlišení (nízká kvalita obrázku znamená viditelné tzv. kostičky nebo rozpitý/rozmazaný text/objekty).",
        penalty=-100,
    ),
    # NOTE: Není implementováno.
    "T_V04": CheckMeta(
        code="T_V04",
        category="Vkládání objektů, seznam vložených objektů",
        title="Chybí další požadovaný objekt",
        description="Není vložen další objekt, byl-li v zadání požadován.",
        penalty=-10,
        per_occurrence=True,
    ),
    "T_V05": CheckMeta(
        code="T_V05",
        category="Vkládání objektů, seznam vložených objektů",
        title="Objekt nemá titulek odpovídajícího typu / je vytvořen ručně",
        description="Vložený objekt nemá titulek odpovídajícího typu (návěští Obrázek, Graf, Tabulka apod.) nebo je vytvořen ručně.",
        penalty=-5,
        per_occurrence=True,
    ),
    "T_V06": CheckMeta(
        code="T_V06",
        category="Vkládání objektů, seznam vložených objektů",
        title="V titulku chybí stručný popis objektu",
        description="V titulku chybí stručný popis objektu.",
        penalty=-5,
        per_occurrence=True,
    ),
    "T_V07": CheckMeta(
        code="T_V07",
        category="Vkládání objektů, seznam vložených objektů",
        title="V textu není křížový odkaz na objekt",
        description="V textu není prostřednictvím křížového odkazu zmíněn vložený objekt.",
        penalty=-1,
        per_occurrence=True,
    ),
    "T_V08": CheckMeta(
        code="T_V08",
        category="Vkládání objektů, seznam vložených objektů",
        title="Objekt není spojen/skupen s titulkem",
        description="Vložený objekt není s titulkem spojen/seskupen.",
        penalty=-1,
        per_occurrence=True,
    ),
    # Literatura a citace
    "T_L01": CheckMeta(
        code="T_L01",
        category="Literatura a citace",
        title="Seznam literatury chybí",
        description="Seznam literatury chybí.",
        penalty=-100,
    ),
    "T_L02": CheckMeta(
        code="T_L02",
        category="Literatura a citace",
        title="Seznam literatury není aktuální",
        description="Seznam literatury není aktuální.",
        penalty=-5,
    ),
    # NOTE: Není implementováno.
    "T_L03": CheckMeta(
        code="T_L03",
        category="Literatura a citace",
        title="Seznam literatury není dle ISO 690",
        description="Seznam literatury není dle ISO 690.",
        penalty=-10,
    ),
    "T_L04": CheckMeta(
        code="T_L04",
        category="Literatura a citace",
        title="Pramen není citován v textu",
        description="Pramen není citován v textu dokumentu.",
        penalty=-1,
        per_occurrence=True,
    ),
    "T_L05": CheckMeta(
        code="T_L05",
        category="Literatura a citace",
        title="Pramen je citován na nevhodném místě",
        description="Pramen je citován na nevhodném místě.",
        penalty=-1,
        per_occurrence=True,
    ),
    # NOTE: Není implementováno.
    "T_L06": CheckMeta(
        code="T_L06",
        category="Literatura a citace",
        title="Seznam literatury je číslovaný, ale pramen s daty není na prvním místě",
        description="Seznam literatury je číslovaný, ale pramen s daty není na prvním místě.",
        penalty=-1,
    ),
    "T_L07": CheckMeta(
        code="T_L07",
        category="Literatura a citace",
        title="Online pramen nemá správně vyplněné URL",
        description="Použitý online pramen nemá řádně vyplněno URL (např. nefunguje, uvedena jen doména (radiologieplzen.eu), vyhledávač (google.com) nebo pouhé Internet).",
        penalty=-10,
        per_occurrence=True,
    ),
    "T_L08": CheckMeta(
        code="T_L08",
        category="Literatura a citace",
        title="Použitý pramen nemá vyplněna bibliografická pole",
        description="Použitý pramen nemá řádně vyplněna všechna bibliografická pole pro daný typ dokumentu.",
        penalty=-100,
    ),
    # Záhlaví a zápatí, číslování stran
    "T_Z01": CheckMeta(
        code="T_Z01",
        category="Záhlaví a zápatí, číslování stran",
        title="Záhlaví v dokumentu není řešeno",
        description="Záhlaví v dokumentu není řešeno.",
        penalty=-30,
    ),
    "T_Z02": CheckMeta(
        code="T_Z02",
        category="Záhlaví a zápatí, číslování stran",
        title="První oddíl nemá prázdné záhlaví",
        description="První oddíl nemá prázdné záhlaví.",
        penalty=-2,
    ),
    "T_Z03": CheckMeta(
        code="T_Z03",
        category="Záhlaví a zápatí, číslování stran",
        title="První oddíl nemá prázdné zápatí",
        description="První oddíl nemá prázdné zápatí.",
        penalty=-2,
    ),
    "T_Z04": CheckMeta(
        code="T_Z04",
        category="Záhlaví a zápatí, číslování stran",
        title="Druhý oddíl je propojen s předchozím v záhlaví",
        description="Druhý oddíl je propojen s předchozím oddílem v záhlaví.",
        penalty=-2,
    ),
    "T_Z05": CheckMeta(
        code="T_Z05",
        category="Záhlaví a zápatí, číslování stran",
        title="Druhý oddíl je propojen s předchozím v zápatí",
        description="Druhý oddíl je propojen s předchozím oddílem v zápatí.",
        penalty=-2,
    ),
    "T_Z06": CheckMeta(
        code="T_Z06",
        category="Záhlaví a zápatí, číslování stran",
        title="Druhý oddíl nemá požadovaný text v záhlaví",
        description="Druhý oddíl nemá požadovaný text v záhlaví.",
        penalty=-2,
    ),
    "T_Z07": CheckMeta(
        code="T_Z07",
        category="Záhlaví a zápatí, číslování stran",
        title="Druhý oddíl nemá číslo strany v zápatí",
        description="Druhý oddíl nemá požadovaný text v zápatí (číslo strany).",
        penalty=-2,
    ),
    "T_Z08": CheckMeta(
        code="T_Z08",
        category="Záhlaví a zápatí, číslování stran",
        title="Druhý oddíl nemá číslování stran od 1",
        description="Druhý oddíl nemá číslo strany od 1.",
        penalty=-5,
    ),
    "T_Z09": CheckMeta(
        code="T_Z09",
        category="Záhlaví a zápatí, číslování stran",
        title="Třetí oddíl je propojen s předchozím v záhlaví",
        description="Třetí oddíl je propojen s předchozím oddílem v záhlaví.",
        penalty=-2,
    ),
    "T_Z10": CheckMeta(
        code="T_Z10",
        category="Záhlaví a zápatí, číslování stran",
        title="Třetí oddíl je propojen s předchozím v zápatí",
        description="Třetí oddíl je propojen s předchozím oddílem v zápatí.",
        penalty=-2,
    ),
    "T_Z11": CheckMeta(
        code="T_Z11",
        category="Záhlaví a zápatí, číslování stran",
        title="Třetí oddíl nemá prázdné záhlaví",
        description="Třetí oddíl nemá prázdné záhlaví.",
        penalty=-2,
    ),
    "T_Z12": CheckMeta(
        code="T_Z12",
        category="Záhlaví a zápatí, číslování stran",
        title="Třetí oddíl nemá číslo strany v zápatí",
        description="Třetí oddíl nemá požadovaný text v zápatí (číslo strany).",
        penalty=-2,
    ),
}


def get_check_meta(code: str) -> Optional[CheckMeta]:
    """
    Vrátí metadata kontroly podle jejího kódu.

    Args:
        code: Kód kontroly.

    Returns:
        Metadata kontroly, nebo None pokud kód neexistuje.
    """
    return CHECKS.get(code)
