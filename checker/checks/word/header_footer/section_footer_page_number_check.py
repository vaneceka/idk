from checks.base_check import BaseCheck, CheckResult


class SectionFooterHasPageNumberCheck(BaseCheck):
    def __init__(self, section_number: int):
        self.section_number = section_number
        self.section_index = section_number - 1

        code_map = {2: "T_Z07", 3: "T_Z12"}
        self.code = code_map[section_number]

    def run(self, document, assignment=None):
        result = document.section_footer_has_page_number(self.section_index)

        if result is None:
            return CheckResult(
                True,
                self.msg("section_missing", "Oddíl v dokumentu neexistuje."),
                0,
            )

        if result:
            return CheckResult(
                True,
                self.msg(
                    "ok", "Zápatí {section}. oddílu obsahuje číslo stránky."
                ).format(section=self.section_number),
                0,
            )

        return CheckResult(
            False,
            self.msg("fail", "{section}. oddíl nemá číslo stránky v zápatí.").format(
                section=self.section_number
            ),
            None,
        )
