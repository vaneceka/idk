from checks.base_check import BaseCheck, CheckResult


class OriginalFormattingCheck(BaseCheck):
    code = "T_F01"
    PREVIEW_LEN = 100
    MAX_EXAMPLES = 5

    def _format_examples(self, hits) -> str:
        """
        Připraví ukázky nalezených problematických odstavců.

        Args:
            hits: Seznam dvojic (index odstavce, text).

        Returns:
            Textový přehled několika ukázek.
        """
        return "\n".join(
            f'- text: "{text[:self.PREVIEW_LEN]}"'
            for i, text in hits[: self.MAX_EXAMPLES]
        )

    def run(self, document, assignment=None):
        if assignment:
            return CheckResult(True, self.msg("ok", "Text neobsahuje původní formátování."), 0)

        problems = []

        html_hits = document.find_html_artifacts()
        if html_hits:
            examples = self._format_examples(html_hits)
            problems.append(
                self.msg(
                    "html",
                    "Detekovány HTML/XML značky nebo entity (např. &nbsp;, <tag>). Nalezeno: {count}\nUkázky:\n{examples}",
                ).format(count=len(html_hits), examples=examples)
            )

        txt_hits = document.find_txt_artifacts()
        if txt_hits:
            examples = self._format_examples(txt_hits)
            problems.append(
                self.msg(
                    "txt",
                    "Detekovány TXT artefakty (pseudo odrážky, taby, divné mezery, ASCII děliče). Nalezeno: {count}\nUkázky:\n{examples}",
                ).format(count=len(txt_hits), examples=examples)
            )

        pdf_hits = document.find_pdf_artifacts()
        if pdf_hits:
            examples = self._format_examples(pdf_hits)
            problems.append(
                self.msg(
                    "pdf",
                    "Detekováno nevhodné zalamování řádků/odstavců (typické pro PDF paste). Nalezeno: {count}\nUkázky:\n{examples}",
                ).format(count=len(pdf_hits), examples=examples)
            )

        if problems:
            item_tpl = self.msg("item", "- {problem}")
            msg = (
                self.msg(
                    "errors_header",
                    "Bylo detekováno původní formátování (HTML/TXT/PDF):",
                )
                + "\n"
                + "\n".join(item_tpl.format(problem=p) for p in problems)
            )
            return CheckResult(False, msg, None)

        return CheckResult(
            True, self.msg("ok", "Text neobsahuje původní formátování."), 0
        )