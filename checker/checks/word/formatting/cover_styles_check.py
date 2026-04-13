from checks.base_check import BaseCheck, CheckResult


class CoverStylesCheck(BaseCheck):
    code = "T_F24"

    def run(self, document, assignment=None):
        if assignment is None:
            return CheckResult(
                True,
                self.msg(
                    "skip_no_assignment", "Chybí assignment - check přeskočen."
                ),
                0,
                count=0,
            )

        errors = []
        bad_count = 0

        required = {
            "desky-fakulta": assignment.styles.get("desky-fakulta"),
            "desky-nazev-prace": assignment.styles.get("desky-nazev-prace"),
            "desky-rok-a-jmeno": assignment.styles.get("desky-rok-a-jmeno"),
        }

        for key, expected in required.items():
            if expected is None:
                continue

            actual = document.get_cover_style(key)

            if actual is None:
                bad_count += 1
                errors.append(
                    self.msg(
                        "style_missing", 'Styl pro "{key}" nebyl v dokumentu nalezen.'
                    ).format(key=key)
                )
                continue

            diffs = actual.diff(
                expected, doc_default_size=document.get_doc_default_font_size()
            )

            if diffs:
                bad_count += 1
                diff_header = self.msg(
                    "style_diff_header", 'Styl "{key}" neodpovídá zadání:'
                ).format(key=key)
                diff_item = self.msg("diff_item", "  - {diff}")
                errors.append(
                    diff_header
                    + "\n"
                    + "\n".join(diff_item.format(diff=d) for d in diffs)
                )

        if errors:
            return CheckResult(
                False,
                self.msg("errors_header", "Chyby ve stylech desek:")
                + "\n"
                + "\n".join(errors),
                None,
                count=bad_count,
            )

        return CheckResult(
            True, self.msg("ok", "Styly desek odpovídají zadání."), 0, count=0
        )
