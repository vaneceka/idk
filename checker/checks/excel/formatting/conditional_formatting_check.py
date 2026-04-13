from checks.base_check import BaseCheck, CheckResult


class ConditionalFormattingExistsCheck(BaseCheck):
    code = "S_F07"
    SHEET = "data"

    def run(self, document, assignment=None):
        if self.SHEET not in document.sheet_names():
            return CheckResult(
                False,
                self.msg("missing_sheet", 'Chybí list "{sheet}".').format(
                    sheet=self.SHEET
                ),
                None,
            )

        if not document.has_conditional_formatting(self.SHEET):
            return CheckResult(
                False,
                self.msg(
                    "missing_cf", "V sešitu není nastaveno žádné podmíněné formátování."
                ),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", "Podmíněné formátování je v sešitu přítomno."),
            0,
        )
