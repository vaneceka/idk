import re

from checks.base_check import BaseCheck, CheckResult


class DescriptiveStatisticsCheck(BaseCheck):
    code = "S_D11"
    SHEET = "data"

    def row_from_addr(self, addr: str) -> int:
        """
        Vrátí číslo řádku z adresy buňky.

        Args:
            addr: Adresa buňky, například A1.

        Returns:
            Číslo řádku.

        Raises:
            ValueError: Pokud adresa buňky nemá platný formát.
        """
        m = re.match(r"[A-Z]+(\d+)", addr)
        if not m:
            raise ValueError(f"Neplatná adresa buňky: {addr}")
        return int(m.group(1))

    def run(self, document, assignment=None):

        if assignment is None or not hasattr(assignment, "cells"):
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."),
                0,
            )

        if self.SHEET not in document.sheet_names():
            return CheckResult(
                False,
                self.msg("missing_sheet", 'Chybí list "{sheet}".').format(
                    sheet=self.SHEET
                ),
                None,
            )

        rows = sorted({self.row_from_addr(a) for a in assignment.cells})
        start_of_stats = None

        for a, b in zip(rows, rows[1:]):
            if b > a + 1:
                start_of_stats = b
                break

        if start_of_stats is None:
            return CheckResult(
                False,
                self.msg(
                    "cannot_detect_start",
                    "Nelze určit začátek popisné charakteristiky.",
                ),
                None,
            )

        problems = []

        for addr, spec in assignment.cells.items():
            if not getattr(spec, "expression", None):
                continue

            if self.row_from_addr(addr) <= start_of_stats:
                continue

            info = document.get_cell_info(self.SHEET, addr)

            if info is None or not info["formula"]:
                problems.append(
                    self.msg(
                        "missing_formula_item", "{sheet}!{addr}: chybí vzorec"
                    ).format(sheet=self.SHEET, addr=addr)
                )

        if problems:
            header = self.msg("missing_stats_header", "Chybí popisná charakteristika:")
            return CheckResult(
                False, header + "\n" + "\n".join("- " + p for p in problems), None
            )

        return CheckResult(
            True,
            self.msg("ok", "Popisná charakteristika je přítomna."),
            0,
        )
