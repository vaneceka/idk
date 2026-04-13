from checks.base_check import BaseCheck, CheckResult


class BibliographyStyleCheck(BaseCheck):
    code = "T_F12"

    def run(self, document, assignment=None):
        if assignment is None:
            return CheckResult(
                True,
                self.msg(
                    "skip_no_assignment",
                    "Chybí assignment - check přeskočen.",
                ),
                0,
            )
        expected = assignment.styles.get("Bibliography")
        if expected is None:
            return CheckResult(
                True,
                self.msg("skip_no_requirement", "Zadání styl Bibliografie neřeší."),
                0,
            )

        actual = document.get_bibliography_style()

        if actual is None:
            return CheckResult(
                False,
                self.msg(
                    "missing_style", "Styl Bibliografie nebyl v dokumentu nalezen."
                ),
                None,
            )

        diffs = actual.diff(
            expected, doc_default_size=document.get_doc_default_font_size()
        )

        if diffs:
            header = self.msg("diff_header", "Styl Bibliografie neodpovídá zadání:")
            item_tpl = self.msg("diff_item", "- {diff}")
            msg = header + "\n" + "\n".join(item_tpl.format(diff=d) for d in diffs)
            return CheckResult(False, msg, None)

        return CheckResult(
            True, self.msg("ok", "Styl Bibliografie odpovídá zadání."), 0
        )
