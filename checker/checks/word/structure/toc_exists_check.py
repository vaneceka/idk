from checks.base_check import BaseCheck, CheckResult


class TOCExistsCheck(BaseCheck):
    code = "T_O01"

    def run(self, document, assignment=None):
        for i in range(document.section_count()):
            if document.has_toc_in_section(i):
                return CheckResult(True, self.msg("ok", "Obsah dokumentu existuje."), 0)

        return CheckResult(
            False, self.msg("fail", "V dokumentu zcela chybí obsah."), None
        )
