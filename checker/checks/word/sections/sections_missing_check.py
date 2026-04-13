from checks.base_check import BaseCheck, CheckResult


class SectionsMissingCheck(BaseCheck):
    code = "T_C01"

    def run(self, document, assignment=None):
        count = document.section_count()

        if count <= 1:
            return CheckResult(
                False,
                self.msg("missing", "Oddíly zcela chybí (nalezen pouze 1 oddíl)."),
                None,
                count=1,
            )

        return CheckResult(True, self.msg("ok", "Oddíly existují."), 0, count=0)
