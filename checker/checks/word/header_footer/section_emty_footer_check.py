from checks.base_check import BaseCheck, CheckResult


class SectionFooterEmptyCheck(BaseCheck):
    code = "T_Z03"

    def __init__(self, section_number: int):
        self.section_number = section_number
        self.section_index = section_number - 1

    def run(self, document, assignment=None):
        if document.section_count() <= self.section_index:
            return CheckResult(
                True,
                self.msg("skip_section_missing", "Oddíl v dokumentu neexistuje."),
                0,
            )

        empty = document.section_footer_is_empty(self.section_index)
        if empty is None:
            return CheckResult(
                True,
                self.msg("skip_footer_undefined", "Zápatí oddílu není definováno."),
                0,
            )

        if empty:
            return CheckResult(
                True, self.msg("ok_empty", "Zápatí oddílu je prázdné."), 0
            )

        return CheckResult(
            False,
            self.msg(
                "fail_not_empty", "{section}. oddíl obsahuje neprázdné zápatí."
            ).format(section=self.section_number),
            None,
        )
