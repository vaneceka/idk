from checks.base_check import BaseCheck, CheckResult

class ContentHeadingStyleCheck(BaseCheck):
    code = "T_F08"

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
        
        expected = assignment.styles.get("Content Heading")
        if expected is None:
            return CheckResult(
                True,
                self.msg("skip_no_style", "Zadání styl Content Heading neřeší."),
                0,
            )

        actual = document.get_content_heading_style()

        if actual is None:
            return CheckResult(
                False,
                self.msg("not_found", "Styl Nadpis obsahu nebyl v dokumentu nalezen."),
                None,
            )

        diffs = actual.diff(
            expected, doc_default_size=document.get_doc_default_font_size()
        )

        if diffs:
            header = self.msg("diff_header", "Styl Nadpis obsahu neodpovídá zadání:")
            item_tpl = self.msg("diff_item", "- {diff}")
            message = header + "\n" + "\n".join(item_tpl.format(diff=d) for d in diffs)
            return CheckResult(False, message, None)

        return CheckResult(
            True, self.msg("ok", "Styl Nadpis obsahu odpovídá zadání."), 0
        )
