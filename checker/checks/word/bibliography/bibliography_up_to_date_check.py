from checks.base_check import BaseCheck, CheckResult


class BibliographyNotUpdatedCheck(BaseCheck):
    code = "T_L02"

    def run(self, document, assignment=None):
        cit_tags = set(document.get_unique_citation_tags())

        if not document.has_bibliography():
            return CheckResult(
                True,
                self.msg("ok_no_bib_field", "Bibliografie chybí."),
                0,
            )

        items = int(document.count_bibliography_items())
        src_tags = set(document.iter_bibliography_source_tags())
        dups = document.find_duplicate_bibliography_tags()

        uniq = len(cit_tags)
        missing = sorted(cit_tags - src_tags)

        if uniq > 0 and items < uniq:
            return CheckResult(
                False,
                self.msg(
                    "fail_not_updated",
                    "Seznam literatury není aktuální "
                    "(citací: {citations}, položek: {items}).",
                ).format(
                    citations=uniq,
                    items=items,
                ),
                None,
            )

        lines = [self.msg("fail_header", "Problém v bibliografických zdrojích:")]
        has_problem = False

        if missing:
            has_problem = True
            lines.append(self.msg("missing_header", "Chybí zdroje pro citace:"))
            lines += [f"- {tag}" for tag in missing]

        if dups:
            has_problem = True
            lines.append(self.msg("dups_header", "Duplicitní zdroje (Tag):"))
            lines += [f"- {tag}" for tag in dups]

        if uniq == 0 and (items > 0 or src_tags):
            has_problem = True
            lines.append(
                self.msg(
                    "extra_header",
                    "V bibliografii jsou položky navíc "
                    "(nejsou citovány v textu):",
                )
            )
            lines += [f"- {tag}" for tag in sorted(src_tags)[:25]]

        if has_problem:
            return CheckResult(False, "\n".join(lines), None)

        ref_order_tags = document.iter_bibliography_source_tags_in_order()
        rendered_order_tags = document.iter_rendered_bibliography_tags_in_order()

        ref_order_tags = [tag for tag in ref_order_tags if tag in cit_tags]
        rendered_order_tags = [tag for tag in rendered_order_tags if tag in cit_tags]

        if uniq > 0 and ref_order_tags and rendered_order_tags:
            if ref_order_tags != rendered_order_tags:
                lines = [
                    self.msg(
                        "fail_order_header",
                        "Pořadí položek v seznamu literatury neodpovídá "
                        "internímu pořadí zdrojů.",
                    )
                ]

                diffs = self._build_order_diffs(ref_order_tags, rendered_order_tags)

                if diffs:
                    lines += [f"- {item}" for item in diffs[:10]]
                else:
                    lines.append(
                        self.msg(
                            "order_length_mismatch",
                            "Pořadí položek v seznamu literatury se liší.",
                        )
                    )

                return CheckResult(False, "\n".join(lines), None)

        if uniq == 0:
            return CheckResult(
                True,
                self.msg("ok_no_citations", "Dokument neobsahuje citace."),
                0,
            )

        return CheckResult(
            True,
            self.msg("ok", "Seznam literatury odpovídá citacím."),
            0,
        )

    def _build_order_diffs(
        self,
        expected_order: list[str],
        actual_order: list[str],
    ) -> list[str]:
        diffs: list[str] = []
        limit = min(len(expected_order), len(actual_order))

        for i in range(limit):
            if expected_order[i] == actual_order[i]:
                continue

            diffs.append(
                self.msg(
                    "order_item",
                    'Na pozici {pos} má být "{expected}", ale je "{found}".',
                ).format(
                    pos=i + 1,
                    expected=expected_order[i],
                    found=actual_order[i],
                )
            )

        if len(expected_order) != len(actual_order):
            diffs.append(
                self.msg(
                    "order_length_mismatch",
                    "Počet položek v seznamu literatury se liší.",
                )
            )

        return diffs