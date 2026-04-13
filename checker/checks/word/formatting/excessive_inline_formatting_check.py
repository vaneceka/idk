from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import group_inline_formatting_by_text


class ExcessiveInlineFormattingCheck(BaseCheck):
    code = "T_F02"

    MIN_ABSOLUTE_HITS = 12
    MIN_RATIO = 0.20
    MAX_PREVIEW = 8

    def _problem_label(self, code: str) -> str:
        """
        Vrátí textový popis typu problému podle jeho kódu.

        Args:
            code: Kód typu problému.

        Returns:
            Lokalizovaný text problému, nebo původní kód pokud překlad neexistuje.
        """
        return self.msg(f"problem_{code}", code)

    def run(self, document, assignment=None): 
        errors = document.find_inline_formatting() or []
        hits = len(errors)

        if hits == 0:
            return CheckResult(
                True,
                self.msg("ok", "Nenalezeno ruční formátování textu (inline)."),
                0,
                count=0,
            )

        paragraphs = list(document.iter_paragraphs())
        total_paras = len(paragraphs)

        ratio = hits / total_paras if total_paras > 0 else 1.0

        too_much = (hits >= self.MIN_ABSOLUTE_HITS) or (ratio >= self.MIN_RATIO)

        if not too_much:
            msg = self.msg(
                "ok_with_hits",
                "Nalezeno ruční formátování, ale ne v kritické míře (zásahy: {hits}, podíl: {pct:.0f}%).",
            ).format(hits=hits, pct=ratio * 100)
            return CheckResult(True, msg, 0, count=hits)

        grouped = group_inline_formatting_by_text(errors)

        item_tpl = self.msg("item_line", '- Text: "{text}"\n  Zásahy: {problems}')
        preview = [
            item_tpl.format(
                text=(i.get("text", "") or "")[:120],
                problems=", ".join(
                    self._problem_label(problem) for problem in i.get("problems", [])
                ),
            )
            for i in grouped[: self.MAX_PREVIEW]
        ]

        header = self.msg(
            "fail_header",
            "Text je ve velké míře formátován přímo a nikoliv prostřednictvím stylů.",
        )

        stats = [
            self.msg("hits_line", "Ručních zásahů: {hits}").format(hits=hits),
            self.msg("ratio_line", "Podíl zásahů/odstavců: {pct:.0f}%").format(
                pct=ratio * 100
            ),
        ]

        msg = (
            header
            + "\n"
            + "\n".join(stats)
            + "\n\n"
            + self.msg("examples_header", "Ukázky:")
            + "\n"
            + "\n".join(preview)
        )

        return CheckResult(False, msg, None, count=hits)
