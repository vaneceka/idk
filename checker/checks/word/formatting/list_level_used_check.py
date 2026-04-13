from checks.base_check import BaseCheck, CheckResult


class ListLevelUsedCheck(BaseCheck):
    def __init__(self, level: int):
        self.level = level

        code_map = {
            1: "T_F09",
            2: "T_F10",
        }
        self.code = code_map[level]

    def run(self, document, assignment=None):
        if document.has_list_level(self.level):
            return CheckResult(
                True,
                self.msg("ok", f"Seznam {self.level}. úrovně je použit."),
                0,
            )

        return CheckResult(
            False,
            self.msg("fail", f"V dokumentu není použit seznam {self.level}. úrovně."),
            None,
        )
