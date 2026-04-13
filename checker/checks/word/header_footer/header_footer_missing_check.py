from checks.base_check import BaseCheck, CheckResult


class HeaderFooterMissingCheck(BaseCheck):
    code = "T_Z01"

    def run(self, document, assignment=None):
        for i in range(document.section_count()):
            if document.section_has_header_or_footer_content(i):
                return CheckResult(
                    True,
                    self.msg("ok", "Záhlaví nebo zápatí je v dokumentu řešeno."),
                    0,
                )

        return CheckResult(
            False,
            self.msg("fail", "Dokument neobsahuje žádné záhlaví ani zápatí."),
            None,
        )
