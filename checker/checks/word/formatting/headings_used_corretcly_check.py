from checks.base_check import BaseCheck, CheckResult


class HeadingsUsedCorrectlyCheck(BaseCheck):
    code = "T_F26"

    def _count(self, items):
        """
        Spočítá výskyty jednotlivých položek v kolekci.

        Args:
            items: Kolekce položek.

        Returns:
            Slovník s počty výskytů jednotlivých položek.
        """
        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        return counts

    def run(self, document, assignment=None):
        if assignment is None or not hasattr(assignment, "headlines"):
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."),
                0,
                count=0,
            )

        expected = [(h["text"].strip(), int(h["level"])) for h in assignment.headlines]

        actual = document.iter_headings()

        expected_counts = self._count(expected)
        actual_counts = self._count(actual)

        missing = []
        for k, v in expected_counts.items():
            missing.extend([k] * max(0, v - actual_counts.get(k, 0)))

        extra = []
        for k, v in actual_counts.items():
            extra.extend([k] * max(0, v - expected_counts.get(k, 0)))

        if not missing and not extra:
            return CheckResult(
                True, self.msg("ok", "Všechny nadpisy odpovídají."), 0, count=0
            )

        lines = []
        item_tpl = self.msg("item_line", "- {text} (H{level})")

        if missing:
            lines.append(self.msg("missing_header", "Chybí nadpisy:"))
            lines += [item_tpl.format(text=t, level=lvl) for t, lvl in missing]

        if extra:
            lines.append(self.msg("extra_header", "Navíc / špatné nadpisy:"))
            lines += [item_tpl.format(text=t, level=lvl) for t, lvl in extra]

        problems = len(missing) + len(extra)

        return CheckResult(False, "\n".join(lines), None, problems)
