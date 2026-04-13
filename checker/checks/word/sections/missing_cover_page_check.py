from checks.base_check import BaseCheck, CheckResult


class MissingCoverPageCheck(BaseCheck):
    code = "T_C04"

    REQUIRED_STYLES = {
        "desky-fakulta",
        "desky-nazev-prace",
        "desky-rok-a-jmeno",
    }

    def run(self, document, assignment=None):
        ok, missing = document.section_missing_styles(0, self.REQUIRED_STYLES)

        if ok:
            return CheckResult(True, self.msg("ok", "Desky práce jsou přítomny."), 0)

        missing_list = ", ".join(missing) if missing else "—"

        header = self.msg("fail", "V prvním oddílu chybí desky práce.")
        details = self.msg("missing_styles", "Chybí styly: {missing}.").format(
            missing=missing_list
        )

        return CheckResult(
            False, header + "\n" + details, None, len(missing) if missing else 1
        )
