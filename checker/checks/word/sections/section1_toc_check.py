from checks.base_check import BaseCheck, CheckResult


class Section1TOCCheck(BaseCheck):
    code = "T_C06"

    def run(self, document, assignment=None):
        if not document.has_toc_in_section(0):
            return CheckResult(
                False,
                self.msg("missing_toc", "V prvním oddílu chybí obsah dokumentu."),
                None,
            )

        return CheckResult(True, self.msg("ok", "Obsah v 1. oddílu OK"), 0)
