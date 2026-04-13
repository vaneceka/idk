from checks.base_check import BaseCheck, CheckResult


class SectionHeaderEmptyCheck(BaseCheck):
    def __init__(self, section_number: int):
        self.section_number = section_number
        self.section_index = section_number - 1

        code_map = {
            1: "T_Z02",
            3: "T_Z11",
        }
        self.code = code_map[section_number]

    def run(self, document, assignment=None):
        if self.code is None:
            return CheckResult(
                True,
                self.msg(
                    "skip_not_defined", "Kontrola není definována pro tento oddíl."
                ),
                0,
                count=0,
            )

        if document.section_count() <= self.section_index:
            return CheckResult(
                True,
                self.msg("skip_section_missing", "Oddíl v dokumentu neexistuje."),
                0,
                count=0,
            )

        empty = document.section_header_is_empty(self.section_index)

        if empty is None:
            return CheckResult(
                True,
                self.msg("skip_header_undefined", "Záhlaví oddílu není definováno."),
                0,
                count=0,
            )

        if empty:
            return CheckResult(
                True, self.msg("ok_empty", "Záhlaví oddílu je prázdné."), 0, count=0
            )

        return CheckResult(
            False,
            self.msg(
                "fail_not_empty", "{section}. oddíl obsahuje neprázdné záhlaví."
            ).format(section=self.section_number),
            None,
        )
