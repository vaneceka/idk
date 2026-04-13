from checks.base_check import BaseCheck, CheckResult


class FrontpageStylesCheck(BaseCheck):
    code = "T_F25"

    def run(self, document, assignment=None):
        if assignment is None:
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."),
                0,
                count=0,
            )

        errors = []
        bad_count = 0

        required_styles = {
            "uvodni-tema": assignment.styles.get("uvodni-tema"),
            "uvodni-autor": assignment.styles.get("uvodni-autor"),
        }

        for style_name, expected in required_styles.items():
            if expected is None:
                continue

            actual = document.get_custom_style(style_name)

            if actual is None:
                bad_count += 1
                errors.append(
                    self.msg(
                        "missing_style", 'Styl "{style}" v dokumentu neexistuje.'
                    ).format(style=style_name)
                )
                continue

            diffs = actual.diff(expected)
            if diffs:
                bad_count += 1
                header = self.msg(
                    "style_mismatch_header", 'Styl "{style}" neodpovídá zadání:'
                ).format(style=style_name)
                errors.append(header + "\n" + "\n".join(f"  - {d}" for d in diffs))

        if errors:
            return CheckResult(
                False,
                self.msg("errors_header", "Chyby ve stylech úvodního listu:")
                + "\n"
                + "\n".join(errors),
                None,
                bad_count,
            )

        return CheckResult(
            True,
            self.msg("ok", "Styly úvodního listu odpovídají zadání."),
            0,
        )
