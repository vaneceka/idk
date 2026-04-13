from checks.base_check import BaseCheck, CheckResult


class HeaderFormattingCheck(BaseCheck):
    code = "S_F05"
    SHEET = "data"

    def run(self, document, assignment=None):
        if assignment is None or not hasattr(assignment, "cells"):
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - přeskočeno."),
                0,
            )

        problems = []

        for addr, spec in assignment.cells.items():
            style_req = getattr(spec, "style", None)
            if not style_req:
                continue

            if not style_req.get("bold"):
                continue

            style = document.get_cell_style(self.SHEET, addr)
            if style is None:
                problems.append(
                    self.msg("cell_missing", "{sheet}!{addr}: buňka neexistuje").format(
                        addr=addr, sheet=self.SHEET
                    )
                )
                continue

            if not style.get("bold"):
                problems.append(
                    self.msg("not_bold", "{sheet}!{addr}: záhlaví není tučné").format(
                        addr=addr, sheet=self.SHEET
                    )
                )

            if style_req.get("alignment"):
                if style.get("align_h") != "center":
                    problems.append(
                        self.msg(
                            "not_center",
                            "{sheet}!{addr}: záhlaví není zarovnáno na střed",
                        ).format(addr=addr, sheet=self.SHEET)
                    )

        if problems:
            msg = (
                self.msg("errors_header", "Záhlaví tabulky není správně formátováno:")
                + "\n"
                + "\n".join("- " + p for p in problems)
            )
            return CheckResult(False, msg, None)

        return CheckResult(
            True,
            self.msg("ok", "Záhlaví tabulek jsou správně formátována."),
            0,
        )
