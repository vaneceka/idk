import re

from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import normalize_spaces


class ListOfFiguresNotUpdatedCheck(BaseCheck):
    code = "T_V02"
    MAX_ITEMS = 10

    def _norm_figure_text(self, s: str) -> str:
        """
        Normalizuje text titulku nebo položky seznamu obrázků pro porovnání.

        Args:
            s: Vstupní text (titulek obrázku nebo položka ze seznamu obrázků).

        Returns:
            Upravený text připravený k porovnávání.
        """
        s = (s or "").lower()
        s = normalize_spaces(s)
        s = re.sub(
            r"^(obrázek|figure)\s+(\d+)\s*[:.\-–]?\s*",
            r"\1 \2 ",
            s,
            flags=re.IGNORECASE,
        )
        return s.strip()

    def run(self, document, assignment=None):
        raw_captions = [x for x in document.iter_figure_caption_texts() if x]
        raw_lof_items = [x for x in document.iter_list_of_figures_texts() if x]
        
        has_lof = any(
            document.has_list_of_figures_in_section(i)
            for i in range(document.section_count())
        )

        if not raw_lof_items:
            if has_lof:
                return CheckResult(
                    True,
                    self.msg(
                        "skip_unreadable_lof",
                        "Seznam obrázků existuje, ale nepodařilo se načíst jeho položky - aktuálnost se nekontroluje.",
                    ),
                    0,
                )

            return CheckResult(
                True,
                self.msg(
                    "skip_missing_lof",
                    "Seznam obrázků v dokumentu chybí - aktuálnost se nekontroluje.",
                ),
                0,
            )

        captions = [(raw, self._norm_figure_text(raw)) for raw in raw_captions]
        lof_items = [(raw, self._norm_figure_text(raw)) for raw in raw_lof_items]
        
        missing = []
        for raw_caption, norm_caption in captions:
            found = any(norm_caption == norm_lof for _, norm_lof in lof_items)
            if not found:
                missing.append(raw_caption)

        extra = []
        for raw_lof, norm_lof in lof_items:
            found = any(norm_lof == norm_caption for _, norm_caption in captions)
            if not found:
                extra.append(raw_lof)

        if missing or extra:
            parts = []

            if missing:
                parts.append(
                    self.msg(
                        "missing_count", "V seznamu obrázků chybí {n} položek."
                    ).format(n=len(missing))
                )
                parts.append(self.msg("missing_header", "Chybějící položky:"))
                parts.extend(f"- {x}" for x in missing[: self.MAX_ITEMS])

                if len(missing) > self.MAX_ITEMS:
                    parts.append(
                        self.msg(
                            "missing_more", "... a dalších {n} chybějících položek."
                        ).format(n=len(missing) - self.MAX_ITEMS)
                    )

            if extra:
                parts.append(
                    self.msg(
                        "extra_count", "Seznam obrázků obsahuje {n} neplatných položek."
                    ).format(n=len(extra))
                )
                parts.append(self.msg("extra_header", "Neplatné položky navíc:"))
                parts.extend(f"- {x}" for x in extra[: self.MAX_ITEMS])

                if len(extra) > self.MAX_ITEMS:
                    parts.append(
                        self.msg(
                            "extra_more", "... a dalších {n} neplatných položek."
                        ).format(n=len(extra) - self.MAX_ITEMS)
                    )

            return CheckResult(
                False,
                self.msg("errors_header", "Seznam obrázků není aktuální:")
                + "\n"
                + "\n".join(parts),
                None,
            )

        return CheckResult(True, self.msg("ok", "Seznam obrázků je aktuální."), 0)
