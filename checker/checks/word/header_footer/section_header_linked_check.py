from checks.base_check import BaseCheck, CheckResult


class HeaderNotLinkedToPreviousCheck(BaseCheck):
    def __init__(self, section_number: int):
        self.section_number = section_number
        self.section_index = section_number - 1

        code_map = {2: "T_Z04", 3: "T_Z09"}
        self.code = code_map[section_number]

    def run(self, document, assignment=None):
        result = document.header_is_linked_to_previous(self.section_index)

        if result is None:
            return CheckResult(
                True,
                self.msg("section_missing", "Oddíl v dokumentu neexistuje."),
                0,
                count=0,
            )

        if result:
            return CheckResult(
                False,
                self.msg("fail", "Záhlaví je propojené s předchozím oddílem."),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", "Záhlaví není propojené s předchozím oddílem."),
            0,
        )
