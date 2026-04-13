from checks.base_check import BaseCheck, CheckResult


class MainChapterStartsOnNewPageCheck(BaseCheck):
    code = "T_F21"

    def run(self, document, assignment=None):
        errors = []
        count = 0

        item_tpl = self.msg("item", 'Hlavní kapitola "{text}" nezačíná na nové straně.')

        for h in document.iter_main_headings():
            text = document.get_visible_text(h)

            if document.heading_starts_on_new_page(h):
                continue

            errors.append(item_tpl.format(text=text))
            count += 1

        if errors:
            return CheckResult(
                False,
                "\n".join(errors),
                None,
                count,
            )

        return CheckResult(
            True, self.msg("ok", "Všechny hlavní kapitoly začínají na nové straně."), 0
        )
