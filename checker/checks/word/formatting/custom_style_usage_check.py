from checks.base_check import BaseCheck, CheckResult


class RequiredCustomStylesUsageCheck(BaseCheck):
    code = "T_F18"

    def run(self, document, assignment=None):
        if assignment is None:
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."),
                0,
                count=0,
            )

        errors = []
        problems = 0

        custom_styles, _ = document.split_assignment_styles(assignment)

        base_styles = set()
        for spec in custom_styles.values():
            if spec.basedOn:
                base_styles.add(spec.basedOn)

        used_styles = document.get_used_paragraph_styles()

        for style_name, spec in custom_styles.items():
            if not document.style_exists(style_name):
                errors.append(
                    self.msg(
                        "missing_style", 'Styl "{style}" v dokumentu neexistuje.'
                    ).format(style=style_name)
                )
                problems += 1
                continue

            if style_name in base_styles:
                continue

            if style_name not in used_styles:
                errors.append(
                    self.msg(
                        "unused_style", 'Styl "{style}" existuje, ale není použit.'
                    ).format(style=style_name)
                )
                problems += 1

        if errors:
            return CheckResult(
                False,
                self.msg("errors_header", "Problémy s použitím vlastních stylů:")
                + "\n"
                + "\n".join(errors),
                None,
                problems,
            )

        return CheckResult(
            True,
            self.msg("ok", "Všechny požadované vlastní styly existují a jsou použity."),
            0,
        )
