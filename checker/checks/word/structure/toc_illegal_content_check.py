from checks.base_check import BaseCheck, CheckResult


class TOCIllegalContentCheck(BaseCheck):
    code = "T_O06"

    def run(self, document, assignment=None):
        exists, errors, msg_key = document.get_toc_illegal_content_errors()

        if not exists:
            return CheckResult(
                True, self.msg(msg_key or "no_toc", "Obsah v dokumentu není."), 0
            )

        if errors:
            header = self.msg("illegal_header", "V obsahu jsou neplatné položky:")
            lines = []

            for error in errors:
                text = self.msg(error.code, "{text}").format(**error.params)
                lines.append(self.msg("item_line", "- {item}").format(item=text))

            return CheckResult(
                False,
                header + "\n" + "\n".join(lines),
                None,
                len(errors),
            )

        return CheckResult(
            True,
            self.msg("ok", "Obsah obsahuje pouze platné položky."),
            0,
        )
