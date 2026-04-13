from checks.base_check import BaseCheck, CheckResult


class CustomStyleInheritanceCheck(BaseCheck):
    name = "Vlastní styl s dědičností"
    code = "T_F19"

    def _norm(self, s: str | None) -> str:
        """
        Normalizuje text pro porovnání odstraněním vybraných oddělovačů.

        Args:
            s: Vstupní text.

        Returns:
            Text převedený na malá písmena bez pomlček, podtržítek a mezer.
        """
        return (s or "").lower().replace("-", "").replace("_", "").replace(" ", "")

    def run(self, document, assignment=None):
        if assignment is None:
            return CheckResult(
                True, self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."), 0
            )

        errors = []

        for style_name, expected in assignment.styles.items():
            if not expected or not expected.basedOn:
                continue

            if not document.style_exists(style_name):
                continue

            actual_parent = document.get_style_parent(style_name)

            if actual_parent is None:
                errors.append(
                    self.msg(
                        "missing_parent",
                        'Styl "{style}" nemá nastavenou dědičnost (má dědit z "{expected}").',
                    ).format(style=style_name, expected=expected.basedOn)
                )
                continue

            if self._norm(actual_parent) != self._norm(expected.basedOn):
                errors.append(
                    self.msg(
                        "wrong_parent",
                        'Styl "{style}" dědí z "{actual}", ale má dědit z "{expected}".',
                    ).format(
                        style=style_name,
                        actual=actual_parent,
                        expected=expected.basedOn,
                    )
                )

        if errors:
            return CheckResult(
                False,
                self.msg("errors_header", "Chyby v dědičnosti stylů:")
                + "\n"
                + "\n".join(errors),
                None,
                len(errors),
            )

        return CheckResult(
            True, self.msg("ok", "Požadovaná dědičnost stylů je správně nastavena."), 0
        )
