from checks.base_check import BaseCheck, CheckResult


class MissingIntroPageCheck(BaseCheck):
    code = "T_C05"

    REQUIRED_STYLES = {"desky-fakulta", "uvodni-tema", "uvodni-autor"}

    def run(self, document, assignment=None):
        ok, missing = document.section_missing_styles(0, self.REQUIRED_STYLES)

        if ok:
            return CheckResult(True, self.msg("ok", "Úvodní list je přítomen."), 0)

        missing_list = ", ".join(missing) if missing else "—"

        msg = (
            self.msg(
                "fail",
                "V prvním oddílu chybí úvodní list (nejsou použity všechny povinné styly úvodu).",
            )
            + "\n"
            + self.msg("missing_line", "Chybí styly: {missing}.").format(
                missing=missing_list
            )
        )

        return CheckResult(False, msg, None, len(missing) if missing else 1)
