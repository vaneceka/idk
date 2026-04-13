from checks.base_check import BaseCheck, CheckResult


class ChartTypeCheck(BaseCheck):
    code = "S_G04"
    SHEET = "data"

    def _normalize_chart_type(self, t: str | None) -> str | None:
        """
        Převede typ grafu do sjednoceného označení.

        Args:
            t: Typ grafu.

        Returns:
            Normalizovaný typ grafu, nebo None pokud není zadán.
        """
        if not t:
            return None

        t = t.lower()

        mapping = {
            # Excel
            "barchart": "bar",
            "linechart": "line",
            "piechart": "pie",
            # Calc
            "bar": "bar",
            "line": "line",
            "pie": "pie",
        }

        return mapping.get(t, t)

    def run(self, document, assignment=None):
        if assignment is None or not assignment.chart:
            return CheckResult(
                True, self.msg("skip_no_chart", "Zadání graf nevyžaduje."), 0
            )

        expected_raw = assignment.chart.get("type")
        expected = self._normalize_chart_type(expected_raw)

        actual_raw = document.chart_type(self.SHEET)
        actual = self._normalize_chart_type(actual_raw)

        if actual is None:
            return CheckResult(
                False, self.msg("missing_chart", "Graf neexistuje."), None
            )

        if expected != actual:
            header = self.msg("wrong_type_header", "Nevhodný typ grafu:")
            exp_line = self.msg("expected_line", "- očekáváno: {expected}").format(
                expected=expected_raw
            )
            found_line = self.msg("found_line", "- nalezeno: {found}").format(
                found=actual_raw
            )

            return CheckResult(
                False, header + "\n" + exp_line + "\n" + found_line, None
            )

        return CheckResult(True, self.msg("ok", "Typ grafu odpovídá zadání."), 0)
