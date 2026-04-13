from checks.base_check import BaseCheck, CheckResult


class TocHeadingNumberingCheck(BaseCheck):
    code = "T_F15"

    def run(self, document, assignment=None):
        any_toc = False
        mismatches = []

        for level in (1, 2, 3):
            toc_has = document.toc_level_contains_numbers(level)
            if toc_has is None:
                continue

            any_toc = True
            head_num = document.heading_level_is_numbered(level)

            if not toc_has and not head_num:
                continue

            if toc_has != head_num:
                mismatches.append((level, toc_has, head_num))

        if not any_toc:
            return CheckResult(True, self.msg("no_toc", "Obsah v dokumentu není."), 0)

        if mismatches:
            yes = self.msg("toc_yes", "ANO")
            no = self.msg("toc_no", "NE")
            line_tpl = self.msg(
                "line_level",
                "- Úroveň {level}: TOC čísla={toc}, nadpisy číslované={head}",
            )

            lines = [
                line_tpl.format(
                    level=lvl,
                    toc=yes if toc_has else no,
                    head=yes if head_num else no,
                )
                for (lvl, toc_has, head_num) in mismatches
            ]

            msg = (
                self.msg("errors_header", "Číslování nadpisů a obsah nejsou v souladu:")
                + "\n"
                + "\n".join(lines)
            )

            return CheckResult(False, msg, None)

        return CheckResult(
            True, self.msg("ok", "Číslování nadpisů odpovídá obsahu."), 0
        )
