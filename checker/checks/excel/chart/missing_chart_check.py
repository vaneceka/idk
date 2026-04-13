from checks.base_check import BaseCheck, CheckResult


class MissingChartCheck(BaseCheck):
    code = "S_G01"
    SHEET = "data"

    def run(self, document, assignment=None):
        if assignment is None or not assignment.chart:
            return CheckResult(
                True, self.msg("skip_no_chart", "Zadání graf nevyžaduje."), 0
            )

        if not document.has_chart(self.SHEET):
            return CheckResult(
                False,
                self.msg("missing_chart", "Požadovaný graf zcela chybí."),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", "Požadovaný graf je v sešitu přítomen."),
            0,
        )
