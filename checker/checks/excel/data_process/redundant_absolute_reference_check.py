import re

from checks.base_check import BaseCheck, CheckResult


class RedundantAbsoluteReferenceCheck(BaseCheck):
    code = "S_D08"

    CELL_REF_RE = re.compile(r"(\$?)([A-Z]+)(\$?)(\d+)")

    def _extract_ref_map(
        self, formula: str
    ) -> dict[tuple[str, str], tuple[bool, bool]]:
        """
        Vytáhne ze vzorce odkazy na buňky a jejich absolutnost.

        Args:
            formula: Vzorec ke zpracování.

        Returns:
            Slovník, kde klíčem je sloupec a řádek buňky a hodnotou informace
            o absolutním sloupci a řádku.
        """
        refs: dict[tuple[str, str], tuple[bool, bool]] = {}

        if not formula:
            return refs

        for m in self.CELL_REF_RE.finditer(formula.upper()):
            col_abs = bool(m.group(1))
            col = m.group(2)
            row_abs = bool(m.group(3))
            row = m.group(4)

            refs[(col, row)] = (col_abs, row_abs)

        return refs

    def run(self, document, assignment=None):
        if assignment is None or not hasattr(assignment, "cells"):
            return CheckResult(
                True,
                self.msg(
                    "skip_no_assignment", "Chybí assignment - check přeskočen."
                ),
                0,
            )

        problems = []

        for addr, spec in assignment.cells.items():
            expected = getattr(spec, "expression", None)
            if not expected:
                continue

            cell = document.get_cell(f"data!{addr}")
            if not cell or not isinstance(cell.get("formula"), str):
                continue

            student_formula = cell["formula"]

            exp_refs = self._extract_ref_map(expected)
            stu_refs = self._extract_ref_map(student_formula)

            for (col, row), (exp_col_abs, exp_row_abs) in exp_refs.items():
                if (col, row) not in stu_refs:
                    continue

                stu_col_abs, stu_row_abs = stu_refs[(col, row)]

                if exp_col_abs != stu_col_abs or exp_row_abs != stu_row_abs:
                    problems.append(
                        self.msg(
                            "bad_abs_ref",
                            "{sheet}!{addr}: špatné použití $ u odkazu {ref}",
                        ).format(sheet="data", addr=addr, ref=f"{col}{row}")
                    )

        if problems:
            msg = (
                self.msg("errors_header", "Nesprávně použité absolutní adresy:")
                + "\n"
                + "\n".join("- " + p for p in problems)
            )
            return CheckResult(False, msg, None)

        return CheckResult(
            True, self.msg("ok", "Absolutní adresy jsou použity správně."), 0
        )
