import re

from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import normalize_spaces


class TOCUpToDateCheck(BaseCheck):
    code = "T_O02"

    ALLOWED_EXTRA_TOC_ITEMS = {
        "bibliografie",
        "seznam literatury",
        "literatura",
    }

    def _norm(self, text: str) -> str:
        """
        Normalizuje text pro porovnání odstraněním číslování a nadbytečných mezer.

        Args:
            text: Vstupní text.

        Returns:
            Upravený text v malých písmenech bez číslování na začátku a čísla na konci.
        """
        if not text:
            return ""

        text = text.lower()
        text = normalize_spaces(text)
        text = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s*", "", text)
        text = re.sub(r"\s*\d+\s*$", "", text)

        return text.strip()

    def run(self, document, assignment=None):
        if not document.has_toc():
            return CheckResult(
                True,
                self.msg("no_toc", "Obsah neexistuje - nelze ověřit aktuálnost."),
                0,
            )

        headings = set()

        for text, level in document.iter_headings():
            if 1 <= level <= 3:
                headings.add(self._norm(text))

        if not headings:
            return CheckResult(
                True,
                self.msg(
                    "no_headings", "Dokument nemá nadpisy - obsah nelze posoudit."
                ),
                0,
            )

        toc_items = set()
        for item in document.iter_toc_items():
            raw = item.get("text", "")
            norm = self._norm(raw)
            if norm and norm != "obsah":
                toc_items.add(norm)

        allowed = {t.lower() for t in self.ALLOWED_EXTRA_TOC_ITEMS}

        missing = sorted(h for h in headings if h not in toc_items)
        extra = sorted(t for t in toc_items if t not in headings and t not in allowed)

        if not missing and not extra:
            return CheckResult(True, self.msg("ok", "Obsah je aktuální."), 0)

        item_tpl = self.msg("item_line", "- {text}")
        gap = self.msg("section_gap", "")

        lines = []
        if missing:
            lines.append(self.msg("missing_header", "V obsahu chybí nadpisy:"))
            lines += [item_tpl.format(text=t) for t in missing]

        if extra:
            if lines and gap:
                lines.append(gap)
            lines.append(self.msg("extra_header", "V obsahu jsou nadpisy navíc:"))
            lines += [item_tpl.format(text=t) for t in extra]

        return CheckResult(
            False,
            self.msg("errors_header", "Obsah pravděpodobně není aktuální:")
            + "\n"
            + "\n".join(lines),
            None,
        )
