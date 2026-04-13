from checks.base_check import BaseCheck, CheckResult


class HeadingHierarchicalNumberingCheck(BaseCheck):
    code = "T_F14"

    def run(self, document, assignment=None):
        broken = []

        for level in (1, 2, 3):
            is_numbered, is_hierarchical, num_level = (
                document.get_heading_numbering_info(level)
            )

            if not is_numbered:
                broken.append(
                    self.msg(
                        "broken_not_numbered", "Nadpis {level}: není číslovaný"
                    ).format(level=level)
                )
                continue

            if not is_hierarchical:
                broken.append(
                    self.msg(
                        "broken_not_hierarchical",
                        "Nadpis {level}: není plně hierarchické číslování (např. 1.1.{ex})",
                    ).format(level=level, ex=("1" if level == 3 else ""))
                )
                continue

            expected_level = level - 1
            if num_level != expected_level:
                broken.append(
                    self.msg(
                        "broken_wrong_level",
                        "Nadpis {level}: špatná úroveň (očekáváno {expected}, nalezeno {found})",
                    ).format(level=level, expected=expected_level, found=num_level)
                )

        if broken:
            msg = (
                self.msg(
                    "errors_header",
                    "Nadpisy nemají správně nastavené automatické hierarchické číslování:",
                )
                + "\n"
                + "\n".join(f"- {b}" for b in broken)
            )
            return CheckResult(False, msg, None)

        return CheckResult(
            True,
            self.msg(
                "ok", "Automatické hierarchické číslování nadpisů je nastaveno správně."
            ),
            0,
        )
