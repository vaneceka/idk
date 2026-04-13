import zipfile
from pathlib import Path

from checks.base_check import BaseCheck, CheckResult


class WrongSubmittedSpreadsheetFileCheck(BaseCheck):
    code = "S_X05"

    def _detect_spreadsheet_kind(self, path: Path) -> str | None:
        """
        Určí typ tabulkového souboru podle jeho vnitřní struktury.

        Args:
            path: Cesta k souboru.

        Returns:
            "xlsx", "ods" nebo None, pokud typ nelze rozpoznat.
        """
        try:
            with zipfile.ZipFile(path) as z:
                names = set(z.namelist())

                # XLSX
                if "xl/workbook.xml" in names and "[Content_Types].xml" in names:
                    return "xlsx"

                # ODS
                if "mimetype" in names:
                    mt = z.read("mimetype").decode("utf-8", errors="ignore").strip()
                    if "opendocument.spreadsheet" in mt:
                        return "ods"

                return None

        except zipfile.BadZipFile:
            return None
        except Exception:
            return None

    def _is_valid_spreadsheet_structure(self, path: Path, kind: str) -> bool:
        """
        Ověří, zda soubor odpovídá očekávané struktuře tabulkového formátu.

        Args:
            path: Cesta k souboru.
            kind: Očekávaný typ souboru.

        Returns:
            True pokud má soubor platnou strukturu, jinak False.
        """
        try:
            with zipfile.ZipFile(path) as z:
                names = set(z.namelist())

                if kind == "xlsx":
                    return (
                        "xl/workbook.xml" in names
                        and "[Content_Types].xml" in names
                        and any(
                            name.startswith("xl/worksheets/") and name.endswith(".xml")
                            for name in names
                        )
                    )

                if kind == "ods":
                    if "mimetype" not in names or "content.xml" not in names:
                        return False

                    mt = z.read("mimetype").decode("utf-8", errors="ignore").strip()
                    return "opendocument.spreadsheet" in mt

                return False

        except Exception:
            return False

    def run_on_path(self, path: Path) -> CheckResult:
        """
        Ověří, zda odevzdaný soubor je platný tabulkový dokument.

        Args:
            path: Cesta k odevzdanému souboru.

        Returns:
            Výsledek kontroly typu, přípony a struktury souboru.
        """
        if not path:
            return CheckResult(
                False,
                self.msg("missing_path", "Nelze zjistit cestu k odevzdanému souboru."),
                None,
            )

        if not path.exists():
            return CheckResult(
                False,
                self.msg("missing_file", "Odevzdaný soubor nebyl nalezen."),
                None,
            )

        kind = self._detect_spreadsheet_kind(path)
        ext = path.suffix.lower()

        if kind not in ("xlsx", "ods"):
            return CheckResult(
                False,
                self.msg(
                    "wrong_file",
                    "Odevzdán nesprávný soubor ({ext}). Očekáván Excel (.xlsx) nebo Calc (.ods).",
                ).format(ext=ext or "bez přípony"),
                None,
            )

        expected_by_ext = {
            ".xlsx": "xlsx",
            ".ods": "ods",
        }

        expected_kind = expected_by_ext.get(ext)
        if expected_kind is None:
            return CheckResult(
                False,
                self.msg(
                    "wrong_extension",
                    "Soubor má nepodporovanou příponu ({ext}), i když jeho obsah odpovídá tabulce {kind}.",
                ).format(ext=ext or "bez přípony", kind=kind.upper()),
                None,
            )

        if expected_kind != kind:
            return CheckResult(
                False,
                self.msg(
                    "extension_mismatch",
                    "Soubor má příponu {ext}, ale jeho skutečný obsah odpovídá formátu {kind}.",
                ).format(ext=ext, kind=kind.upper()),
                None,
            )

        if not self._is_valid_spreadsheet_structure(path, kind):
            return CheckResult(
                False,
                self.msg(
                    "invalid_structure",
                    "Soubor má správný typ ({kind}), ale je poškozený nebo nemá platnou strukturu.",
                ).format(kind=kind.upper()),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", "Odevzdán správný tabulkový soubor ({kind}).").format(
                kind=kind.upper()
            ),
            0,
        )

    def run(self, document, assignment=None) -> CheckResult:
        path = Path(getattr(document, "path", "") or "")
        return self.run_on_path(path)
