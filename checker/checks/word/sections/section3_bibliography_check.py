from checks.base_check import BaseCheck, CheckResult


class Section3BibliographyCheck(BaseCheck):
    code = "T_C10"

    def run(self, document, assignment=None):
        if not document.has_bibliography_in_section(2):
            return CheckResult(
                False,
                self.msg(
                    "missing_bibliography", "Ve třetím oddílu chybí seznam literatury."
                ),
                None,
            )

        return CheckResult(True, self.msg("ok", "Seznam literatury nalezen."), 0)
