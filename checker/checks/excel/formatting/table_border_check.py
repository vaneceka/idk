from checks.base_check import BaseCheck, CheckResult
from models.spreadsheet_models import BorderProblem


class TableBorderCheck(BaseCheck):
    code = "S_F03"
    SHEET = "data"

    SIDE_CZ = {"top": "horní", "bottom": "dolní", "left": "levé", "right": "pravé"}

    def _fmt_border_problem(self, p: BorderProblem, sheet: str, location: str) -> str:
        """
        Vytvoří textový popis problému s ohraničením buněk.

        Args:
            p: Informace o nalezeném problému.
            sheet: Název listu.
            location: Výchozí umístění kontrolované oblasti.

        Returns:
            Text chyby popisující problém s ohraničením.
        """
        kind = p.kind

        if kind == "sheet_missing":
            return self.msg("missing_sheet", 'Chybí list "{sheet}".').format(
                sheet=p.sheet or sheet
            )

        if p.cell:
            where = p.cell if "!" in p.cell else f"{sheet}!{p.cell}"
        else:
            where = f"{sheet}!{p.range or location}"

        if kind == "outer":
            side_key = p.side or ""
            side = self.SIDE_CZ.get(side_key, side_key)
            return self.msg(
                "outer_missing", "{where}: chybí {side} vnější ({expected})"
            ).format(
                where=where,
                side=side,
                expected=p.expected or "",
            )

        if kind == "inner_h":
            return self.msg(
                "inner_h_missing", "{where}: chybí vnitřní vodorovné ({expected})"
            ).format(
                where=where,
                expected=p.expected or "",
            )

        if kind == "inner_v":
            return self.msg(
                "inner_v_missing", "{where}: chybí vnitřní svislé ({expected})"
            ).format(
                where=where,
                expected=p.expected or "",
            )

        return self.msg("unknown_problem", "{where}: chyba ohraničení").format(
            where=where
        )

    def run(self, document, assignment=None):
        if assignment is None or not hasattr(assignment, "borders"):
            return CheckResult(
                True,
                self.msg("skip_no_tables", "Chybí definice tabulek - check přeskočen."),
                0,
            )

        problems = []

        for table in assignment.borders:
            raw = document.check_table_borders(
                sheet=self.SHEET,
                location=table["location"],
                outer=table["outlineBorderStyle"],
                inner=table["insideBorderStyle"],
            )

            if raw and raw[0].kind == "sheet_missing":
                msg = self._fmt_border_problem(raw[0], self.SHEET, table["location"])
                return CheckResult(False, msg, None)

            for p in raw:
                problems.append(
                    self._fmt_border_problem(p, self.SHEET, table["location"])
                )

        if problems:
            max_lines = int(self.msg("max_lines", "15") or "15")
            header = self.msg("errors_header", "Chybí ohraničení tabulky:")
            msg = header + "\n" + "\n".join("- " + p for p in problems[:max_lines])
            return CheckResult(False, msg, None)

        return CheckResult(True, self.msg("ok", "Tabulky mají správné ohraničení."), 0)
