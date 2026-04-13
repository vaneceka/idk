from checks.base_check import BaseCheck, CheckResult


class ThirdSectionPageNumberingContinuesCheck(BaseCheck):
    code = "T_O08"

    def run(self, document, assignment=None):
        if document.section_count() < 3:
            return CheckResult(
                True,
                self.msg(
                    "skip_no_third_section",
                    "Dokument nemá třetí oddíl - nelze ověřit kontinuitu stránkování.",
                ),
                0,
            )

        has_number = document.section_footer_has_page_number(2)
        if has_number is not True:
            return CheckResult(
                False,
                self.msg(
                    "missing_page_number",
                    "Ve třetím oddílu není zobrazené číslo stránky.",
                ),
                None,
            )

        restarts = document.section_page_number_starts_at_one(2)

        if restarts is None:
            return CheckResult(
                False,
                self.msg(
                    "cannot_verify_restart",
                    "Nelze ověřit, zda se ve třetím oddílu restartuje číslování stránek.",
                ),
                None,
            )

        if restarts is True:
            return CheckResult(
                False,
                self.msg(
                    "restarts",
                    "Ve třetím oddílu se číslování stránek restartuje - má pokračovat z druhého oddílu.",
                ),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", "Číslování stránek ve třetím oddílu správně pokračuje."),
            0,
        )
