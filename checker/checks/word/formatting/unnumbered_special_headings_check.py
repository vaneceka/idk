import re

from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import normalize_spaces

class UnnumberedSpecialHeadingsCheck(BaseCheck):
    code = "T_F16"

    SPECIAL_TITLES = {
        "obsah",
        "table of contents",
        "bibliografie",
        "bibliography",
        "seznam literatury",
        "list of references",
        "references",
        "seznam použité literatury",
        "seznam obrázků",
        "list of figures",
        "seznam tabulek",
        "list of tables",
    }

    _MANUAL_NUM_PREFIX_RE = re.compile(
        r"^\s*(?:\d+(?:\.\d+)*|[ivxlcdm]+)\s*[\.\)\-:]?\s+", re.IGNORECASE
    )

    def _norm_title(self, text: str) -> str:
        """
        Normalizuje text nadpisu pro porovnání.

        Args:
            text: Text nadpisu.

        Returns:
            Normalizovaný text bez ručního číslování na začátku.
        """
        t = normalize_spaces((text or "").lower())
        t = self._MANUAL_NUM_PREFIX_RE.sub("", t)
        return t.strip()

    def _has_manual_number_prefix(self, text: str) -> bool:
        """
        Ověří, zda text začíná ručně napsaným číslováním.

        Args:
            text: Text ke kontrole.

        Returns:
            True pokud text obsahuje ruční číselnou předponu, jinak False.
        """
        return bool(self._MANUAL_NUM_PREFIX_RE.match(text or ""))

    def run(self, document, assignment=None):
        errors = set()

        item_style_tpl = self.msg("item_line_style", "- {text} (styl {style})")

        for p in document.iter_paragraphs():
            text = (document.paragraph_text(p) or "").strip()
            if not text:
                continue

            norm = self._norm_title(text)
            if norm not in self.SPECIAL_TITLES:
                continue

            style_id = (document.paragraph_style_id(p) or "").strip()

            is_numbered = (
                document.paragraph_has_numbering(p)
                or self._has_manual_number_prefix(text)
            )

            if is_numbered:
                errors.add(
                    item_style_tpl.format(
                        text=text,
                        style=style_id or "bez stylu",
                    )
                )

        if errors:
            msg = (
                self.msg(
                    "errors_header", "Následující speciální kapitoly jsou číslované:"
                )
                + "\n"
                + "\n".join(sorted(errors))
            )
            return CheckResult(False, msg, None)

        return CheckResult(
            True, self.msg("ok", "Speciální kapitoly nejsou číslované."), 0
        )