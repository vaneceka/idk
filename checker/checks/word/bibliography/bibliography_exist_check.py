from checks.base_check import BaseCheck, CheckResult


class MissingBibliographyCheck(BaseCheck):
    code = "T_L01"

    def run(self, document, assignment=None):
        if not document.has_bibliography():
            return CheckResult(
                False,
                self.msg("missing", "Seznam literatury chybí."),
                None,
            )

        items = int(document.count_bibliography_items() or 0)
        if items <= 0:
            return CheckResult(
                False,
                self.msg("empty", "Seznam literatury je prázdný."),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", "Seznam literatury je v dokumentu přítomen."),
            0,
        )
