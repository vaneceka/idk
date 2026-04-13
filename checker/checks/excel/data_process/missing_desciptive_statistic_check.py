import re

from checks.base_check import BaseCheck, CheckResult


class MissingDescriptiveStatisticsCheck(BaseCheck):
    code = "S_D09"

    REQUIRED_FUNCTIONS = {"MIN", "MAX", "AVERAGE", "MEDIAN"}
    FUNC_RE = re.compile(r"=([A-Z]+)\(", re.IGNORECASE)

    def run(self, document, assignment=None):
        if "data" not in document.sheet_names():
            return CheckResult(
                False,
                self.msg(
                    "missing_sheet",
                    'List "{sheet}" chybí - nelze vytvořit popisnou charakteristiku.',
                ).format(sheet="data"),
                None,
            )

        found = set()

        for item in document.iter_formulas():
            if item.get("sheet") != "data":
                continue

            formula = item.get("formula")
            if not isinstance(formula, str):
                continue

            for func in self.FUNC_RE.findall(formula):
                func = func.upper()
                if func in self.REQUIRED_FUNCTIONS:
                    found.add(func)

        missing = self.REQUIRED_FUNCTIONS - found

        if missing:
            header = self.msg(
                "missing_stats_header",
                "Chybí popisná charakteristika - nebyly nalezeny funkce:",
            )
            return CheckResult(
                False,
                header + " " + ", ".join(sorted(missing)),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", "Popisná charakteristika je přítomna."),
            0,
        )
