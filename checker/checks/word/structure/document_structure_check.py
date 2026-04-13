from checks.base_check import BaseCheck, CheckResult


class DocumentStructureCheck(BaseCheck):
    code = "T_O03"

    def run(self, document, assignment=None):
        headings = document.iter_headings()
        if not headings:
            return CheckResult(
                True, self.msg("no_headings", "Dokument neobsahuje nadpisy."), 0
            )

        errors = []
        last_level = None

        for text, level in headings:
            if last_level is None and level != 1:
                errors.append(
                    self.msg(
                        "must_start_h1",
                        'Nadpis "{text}" je úrovně {level}, dokument musí začínat Nadpisem 1.',
                    ).format(text=text, level=level)
                )

            if last_level is not None and level > last_level + 1:
                errors.append(
                    self.msg(
                        "skip_level",
                        'Nadpis "{text}" (úroveň {level}) přeskakuje úroveň (předchozí byla {last_level}).',
                    ).format(text=text, level=level, last_level=last_level)
                )

            last_level = level

        if errors:
            return CheckResult(
                False,
                self.msg("errors_header", "Chybná hierarchie nadpisů:")
                + "\n"
                + "\n".join(errors),
                None,
                len(errors),
            )

        return CheckResult(True, self.msg("ok", "Hierarchie nadpisů je správná."), 0)
