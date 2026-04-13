import re

from checks.base_check import BaseCheck, CheckResult


class MergedCellsCheck(BaseCheck):
    code = "S_F04"
    SHEET = "data"

    def _split_addr(self, addr: str) -> tuple[int, int]:
        """
        Rozdělí adresu buňky na číslo sloupce a řádku.

        Args:
            addr: Adresa buňky, například A1.

        Returns:
            Číslo sloupce a číslo řádku.

        Raises:
            ValueError: Pokud adresa buňky nemá platný formát.
        """
        m = re.fullmatch(r"([A-Z]+)(\d+)", addr.upper())
        if not m:
            raise ValueError(f"Neplatná adresa buňky: {addr}")

        col_letters, row = m.groups()
        row = int(row)

        col = 0
        for c in col_letters:
            col = col * 26 + (ord(c) - ord("A") + 1)

        return col, row

    def _data_table_bounds(self, assignment):
        """
        Určí hranice datové tabulky podle adres buněk v zadání.

        Args:
            assignment: Zadání obsahující buňky tabulky.

        Returns:
            Minimální sloupec, minimální řádek, maximální sloupec a maximální řádek.
        """
        rows = []
        cols = []

        for addr in assignment.cells:
            col, row = self._split_addr(addr)
            rows.append(row)
            cols.append(col)

        return min(cols), min(rows), max(cols), max(rows)

    def _overlaps(self, a, b):
        """
        Ověří, zda se dva obdélníkové rozsahy překrývají.

        Args:
            a: První rozsah ve tvaru (col1, row1, col2, row2).
            b: Druhý rozsah ve tvaru (col1, row1, col2, row2).

        Returns:
            True pokud se rozsahy překrývají, jinak False.
        """
        c1, r1, c2, r2 = a
        C1, R1, C2, R2 = b
        return not (c2 < C1 or c1 > C2 or r2 < R1 or r1 > R2)

    def run(self, document, assignment=None):
        if self.SHEET not in document.sheet_names():
            return CheckResult(
                False,
                self.msg("missing_sheet", 'Chybí list "{sheet}".').format(
                    sheet=self.SHEET
                ),
                None,
            )

        if assignment is None:
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočeno."),
                0,
            )

        forbidden = self._data_table_bounds(assignment)
        problems = []

        for merged in document.merged_ranges(self.SHEET):
            if self._overlaps(merged, forbidden):
                problems.append(
                    self.msg(
                        "overlaps_data", "Sloučené buňky zasahují do datové oblasti"
                    )
                )

        if problems:
            return CheckResult(
                False,
                self.msg("errors_header", "Chybné sloučení buněk:")
                + "\n"
                + "\n".join("- " + p for p in problems),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", "Sloučení buněk je použito správně."),
            0,
        )
