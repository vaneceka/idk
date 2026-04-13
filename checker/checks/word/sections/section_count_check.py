from checks.base_check import BaseCheck, CheckResult


class SectionCountCheck(BaseCheck):
    code = "T_C02"

    def run(self, document, assignment=None):
        count = document.section_count()

        if count <= 1:
            return CheckResult(
                True,
                self.msg("skip_missing_sections", "Oddíly chybí - řeší jiná kontrola."),
                0,
            )

        expected = int(self.msg("expected", "3") or "3")

        if count != expected:
            return CheckResult(
                False,
                self.msg(
                    "fail_wrong_count",
                    "Nalezeno {count} oddílů, požadovány {expected}.",
                ).format(count=count, expected=expected),
                None,
                1,
            )

        return CheckResult(
            True, self.msg("ok", "Počet oddílů OK ({count})").format(count=count), 0
        )
