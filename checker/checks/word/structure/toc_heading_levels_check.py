from checks.base_check import BaseCheck, CheckResult


class TOCHeadingLevelsCheck(BaseCheck):
    code = "T_O04"

    def run(self, document, assignment=None):
        ok, missing = document.toc_missing_used_headings(max_level=3)

        if ok is None:
            return CheckResult(
                False,
                self.msg("no_toc", "V dokumentu nebyl nalezen obsah."),
                None,
            )

        if ok:
            return CheckResult(
                True,
                self.msg("ok", "Obsah zahrnuje všechny použité nadpisy úrovní H1-H3."),
                0,
            )

        preview = "\n".join(f"- {t}" for t in missing[:10])
        more = f"\n(+{len(missing) - 10} dalších)" if len(missing) > 10 else ""

        return CheckResult(
            False,
            self.msg("fail", "V obsahu chybí některé použité nadpisy (H1-H3):")
            + "\n"
            + preview
            + more,
            None,
        )
