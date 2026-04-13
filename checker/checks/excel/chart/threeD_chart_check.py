from checks.base_check import BaseCheck, CheckResult


class ThreeDChartCheck(BaseCheck):
    code = "S_G02"
    SHEET = "data"

    def run(self, document, assignment=None):
        if not document.has_chart(self.SHEET):
            return CheckResult(True, self.msg("no_chart", "Graf nebyl nalezen."), 0)

        if document.has_3d_chart(self.SHEET):
            return CheckResult(
                False,
                self.msg("fail_3d", "Použit 3D graf."),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok_2d", "Použit 2D graf."),
            0,
        )
