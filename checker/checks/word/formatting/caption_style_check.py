from checks.base_check import BaseCheck, CheckResult


class CaptionStyleCheck(BaseCheck):
    code = "T_F11"

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
        expected = assignment.styles.get("Caption")
        if expected is None:
            return CheckResult(
                True,
                self.msg("skip_no_requirement", "Zadání styl Titulek/Caption neřeší."),
                0,
            )

        actual = document.get_style_by_any_name(
            ["Caption", "Titulek"], default_alignment="start"
        )

        if actual is None:
            return CheckResult(
                True,
                self.msg(
                    "not_modified_default",
                    "Styl Caption nebyl v dokumentu upraven - používá se výchozí styl LibreOffice.",
                ),
                0,
            )

        diffs = actual.diff(
            expected, doc_default_size=document.get_doc_default_font_size()
        )

        if diffs:
            header = self.msg(
                "diff_header", "Styl Titulek (Caption) neodpovídá zadání:"
            )
            item_tpl = self.msg("diff_item", "- {diff}")
            msg = header + "\n" + "\n".join(item_tpl.format(diff=d) for d in diffs)
            return CheckResult(False, msg, None)

        return CheckResult(
            True, self.msg("ok", "Styl Titulek (Caption) odpovídá zadání."), 0
        )
