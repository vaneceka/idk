from checks.base_check import BaseCheck, CheckResult


class RequiredDataWorksheetCheck(BaseCheck):
    code = "S_D03"

    def run(self, document, assignment=None):
        sheet_names = document.sheet_names()

        if not any(name.lower() == "data" for name in sheet_names):
            return CheckResult(
                False,
                self.msg("fail", 'Požadovaný list "data" zcela chybí.'),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", 'Požadovaný list "data" je v sešitu přítomen.'),
            0,
        )
