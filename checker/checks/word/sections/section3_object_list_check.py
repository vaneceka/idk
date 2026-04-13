from checks.base_check import BaseCheck, CheckResult


class Section3ObjectsListsCheck(BaseCheck):
    code = "T_C09"
    SECTION_INDEX = 2

    def run(self, document, assignment=None):
        has_tables = document.has_any_table()
        has_charts = document.has_any_chart()
        has_equations = document.has_any_equation()
        if not (has_tables or has_charts or has_equations):
            return CheckResult(
                True,
                self.msg(
                    "no_objects_ok",
                    "Dokument neobsahuje tabulky/grafy/rovnice – seznamy nejsou vyžadovány.",
                ),
                0,
            )

        missing = []

        if has_tables and not document.has_list_of_tables_in_section(
            self.SECTION_INDEX
        ):
            missing.append(self.msg("missing_tables", "chybí seznam tabulek"))

        if has_charts and not document.has_list_of_charts_in_section(
            self.SECTION_INDEX
        ):
            missing.append(self.msg("missing_charts", "chybí seznam grafů"))

        if has_equations and not document.has_list_of_equations_in_section(
            self.SECTION_INDEX
        ):
            missing.append(self.msg("missing_equations", "chybí seznam rovnic"))

        if missing:
            header = self.msg(
                "fail",
                "Ve třetím oddílu není seznam některých objektů, přestože se v dokumentu nacházejí:",
            )
            msg = header + "\n" + "\n".join("– " + m for m in missing)
            return CheckResult(False, msg, None, count=len(missing))

        return CheckResult(
            True, self.msg("ok", "Seznamy objektů ve 3. oddílu jsou přítomné."), 0
        )
