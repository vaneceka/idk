from checks.base_check import BaseCheck, CheckResult


class HeadingStyleCheck(BaseCheck):
    def __init__(self, level: int):
        self.level = level

        code_map = {
            1: "T_F05",
            2: "T_F06",
            3: "T_F07",
        }
        self.code = code_map[level]

    def run(self, document, assignment=None):
        if assignment is None:
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."),
                0,
                count=0,
            )

        expected = assignment.styles.get(f"Heading {self.level}")
        if expected is None:
            return CheckResult(
                True,
                self.msg("skip_not_required", "Zadání styl neřeší."),
                0,
                count=0,
            )

        actual_styles = document.get_heading_styles(self.level)
        if not actual_styles:
            return CheckResult(
                False,
                self.msg(
                    "missing_style",
                    "V dokumentu neexistuje žádný použitý styl pro nadpis úrovně {level}.",
                ).format(level=self.level),
                None,
            )

        expected_num_level = getattr(expected, "numLevel", None)
        is_numbered, is_hierarchical, actual_num_level = (
            document.get_heading_numbering_info(self.level)
        )

        best_diffs: list[str] | None = None

        for actual in actual_styles:
            diffs = actual.diff(expected)

            local_diffs = list(diffs)

            if expected_num_level is not None:
                if not is_numbered:
                    local_diffs.append(
                        self.msg("num_not_numbered", "numLevel: nadpis není číslovaný")
                    )
                elif not is_hierarchical:
                    local_diffs.append(
                        self.msg(
                            "num_not_hierarchical",
                            "numLevel: číslování není hierarchické",
                        )
                    )
                elif actual_num_level != expected_num_level:
                    local_diffs.append(
                        self.msg(
                            "num_wrong_level",
                            "numLevel: očekáváno {expected}, nalezeno {found}",
                        ).format(expected=expected_num_level, found=actual_num_level)
                    )

            if not local_diffs:
                return CheckResult(
                    True,
                    self.msg(
                        "ok", "Styl nadpisu úrovně {level} odpovídá zadání."
                    ).format(level=self.level),
                    0,
                )

            if best_diffs is None or len(local_diffs) < len(best_diffs):
                best_diffs = local_diffs

        header = self.msg(
            "diffs_header", "Styl nadpisu úrovně {level} neodpovídá zadání:"
        ).format(level=self.level)
        message = header
        if best_diffs:
            message += "\n" + "\n".join(f"- {d}" for d in best_diffs)

        return CheckResult(False, message, None)
