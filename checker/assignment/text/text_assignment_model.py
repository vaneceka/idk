from dataclasses import dataclass
from typing import Dict, List


@dataclass
class StyleSpec:
    """
    Reprezentuje specifikaci stylu textu pro kontrolu textového dokumentu.

    Attributes:
        name: Název stylu.
        font: Očekávaný název písma.
        size: Očekávaná velikost písma.
        bold: Určuje, zda má být text tučný.
        italic: Určuje, zda má být text kurzívou.
        allCaps: Určuje, zda má být text psán verzálkami.
        color: Očekávaná barva textu.
        alignment: Očekávané zarovnání odstavce.
        lineHeight: Očekávaná výška řádku.
        pageBreakBefore: Určuje, zda má být před odstavcem zalomení stránky.
        isNumbered: Určuje, zda má být styl číslovaný.
        numLevel: Očekávaná úroveň číslování.
        basedOn: Název nadřazeného stylu.
        spaceBefore: Očekávané odsazení před odstavcem.
        tabs: Očekávané tabulátory ve tvaru (zarovnání, pozice).
    """

    TAB_TOLERANCE = 5
    SPACE_TOLERANCE = 20
    INDENT_TOLERANCE = 20

    name: str
    font: str | None = None
    size: float | None = None
    bold: bool | None = None
    italic: bool | None = None
    allCaps: bool | None = None
    color: str | None = None
    alignment: str | None = None
    lineHeight: float | None = None
    pageBreakBefore: bool | None = None
    isNumbered: bool | None = None
    numLevel: int | None = None
    basedOn: str | None = None
    spaceBefore: int | None = None
    tabs: list[tuple[str, int]] | None = None

    def _int_close(self, a: int | None, b: int | None, tol: int) -> bool:
        """
        Porovná dvě celočíselné hodnoty s tolerancí.

        Args:
            a: První hodnota.
            b: Druhá hodnota.
            tol: Povolená tolerance rozdílu.

        Returns:
            True, pokud jsou hodnoty v rámci tolerance nebo obě None, jinak False.
        """
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return abs(a - b) <= tol

    def _tabs_close(
        self,
        actual: list[tuple[str, int]] | None,
        expected: list[tuple[str, int]] | None,
        tol: int = TAB_TOLERANCE,
    ) -> bool:
        """
        Porovná seznamy tabulátorů s tolerancí pozice.

        Args:
            actual: Skutečně nalezené tabulátory.
            expected: Očekávané tabulátory.
            tol: Povolená tolerance rozdílu pozice.

        Returns:
            True, pokud se seznamy tabulátorů shodují v zarovnání,
            počtu i pozicích v rámci tolerance, jinak False.
        """
        if actual is None and expected is None:
            return True
        if actual is None or expected is None:
            return False
        if len(actual) != len(expected):
            return False

        for (a_align, a_pos), (e_align, e_pos) in zip(actual, expected):
            if a_align != e_align:
                return False
            if abs(a_pos - e_pos) > tol:
                return False

        return True

    def _norm_alignment(self, v: str | None) -> str | None:
        """
        Normalizuje hodnotu zarovnání textu pro porovnání.

        Args:
            v: Hodnota zarovnání.

        Returns:
            Normalizovaná hodnota zarovnání nebo None.
        """
        if v is None:
            return None
        vv = v.strip().lower()
        norm = {"left": "start", "right": "end"}
        return norm.get(vv, vv)

    def _compare_field(
        self,
        field: str,
        actual,
        expected,
        ignore: set[str],
        diffs: list[str],
    ) -> None:
        """
        Porovná jednu vlastnost stylu a případný rozdíl přidá do seznamu.

        Args:
            field: Název porovnávané vlastnosti.
            actual: Skutečná hodnota vlastnosti.
            expected: Očekávaná hodnota vlastnosti.
            ignore: Množina názvů polí, která se nemají porovnávat.
            diffs: Seznam nalezených rozdílů.
        """
        if field in ignore:
            return
        if expected is None:
            return
        if actual != expected:
            diffs.append(f"{field}: očekáváno {expected}, nalezeno {actual}")

    def diff(
        self,
        expected: "StyleSpec",
        *,
        doc_default_size: int | None = None,
        ignore_fields: set[str] | None = None,
    ) -> list[str]:
        """
        Porovná aktuální styl s očekávaným stylem a vrátí seznam rozdílů.

        Args:
            expected: Očekávaná specifikace stylu.
            doc_default_size: Výchozí velikost písma dokumentu.
            ignore_fields: Množina názvů polí, která se nemají porovnávat.

        Returns:
            Seznam textových popisů nalezených rozdílů.
        """
        if expected is None:
            return []

        ignore = {"name"} if ignore_fields is None else ignore_fields
        diffs: list[str] = []

        if "spaceBefore" not in ignore and expected.spaceBefore is not None:
            if not self._int_close(
                self.spaceBefore, expected.spaceBefore, self.SPACE_TOLERANCE
            ):
                diffs.append(
                    f"spaceBefore: očekáváno {expected.spaceBefore}, nalezeno {self.spaceBefore}"
                )

        if "tabs" not in ignore and expected.tabs is not None:
            if not self._tabs_close(self.tabs, expected.tabs):
                diffs.append(f"tabs: očekáváno {expected.tabs}, nalezeno {self.tabs}")

        if "size" not in ignore and expected.size is not None:
            if self.size is None:
                if doc_default_size != expected.size:
                    diffs.append(
                        f"size: očekáváno {expected.size}, default dokumentu je {doc_default_size}"
                    )
            elif self.size != expected.size:
                diffs.append(f"size: očekáváno {expected.size}, nalezeno {self.size}")

        if "alignment" not in ignore and expected.alignment is not None:
            act = self._norm_alignment(self.alignment)
            exp = self._norm_alignment(expected.alignment)
            if act != exp:
                diffs.append(
                    f"alignment: očekáváno {expected.alignment}, nalezeno {self.alignment}"
                )

        self._compare_field("font", self.font, expected.font, ignore, diffs)
        self._compare_field("bold", self.bold, expected.bold, ignore, diffs)
        self._compare_field("italic", self.italic, expected.italic, ignore, diffs)
        self._compare_field("allCaps", self.allCaps, expected.allCaps, ignore, diffs)
        self._compare_field("color", self.color, expected.color, ignore, diffs)
        self._compare_field(
            "lineHeight", self.lineHeight, expected.lineHeight, ignore, diffs
        )
        self._compare_field(
            "pageBreakBefore",
            self.pageBreakBefore,
            expected.pageBreakBefore,
            ignore,
            diffs,
        )
        self._compare_field(
            "isNumbered", self.isNumbered, expected.isNumbered, ignore, diffs
        )
        self._compare_field("numLevel", self.numLevel, expected.numLevel, ignore, diffs)
        self._compare_field("basedOn", self.basedOn, expected.basedOn, ignore, diffs)

        return diffs

    def matches(
        self,
        expected: "StyleSpec",
        *,
        doc_default_size: int | None = None,
    ) -> bool:
        """
        Ověří, zda aktuální styl odpovídá očekávanému stylu.

        Args:
            expected: Očekávaná specifikace stylu.
            doc_default_size: Výchozí velikost písma dokumentu.

        Returns:
            True, pokud styl odpovídá očekávané specifikaci, jinak False.
        """
        return len(self.diff(expected, doc_default_size=doc_default_size)) == 0


@dataclass
class TextAssignment:
    """
    Reprezentuje celé zadání pro kontrolu textového dokumentu.

    Attributes:
        styles: Mapa názvů stylů na jejich očekávané specifikace.
        headlines: Seznam pravidel pro kontrolu nadpisů.
        objects: Seznam pravidel pro kontrolu objektů v dokumentu.
        bibliography: Seznam pravidel pro kontrolu bibliografie.
    """

    styles: Dict[str, StyleSpec]
    headlines: List[dict]
    objects: List[dict]
    bibliography: List[dict]
