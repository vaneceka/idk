import zipfile
from pathlib import Path

from checks.base_check import BaseCheck, CheckResult


class WrongSubmittedTextFileCheck(BaseCheck):
    code = "T_X05"

    def _detect_text_kind(self, path: Path) -> str | None:
        """
        Určí typ textového souboru podle jeho vnitřní struktury.

        Args:
            path: Cesta k souboru.

        Returns:
            "docx", "odt" nebo None, pokud typ nelze rozpoznat.
        """
        try:
            with zipfile.ZipFile(path) as z:
                names = set(z.namelist())

                if "word/document.xml" in names and "[Content_Types].xml" in names:
                    return "docx"

                if "mimetype" in names:
                    mt = (
                        z.read("mimetype")
                        .decode("utf-8", errors="ignore")
                        .strip()
                        .lower()
                    )
                    if "opendocument.text" in mt:
                        return "odt"

                return None

        except zipfile.BadZipFile:
            return None
        except Exception:
            return None

    def run_on_path(self, path: Path) -> CheckResult:
        """
        Ověří, zda odevzdaný soubor je platný textový dokument.

        Args:
            path: Cesta k odevzdanému souboru.

        Returns:
            Výsledek kontroly typu souboru.
        """
        if not path:
            return CheckResult(
                False,
                self.msg("missing_path", "Nelze zjistit cestu k odevzdanému souboru."),
                None,
            )

        if not path.exists():
            return CheckResult(
                False, self.msg("missing_file", "Odevzdaný soubor nebyl nalezen."), None
            )

        kind = self._detect_text_kind(path)

        if kind not in ("docx", "odt"):
            ext = path.suffix.lower()
            return CheckResult(
                False,
                self.msg(
                    "wrong_file",
                    "Odevzdán nesprávný soubor ({ext}). Očekáván Word (.docx) nebo Writer (.odt).",
                ).format(ext=ext or "bez přípony"),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", "Odevzdán správný textový soubor ({kind}).").format(
                kind=kind.upper()
            ),
            0,
        )

    def run(self, document, assignment=None) -> CheckResult:
        path = Path(getattr(document, "path", "") or "")
        return self.run_on_path(path)
