from checks.base_check import BaseCheck, CheckResult


class FooterLinkedToPreviousCheck(BaseCheck):
    def __init__(self, section_number: int):
        self.section_number = section_number
        self.section_index = section_number - 1

        code_map = {
            2: "T_Z05",
            3: "T_Z10",
        }
        self.code = code_map[section_number]

    def run(self, document, assignment=None):
        if self.code is None:
            return CheckResult(
                True,
                self.msg("not_defined", "Kontrola není definována pro tento oddíl."),
                0,
                count=0,
            )

        if document.section_count() <= self.section_index:
            return CheckResult(
                True,
                self.msg("section_missing", "Oddíl v dokumentu neexistuje."),
                0,
                count=0,
            )

        linked = document.footer_is_linked_to_previous(self.section_index)

        if linked is None:
            return CheckResult(
                True,
                self.msg(
                    "not_supported",
                    "Propojení zápatí mezi oddíly není v tomto formátu podporováno.",
                ),
                0,
            )

        if linked:
            return CheckResult(
                False,
                self.msg("linked", "Zápatí oddílu je propojené s předchozím oddílem."),
                None,
            )

        return CheckResult(
            True,
            self.msg(
                "not_linked", "Zápatí oddílu není propojené s předchozím oddílem."
            ),
            0,
        )
