from checks.base_check import BaseCheck, CheckResult


class NumberFormattingCheck(BaseCheck):
    code = "S_F01"
    SHEET = "data"

    def _normalize_format(self, fmt: str | None) -> str:
        """
        Normalizuje formát čísla do jednotné podoby.

        Args:
            fmt: Formát čísla.

        Returns:
            Upravený formát, nebo prázdný řetězec.
        """
        if not fmt:
            return ""

        f = fmt.strip().replace(" ", "")

        if f.startswith("%"):
            f = f[1:] + "%"

        return f

    def _is_percent_format(self, fmt: str | None) -> bool:
        """
        Ověří, zda formát představuje procenta.

        Args:
            fmt: Formát čísla.

        Returns:
            True pokud jde o procentní formát, jinak False.
        """
        return "%" in self._normalize_format(fmt)

    def _decimal_places(self, fmt: str | None) -> int:
        """
        Vrátí počet desetinných míst podle formátu čísla.

        Args:
            fmt: Formát čísla.

        Returns:
            Počet desetinných míst.
        """
        f = self._normalize_format(fmt)
        if "." not in f:
            return 0

        right = f.split(".", 1)[1]
        right = right.replace("%", "")

        count = 0
        for ch in right:
            if ch in ("0", "#"):
                count += 1
            else:
                break

        return count

    def run(self, document, assignment=None):
        if assignment is None or not hasattr(assignment, "cells"):
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."),
                0,
            )

        if not document.has_sheet(self.SHEET):
            return CheckResult(
                True,
                self.msg(
                    "skip_missing_sheet",
                    'List "{sheet}" neexistuje - kontrola se přeskakuje.',
                ).format(sheet=self.SHEET),
                0,
            )

        problems = []

        for addr, spec in assignment.cells.items():
            style_req = getattr(spec, "style", None) or {}
            expected_fmt = style_req.get("numberFormat")
            if not expected_fmt:
                continue

            style = document.get_cell_style(self.SHEET, addr) or {}

            expected_percent = self._is_percent_format(expected_fmt)
            expected_dp = self._decimal_places(expected_fmt)

            found_dp = style.get("decimal_places")
            found_fmt = style.get("number_format")

            if found_dp is not None:
                if found_dp != expected_dp:
                    problems.append(
                        self.msg(
                            "wrong_decimal_places",
                            "{sheet}!{addr}: špatný počet desetinných míst (oček. {expected}, nalezen {found})",
                        ).format(
                            addr=addr,
                            expected=expected_dp,
                            found=found_dp,
                            sheet=self.SHEET,
                        )
                    )
                    continue

                if found_fmt is not None:
                    found_percent = self._is_percent_format(found_fmt)
                    if found_percent != expected_percent:
                        problems.append(
                            self.msg(
                                "wrong_number_format",
                                "{sheet}!{addr}: špatný formát čísla (oček. {expected}, nalezen {found})",
                            ).format(
                                addr=addr,
                                expected=expected_fmt,
                                found=found_fmt,
                                sheet=self.SHEET,
                            )
                        )
                continue

            if found_fmt is not None:
                found_percent = self._is_percent_format(found_fmt)
                found_dp_from_fmt = self._decimal_places(found_fmt)

                if (
                    found_percent != expected_percent
                    or found_dp_from_fmt != expected_dp
                ):
                    problems.append(
                        self.msg(
                            "wrong_number_format",
                            "{sheet}!{addr}: špatný formát čísla (oček. {expected}, nalezen {found})",
                        ).format(
                            addr=addr,
                            expected=expected_fmt,
                            found=found_fmt,
                            sheet=self.SHEET,
                        )
                    )

        if problems:
            msg = (
                self.msg("errors_header", "Chybné formátování:")
                + "\n"
                + "\n".join("- " + p for p in problems[:50])
            )
            return CheckResult(False, msg, None)

        return CheckResult(True, self.msg("ok", "Formátování odpovídá zadání."), 0)
