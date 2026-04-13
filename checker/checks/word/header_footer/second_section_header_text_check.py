from checks.base_check import BaseCheck, CheckResult


class SecondSectionHeaderHasTextCheck(BaseCheck):
    code = "T_Z06"

    def run(self, document, assignment=None):
        if document.section_count() < 2:
            return CheckResult(
                True,
                self.msg("skip_too_few_sections", "Dokument má méně než dva oddíly."),
                0,
            )

        if document.section_has_header_text(1):
            return CheckResult(
                True,
                self.msg("ok", "Záhlaví druhého oddílu obsahuje text."),
                0,
            )

        return CheckResult(
            False,
            self.msg("fail", "Záhlaví druhého oddílu je prázdné nebo neexistuje."),
            None,
        )
