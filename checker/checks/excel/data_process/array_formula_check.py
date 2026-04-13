from checks.base_check import BaseCheck, CheckResult


class ArrayFormulaCheck(BaseCheck):
    code = "S_D06"

    def run(self, document, assignment=None):
        array_cells = document.get_array_formula_cells()

        if array_cells:
            lines = "\n".join(f"- {c}" for c in array_cells)

            header = self.msg(
                "fail", default="Není použit klasický vzorec, ale maticový:"
            )

            return CheckResult(
                False,
                header + "\n" + lines,
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", default="Vzorce nejsou maticové."),
            0,
        )
