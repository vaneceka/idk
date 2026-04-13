from checks.base_check import BaseCheck, CheckResult


class TOCFirstSectionContentCheck(BaseCheck):
    code = "T_O05"

    def run(self, document, assignment=None):
        toc_section = None
        for i in range(document.section_count()):
            if document.has_toc_in_section(i):
                toc_section = i
                break

        if toc_section is None:
            return CheckResult(True, self.msg("no_toc", "Obsah neexistuje."), 0)

        toc_items: list[str] = []
        for p in document.iter_toc_paragraphs():
            txt = document.paragraph_text(p)
            if txt:
                toc_items.append(txt)

        if not toc_items:
            return CheckResult(
                False,
                self.msg(
                    "toc_empty",
                    "Obsah byl nalezen, ale nepodařilo se načíst žádné položky.",
                ),
                0,
            )

        first_section_headings: set[str] = set()
        for el in document.iter_section_blocks(0):
            if not document.paragraph_is_heading(el):
                continue

            txt = document.get_visible_text(el)
            if txt:
                first_section_headings.add(txt)

        normalized_headings = {
            document.normalize_heading_text(h) for h in first_section_headings
        }

        illegal = []
        for item in toc_items:
            norm_item = document.normalize_heading_text(item)
            if norm_item in normalized_headings:
                illegal.append(item)

        if illegal:
            header = self.msg(
                "errors_header", "Obsah obsahuje nadpisy z prvního oddílu:"
            )
            item_tpl = self.msg("item_line", "- {text}")
            lines = "\n".join(item_tpl.format(text=t) for t in illegal[:5])

            return CheckResult(
                False,
                header + "\n" + lines,
                None,
                len(illegal),
            )

        return CheckResult(
            True, self.msg("ok", "Obsah neobsahuje žádný text z prvního oddílu."), 0
        )
