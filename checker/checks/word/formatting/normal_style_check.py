from checks.base_check import BaseCheck, CheckResult


class NormalStyleCheck(BaseCheck):
    code = "T_F04"

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


        expected = assignment.styles.get("Normal")
        actual = document.get_normal_style()

        if actual is None:
            return CheckResult(
                False,
                self.msg("missing_style", "Definice stylu Normal nebyla nalezena."),
                None,
            )

        diffs = actual.diff(expected)

        if diffs:
            item_tpl = self.msg("diff_item", "- {diff}")
            message = (
                self.msg("diff_header", "Styl Normal neodpovídá zadání:")
                + "\n"
                + "\n".join(item_tpl.format(diff=d) for d in diffs)
            )
        else:
            message = self.msg("diff_header", "Styl Normal neodpovídá zadání.")

        if not actual.matches(expected):
            return CheckResult(False, message, None)

        return CheckResult(
            True, self.msg("ok", "Styl Normal je nastaven správně dle zadání."), 0
        )
