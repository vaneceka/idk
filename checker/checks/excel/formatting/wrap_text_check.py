import re

from checks.base_check import BaseCheck, CheckResult


class WrapTextCheck(BaseCheck):
    code = "S_F06"
    SHEET = "data"
    HEADER_ROW = 1
    MIN_TEXT_LENGTH = 12

    def _row_of_addr(self, addr: str) -> int | None:
        """
        Vrátí číslo řádku z adresy buňky.

        Args:
            addr: Adresa buňky, například A1.

        Returns:
            Číslo řádku, nebo None pokud adresa není platná.
        """
        m = re.match(r"[A-Z]+(\d+)$", addr)
        return int(m.group(1)) if m else None

    def run(self, document, assignment=None):
        problems = []

        for addr in document.iter_cells(self.SHEET):
            row = self._row_of_addr(addr)
            if row != self.HEADER_ROW:
                continue

            value = document.get_cell_value(self.SHEET, addr)

            if not isinstance(value, str):
                continue
            if document.has_formula(self.SHEET, addr):
                continue

            text = value.strip()
            if len(text) < self.MIN_TEXT_LENGTH:
                continue

            style = document.get_cell_style(self.SHEET, addr)
            if not style or style.get("wrap") is not True:
                problems.append(
                    self.msg(
                        "missing_wrap_item", "{sheet}!{addr}: chybí zalamování textu"
                    ).format(addr=addr, sheet=self.SHEET)
                )

        if problems:
            max_lines = int(self.msg("max_lines", "10") or "10")
            header = self.msg("errors_header", "Chybí zalamování textu v buňkách:")

            return CheckResult(
                False,
                header + "\n" + "\n".join("- " + p for p in problems[:max_lines]),
                None,
            )

        return CheckResult(
            True, self.msg("ok", "Zalamování textu je nastaveno správně."), 0
        )
