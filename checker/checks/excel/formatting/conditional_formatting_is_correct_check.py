from checks.base_check import BaseCheck, CheckResult


class ConditionalFormattingCorrectnessCheck(BaseCheck):
    code = "S_F08"
    SHEET = "data"

    OP = {
        "greaterThan": ">",
        "lessThan": "<",
        "greaterThanOrEqual": ">=",
        "lessThanOrEqual": "<=",
        "equal": "=",
        "notEqual": "!=",
    }

    def _expected_from_assignment(self, assignment):
        """
        Získá ze zadání očekávaná pravidla podmíněného formátování.

        Args:
            assignment: Zadání obsahující specifikaci buněk.

        Returns:
            Slovník očekávaných pravidel podmíněného formátování podle adres buněk.
        """
        expected = {}

        for addr, spec in assignment.cells.items():
            conds = getattr(spec, "conditionalFormat", None)
            if not conds:
                continue

            expected.setdefault(addr, [])

            for rule in conds:
                raw = rule.get("value", None)
                if raw is None:
                    continue

                if isinstance(raw, str):
                    raw = raw.strip()
                    if raw == "":
                        continue
                    raw = raw.replace(",", ".")

                try:
                    val = float(raw)
                except (ValueError, TypeError):
                    continue

                expected[addr].append(
                    {
                        "operator": rule.get("operator"),
                        "value": val,
                    }
                )

        return expected

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

        expected = self._expected_from_assignment(assignment)

        if not expected:
            return CheckResult(
                False,
                self.msg(
                    "no_expected",
                    "V assignmentu není definováno žádné podmíněné formátování.",
                ),
                None,
            )

        missing = document.check_conditional_formatting(self.SHEET, expected)

        if missing:
            header = self.msg(
                "errors_header", "Podmíněné formátování neodpovídá zadání:"
            )

            lines = []
            for p in missing:
                if p.get("kind") == "sheet_missing":
                    lines.append(
                        self.msg("missing_sheet", 'Chybí list "{sheet}".').format(
                            sheet=p.get("sheet", self.SHEET)
                        )
                    )
                    continue

                if p.get("kind") == "missing_rule":
                    addr = p.get("cell", "")
                    op_key = p.get("operator", "")
                    op = self.OP.get(op_key, op_key)
                    val = p.get("value", "")
                    where = f"{self.SHEET}!{addr}" if addr else self.SHEET

                    lines.append(
                        self.msg(
                            "missing_rule", "{where}: chybí pravidlo {op} {val}"
                        ).format(where=where, op=op, val=val)
                    )
                    continue

                lines.append(
                    self.msg("unknown", "Neznámá chyba v podmíněném formátování.")
                )

            msg = header + "\n" + "\n".join("- " + x for x in lines)

            return CheckResult(False, msg, None, count=len(lines))

        return CheckResult(
            True, self.msg("ok", "Podmíněné formátování odpovídá zadání."), 0
        )
