from checks.base_check import BaseCheck, CheckResult


class ManualVerticalSpacingCheck(BaseCheck):
    code = "T_F23"

    MAX_EMPTY_BEFORE_TEXT = 2
    MAX_EMPTY_BEFORE_HEADING = 3

    def _is_allowed_spacing(self, document, paragraph, empty_count):
        """
        Ověří, zda je počet prázdných řádků před odstavcem přípustný.

        Args:
            document: Dokument obsahující odstavec.
            paragraph: Odkaz na kontrolovaný odstavec.
            empty_count: Počet prázdných řádků před odstavcem.

        Returns:
            True pokud je dané odsazení povolené, jinak False.
        """
        if not document.paragraph_has_text(paragraph):
            return True

        if document.paragraph_is_generated(paragraph):
            return True

        if document.paragraph_has_page_break(paragraph):
            return True

        if document.paragraph_has_spacing_before(paragraph):
            return True

        if document.paragraph_is_heading(paragraph):
            return empty_count <= self.MAX_EMPTY_BEFORE_HEADING

        return empty_count <= self.MAX_EMPTY_BEFORE_TEXT

    def _previous_nonempty_paragraph(self, document, paragraphs, start_index):
        """
        Najde předchozí neprázdný odstavec před zadaným indexem.

        Args:
            document: Dokument obsahující odstavce.
            paragraphs: Seznam odstavců.
            start_index: Index, před kterým se má hledat.

        Returns:
            Předchozí neprázdný odstavec nebo None.
        """
        k = start_index - 1
        while k >= 0:
            p = paragraphs[k]
            if document.paragraph_has_text(p):
                return p
            k -= 1
        return None

    def _is_after_generated_block(self, document, paragraphs, start_index):
        """
        Ověří, zda prázdné odstavce následují po generovaném bloku.

        Args:
            document: Dokument obsahující odstavce.
            paragraphs: Seznam odstavců.
            start_index: Index prvního prázdného odstavce.

        Returns:
            True pokud před nimi stojí generovaný odstavec, jinak False.
        """
        prev_p = self._previous_nonempty_paragraph(document, paragraphs, start_index)
        if prev_p is None:
            return False

        return document.paragraph_is_generated(prev_p)

    def run(self, document, assignment=None):
        paragraphs = list(document.iter_paragraphs())
        errors = []

        i = 0
        total_length = len(paragraphs)
        while i < total_length - 1:
            p = paragraphs[i]

            if document.paragraph_has_page_break(p):
                i += 1
                continue

            if document.paragraph_has_text(p):
                i += 1
                continue

            if not document.paragraph_is_empty(p):
                i += 1
                continue

            empty_count = 1
            j = i + 1

            while j < total_length:
                pj = paragraphs[j]

                if document.paragraph_has_page_break(pj):
                    break

                if not document.paragraph_is_empty(pj):
                    break

                empty_count += 1
                j += 1

            if empty_count <= self.MAX_EMPTY_BEFORE_TEXT:
                i = j
                continue

            if self._is_after_generated_block(document, paragraphs, i):
                i = j
                continue

            if j >= total_length:
                break

            next_p = paragraphs[j]

            if self._is_allowed_spacing(document, next_p, empty_count):
                i = j
                continue

            errors.append(
                {
                    "style": document.paragraph_style_name(next_p) or "bez stylu",
                    "text": document.paragraph_text(next_p),
                    "count": empty_count,
                }
            )

            i = j

        if errors:
            max_lines = int(self.msg("max_lines", "5") or "5")
            preview_len = int(self.msg("preview_len", "80") or "80")

            line_tpl = self.msg("line", '- {count} prázdné řádky před textem "{text}…"')

            lines = []
            for e in errors[:max_lines]:
                preview = (e["text"] or "")[:preview_len]
                lines.append(
                    line_tpl.format(
                        count=e["count"],
                        text=preview,
                    )
                )

            return CheckResult(
                False,
                self.msg(
                    "fail_header",
                    "V dokumentu je text vertikálně formátován pomocí více prázdných řádků:",
                )
                + "\n"
                + "\n".join(lines),
                None,
                len(errors),
            )

        return CheckResult(
            True,
            self.msg(
                "ok",
                "Nenalezeno ruční vertikální odsazení pomocí více prázdných řádků.",
            ),
            0,
        )