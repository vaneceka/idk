from checks.base_check import BaseCheck, CheckResult


class ChartFormattingCheck(BaseCheck):
    code = "S_G03"
    SHEET = "data"

    def run(self, document, assignment=None):
        if not assignment or not assignment.chart:
            return CheckResult(
                True, self.msg("skip_no_chart", "Zadání neobsahuje graf."), 0
            )

        if not document.has_chart(self.SHEET):
            return CheckResult(
                False, self.msg("missing_chart", "Graf v sešitu chybí."), None
            )

        expected = assignment.chart
        errors = []

        if expected.get("title"):
            actual_title = document.chart_title(self.SHEET)
            if not actual_title or not str(actual_title).strip():
                errors.append(self.msg("missing_title", "chybí název grafu"))

        if expected.get("xAxisLabel"):
            actual_x = document.chart_x_label(self.SHEET)
            if actual_x != expected["xAxisLabel"]:
                if actual_x:
                    errors.append(
                        self.msg(
                            "wrong_x_axis",
                            'název osy X neodpovídá zadání (oček. "{expected}", nalezen "{found}")',
                        ).format(expected=expected["xAxisLabel"], found=actual_x)
                    )
                else:
                    errors.append(self.msg("missing_x_axis", "chybí název osy X"))

        if expected.get("yAxisLabel"):
            actual_y = document.chart_y_label(self.SHEET)
            if actual_y != expected["yAxisLabel"]:
                if actual_y:
                    errors.append(
                        self.msg(
                            "wrong_y_axis",
                            'název osy Y neodpovídá zadání (oček. "{expected}", nalezen "{found}")',
                        ).format(expected=expected["yAxisLabel"], found=actual_y)
                    )
                else:
                    errors.append(self.msg("missing_y_axis", "chybí název osy Y"))

        if not document.chart_has_data_labels(self.SHEET):
            errors.append(self.msg("missing_data_labels", "chybí popisky dat"))

        if errors:
            header = self.msg("missing_header", "Problémy ve formátování grafu:")
            return CheckResult(
                False,
                header + "\n- " + "\n- ".join(errors),
                None,
                len(errors),
            )

        return CheckResult(True, self.msg("ok", "Graf má správné formátování."), 0)
