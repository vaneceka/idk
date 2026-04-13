import re
import unicodedata

from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import normalize_spaces


class UnusedBibliographySourceCheck(BaseCheck):
    code = "T_L04"

    def _norm(self, s: str) -> str:
        """
        Normalizuje text pro porovnání bez ohledu na diakritiku a interpunkci.

        Args:
            s: Vstupní text.

        Returns:
            Normalizovaný text.
        """
        s = (s or "").strip().lower()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = re.sub(r"[^a-z0-9]+", " ", s)
        return normalize_spaces(s)

    def _year(self, y: str) -> str:
        """
        Z textu vrátí rok, pokud je nalezen, jinak jeho normalizovanou podobu.

        Args:
            y: Text obsahující rok.

        Returns:
            Nalezený rok nebo normalizovaný text.
        """
        y = (y or "").strip()
        m = self.YEAR_RE.search(y)
        return m.group(1) if m else self._norm(y)

    def _standard_number(self, data: dict) -> str:
        """
        Vrátí standardní číslo zdroje v normalizované podobě.

        Args:
            data: Data bibliografické položky.

        Returns:
            Normalizované standardní číslo.
        """
        return self._norm(
            data.get("standard_number", "")
            or data.get("isbn", "")
            or data.get("issn", "")
        )

    def _make_key_from_data(self, typ: str, data: dict) -> str:
        """
        Sestaví porovnávací klíč z typu a dat bibliografické položky.

        Args:
            typ: Typ zdroje.
            data: Data bibliografické položky.

        Returns:
            Řetězec použitelný pro porovnání položek.
        """
        typ_n = self._norm(typ)

        author = self._norm(data.get("author", ""))
        title = self._norm(data.get("title", ""))
        year = self._year(str(data.get("year", "") or ""))
        publisher = self._norm(data.get("publisher", ""))
        address = self._norm(data.get("address", ""))

        standard_number = self._standard_number(data)

        return "|".join(
            [typ_n, author, title, year, publisher, address, standard_number]
        )

    def _extract_fields_from_doc_source(self, s) -> tuple[str, dict]:
        """
        Vytáhne ze zdroje dokumentu typ a základní bibliografická pole.

        Args:
            s: Zdroj z dokumentu.

        Returns:
            Typ zdroje a slovník s bibliografickými údaji.
        """
        typ = s.type or ""

        data = {
            "author": s.author or "",
            "title": s.title or "",
            "year": s.year or "",
            "publisher": s.publisher or "",
            "address": s.address or "",
            "standard_number": s.isbn or "",
        }

        return typ, data

    def run(self, document, assignment=None):
        if assignment is None or not getattr(assignment, "bibliography", None):
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."),
                0,
            )

        cit_tags = set(document.get_unique_citation_tags())

        sources = list(document.iter_bibliography_sources())
        if not sources:
            return CheckResult(
                False,
                self.msg(
                    "fail_no_sources",
                    "V dokumentu nejsou žádné zdroje, ale zadání bibliografii vyžaduje.",
                ),
                None,
                len(assignment.bibliography) or 1,
            )

        if not cit_tags:
            return CheckResult(
                False,
                self.msg(
                    "fail_no_citations",
                    "V textu nejsou žádné citace pramenů ze zadání.",
                ),
                None,
                len(assignment.bibliography) or 1,
            )

        idx: dict[str, list[str]] = {}
        for s in sources:
            tag = (s.tag or "").strip()
            typ, data = self._extract_fields_from_doc_source(s)
            doc_key = self._make_key_from_data(typ, data)
            if tag:
                idx.setdefault(doc_key, []).append(tag)

        missing_expected = []

        for item in assignment.bibliography:
            if isinstance(item, dict):
                typ = item.get("type", "") or ""
                data = item.get("data", {}) or {}
            else:
                typ = getattr(item, "type", "") or ""
                data = getattr(item, "data", {}) or {}

            author = data.get("author", "")
            year = str(data.get("year", "") or "")

            asg_key = self._make_key_from_data(typ, data)
            tags = idx.get(asg_key, [])

            if not tags:
                missing_expected.append(
                    self.msg(
                        "missing_in_doc_sources",
                        'Pramen "{author}" ({year}) není v dokumentu mezi zdroji.',
                    ).format(author=author, year=year)
                )
                continue

            if not any(t in cit_tags for t in tags):
                missing_expected.append(
                    self.msg(
                        "not_cited",
                        'Pramen "{author}" ({year}) je ve zdrojích, ale není citován v textu.',
                    ).format(author=author, year=year)
                )

        if missing_expected:
            lines = [
                self.msg(
                    "fail_header",
                    "Některé prameny jsou v bibliografii/zdrojích, ale nejsou citovány v textu:",
                )
            ]
            lines += [f"- {x}" for x in missing_expected]
            return CheckResult(False, "\n".join(lines), None, len(missing_expected))

        return CheckResult(
            True, self.msg("ok", "Prameny ze zadání jsou v textu citovány."), 0
        )
