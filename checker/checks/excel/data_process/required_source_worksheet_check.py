from checks.base_check import BaseCheck, CheckResult


class RequiredSourceWorksheetCheck(BaseCheck):
    code = "S_D01"

    def run(self, document, assignment=None):
        sheet_names = document.sheet_names()

        if not any(name.lower() == "zdroj" for name in sheet_names):
            return CheckResult(
                False,
                self.msg("fail", 'Požadovaný list "zdroj" zcela chybí.'),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", 'Požadovaný list "zdroj" je v sešitu přítomen.'),
            0,
        )
