from checks.base_check import BaseCheck, CheckResult


class SecondSectionPageNumberStartsAtOneCheck(BaseCheck):
    code = "T_Z08"

    def run(self, document, assignment=None):
        result = document.second_section_page_number_starts_at_one()

        if result is None:
            return CheckResult(
                True,
                self.msg("skip_too_few_sections", "Dokument má méně než dva oddíly."),
                0,
            )

        if not result:
            return CheckResult(
                False,
                self.msg("fail", "Číslování stránek druhého oddílu nezačíná od 1."),
                None,
            )

        return CheckResult(
            True, self.msg("ok", "Číslování stránek druhého oddílu začíná od 1."), 0
        )
