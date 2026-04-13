from checks.base_check import BaseCheck, CheckResult


class Section3FigureListCheck(BaseCheck):
    code = "T_C08"

    def run(self, document, assignment=None):
        if document.has_list_of_figures_in_section(2):
            return CheckResult(True, self.msg("ok", "Seznam obrázků nalezen."), 0)

        return CheckResult(
            False,
            self.msg(
                "missing_list_of_figures", "Ve třetím oddílu chybí seznam obrázků."
            ),
            None,
        )
