import re

from checks.base_check import BaseCheck, CheckResult


class NamedRangeUsageCheck(BaseCheck):
    code = "S_D07"

    TOKEN_RE = re.compile(r"\b[A-Z_][A-Z0-9_]*\b")
    CELL_RE = re.compile(r"\$?[A-Z]{1,3}\$?\d+")

    def run(self, document, assignment=None):
        defined_names = document.get_defined_names()
        bad_cells = []

        for cell in document.cells_with_formulas():
            formula = document.normalize_formula(cell["formula"])
            if not formula:
                continue

            tokens = self.TOKEN_RE.findall(formula)

            for token in tokens:
                if self.CELL_RE.fullmatch(token):
                    continue

                if token in defined_names:
                    bad_cells.append(
                        self.msg("bad_cell", "{sheet}!{addr}: {name}").format(
                            sheet=cell["sheet"], addr=cell["address"], name=token
                        )
                    )
                    break

                if bad_cells:
                    header = self.msg(
                        "header", "Použity pojmenované oblasti místo adres buněk:"
                    )
                    lines = "\n".join(f"- {c}" for c in bad_cells)

                    return CheckResult(
                        False,
                        header + "\n" + lines,
                        None,
                    )

        return CheckResult(
            True,
            self.msg("ok", "Vzorce používají pouze adresy buněk."),
            0,
        )
