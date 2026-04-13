from checks.base_check import BaseCheck, CheckResult


class FirstChapterStartsOnPageOneCheck(BaseCheck):
    code = "T_O07"

    def run(self, document, assignment=None):
        if document.section_count() < 2:
            return CheckResult(
                False,
                self.msg(
                    "missing_second_section",
                    "Dokument nemá druhý oddíl - nelze ověřit začátek kapitol.",
                ),
                None,
            )

        starts_at_one = document.second_section_page_number_starts_at_one()
        if starts_at_one is False:
            return CheckResult(
                False,
                self.msg(
                    "page_num_not_starting_1",
                    "Číslování stránek ve druhém oddílu nezačíná od 1.",
                ),
                None,
            )
        if starts_at_one is None:
            return CheckResult(
                False,
                self.msg(
                    "page_num_cannot_verify",
                    "Nelze ověřit číslování stránek ve druhém oddílu.",
                ),
                None,
            )

        ok = document.first_chapter_is_first_content_in_section(1)
        if not ok:
            return CheckResult(
                False,
                self.msg(
                    "visible_content_before_ch1",
                    "Před první kapitolou je ve druhém oddílu viditelný obsah.",
                ),
                None,
            )

        return CheckResult(
            True,
            self.msg("ok", "První kapitola ve druhém oddílu začíná na straně 1."),
            0,
        )
