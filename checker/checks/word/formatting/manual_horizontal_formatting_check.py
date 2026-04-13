import re

from checks.base_check import BaseCheck, CheckResult


class ManualHorizontalSpacingCheck(BaseCheck):
    code = "T_F22"

    BAD_PATTERNS = [
        (re.compile(r" {4,}"), "více mezer (4+)"),
        (re.compile(r"\.{4,}"), "tečky (4+)"),
        (re.compile(r"-{4,}"), "pomlčky (4+)"),
        (re.compile(r"_{4,}"), "podtržítka (4+)"),
    ]

    MAX_SAMPLES = 10
    SNIPPET_LEN = 80

    def _snippet(self, document, p) -> str:
        """
        Vrátí zkrácenou ukázku textu odstavce.

        Args:
            document: Dokument, ze kterého se text čte.
            p: Odkaz na odstavec.

        Returns:
            Text odstavce zkrácený na maximální délku.
        """
        txt = (document.paragraph_text(p) or "").strip()
        if not txt:
            txt = (document.paragraph_text_raw(p) or "").strip()
        txt = " ".join(txt.split())
        return txt[: self.SNIPPET_LEN - 1] + "…" if len(txt) > self.SNIPPET_LEN else txt

    def run(self, document, assignment=None):
        found = 0
        items: list[str] = []

        for p in document.iter_paragraphs():
            if document.paragraph_is_toc(p):
                continue

            raw = document.paragraph_text_raw(p) or ""
            if not raw.strip():
                continue

            kind = None
            for rx, label in self.BAD_PATTERNS:
                if rx.search(raw):
                    kind = label
                    break

            if not kind:
                continue

            found += 1

            if len(items) < self.MAX_SAMPLES:
                snippet = self._snippet(document, p)
                items.append(
                    self.msg("item", '- {kind} před textem "{snippet}"').format(
                        kind=kind,
                        snippet=snippet or "…",
                    )
                )

        if not found:
            return CheckResult(
                True, self.msg("ok", "Nenalezeno ruční horizontální formátování."), 0
            )

        lines = [
            self.msg(
                "fail_header",
                "V dokumentu je text horizontálně formátován pomocí mezer/znaků:",
            )
        ]
        lines += items
        if found > self.MAX_SAMPLES:
            lines.append(
                self.msg("more", "… a dalších {n}").format(n=found - self.MAX_SAMPLES)
            )

        return CheckResult(False, "\n".join(lines), None, found)
