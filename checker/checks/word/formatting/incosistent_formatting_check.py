from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import group_inline_formatting_by_text


class InconsistentFormattingCheck(BaseCheck):
    code = "T_F03"

    def run(self, document, assignment=None):
        errors = document.find_inline_formatting()

        if not errors:
            return CheckResult(
                True, self.msg("ok", "Nenalezeno nekonzistentní formátování."), 0
            )

        grouped = group_inline_formatting_by_text(errors)

        item_tpl = self.msg("item_line", '- Text: "{text}"\n  Zásahy: {problems}')
        max_examples = int(self.msg("max_examples", "5") or "5")
        preview_len = int(self.msg("preview_len", "80") or "80")

        lines = [
            item_tpl.format(
                text=(item["text"] or "")[:preview_len],
                problems=", ".join(
                    self.msg(f"problem_{problem}", problem)
                    for problem in item["problems"]
                ),
            )
            for item in grouped[:max_examples]
        ]

        message = (
            self.msg(
                "errors_header", "V dokumentu je použito nekonzistentní formátování:"
            )
            + "\n"
            + "\n".join(lines)
        )

        if len(grouped) > max_examples:
            message += "\n" + self.msg(
                "more_items",
                f"... a dalších {len(grouped) - max_examples} případů.",
            )

        return CheckResult(
            False,
            message,
            None,
            len(errors),
        )