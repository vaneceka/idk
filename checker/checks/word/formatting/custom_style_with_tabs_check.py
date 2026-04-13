from checks.base_check import BaseCheck, CheckResult


class CustomStyleWithTabsCheck(BaseCheck):
    code = "T_F20"
    TOLERANCE = 10  # twips

    def run(self, document, assignment=None):
        if assignment is None:
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."),
                0,
                count=0,
            )

        errors = []
        has_error = False

        for style_name, spec in assignment.styles.items():
            if not spec.tabs:
                continue

            style = document.get_custom_style(style_name)
            if style is None:
                errors.append(
                    self.msg(
                        "missing_style", 'Styl "{style}" v dokumentu neexistuje.'
                    ).format(style=style_name)
                )
                has_error = True
                continue

            actual_tabs = style.tabs
            if not actual_tabs:
                errors.append(
                    self.msg(
                        "no_tabs", 'Styl "{style}" nemá definované tabulátory.'
                    ).format(style=style_name)
                )
                has_error = True
                continue

            expected_tabs = {align.lower(): int(pos) for align, pos in spec.tabs}
            actual_tabs_map = {align.lower(): int(pos) for align, pos in actual_tabs}

            if set(expected_tabs.keys()) != set(actual_tabs_map.keys()):
                errors.append(
                    self.msg(
                        "wrong_tab_types",
                        'Styl "{style}" má špatné typy tabulátorů:\n'
                        "  očekáváno: {expected}\n"
                        "  nalezeno:  {actual}",
                    ).format(
                        style=style_name, expected=expected_tabs, actual=actual_tabs_map
                    )
                )
                has_error = True
                continue

            for align, expected_pos in expected_tabs.items():
                actual_pos = actual_tabs_map[align]
                if abs(expected_pos - actual_pos) > self.TOLERANCE:
                    errors.append(
                        self.msg(
                            "wrong_tabs",
                            'Styl "{style}" má špatné tabulátory:\n'
                            "  očekáváno: {expected}\n"
                            "  nalezeno:  {actual}",
                        ).format(
                            style=style_name,
                            expected=expected_tabs,
                            actual=actual_tabs_map,
                        )
                    )
                    has_error = True
                    break

        if has_error:
            return CheckResult(
                passed=False,
                message=self.msg("errors_header", "Chyby v nastavení tabulátorů:")
                + "\n"
                + "\n".join(errors),
                points=None,
            )

        return CheckResult(
            True,
            self.msg(
                "ok", "Všechny styly s tabulátory jsou nastaveny správně dle zadání."
            ),
            0,
        )
