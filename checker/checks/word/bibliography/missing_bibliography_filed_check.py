from checks.base_check import BaseCheck, CheckResult


class MissingBibliographyFieldsCheck(BaseCheck):
    code = "T_L08"

    REQUIRED_FIELDS = {
        "book": {"author", "title", "year", "publisher", "address", "standard_number"},
        "article": {
            "author",
            "title",
            "year",
            "journal",
            "volume",
            "number",
            "pages",
            "standard_number",
        },
        "online": {"author", "title", "year", "url", "access_date"},
        "www": {"author", "title", "year", "url", "access_date"},
    }

    TYPE_MAP = {
        "internetsite": "online",
        "website": "online",
        "websites": "online",
        "www": "online",
        "web": "online",
        "internet": "online",
        "articleinaperiodical": "article",
        "journalarticle": "article",
        "conferenceproceedings": "article",
    }

    FIELD_LABELS = {
        "author": "author",
        "title": "title",
        "year": "year",
        "publisher": "publisher",
        "address": "address",
        "standard_number": "standard_number",
        "journal": "journal",
        "volume": "volume",
        "number": "number",
        "pages": "pages",
        "url": "url",
        "access_date": "access_date",
    }

    def _norm_type(self, t: str) -> str:
        """
        Převede typ zdroje do sjednoceného označení.

        Args:
            t: Typ zdroje.

        Returns:
            Normalizovaný typ zdroje.
        """
        t = (t or "").strip().lower()
        return self.TYPE_MAP.get(t, t)

    def _year_ok(self, y: str) -> bool:
        """
        Ověří, zda text obsahuje platný rok.

        Args:
            y: Text s rokem.

        Returns:
            True pokud je v textu nalezen rok, jinak False.
        """
        y = (y or "").strip()
        return bool(self.YEAR_RE.search(y))

    def _stdnum(self, src) -> str:
        """
        Vrátí standardní číslo zdroje.

        Args:
            src: Zdroj bibliografických dat.

        Returns:
            Standardní číslo zdroje, nebo prázdný řetězec.
        """
        return (src.isbn or "").strip()

    def _access_date_ok(self, src) -> bool:
        """
        Ověří, zda má online zdroj vyplněné datum přístupu.

        Args:
            src: Zdroj bibliografických dat.

        Returns:
            True pokud je datum přístupu vyplněné.
        """
        return bool(str(getattr(src, "access_date", "") or "").strip())

    def _field_ok(self, src, field: str) -> bool:
        """
        Ověří, zda má zdroj vyplněné požadované pole.

        Args:
            src: Zdroj bibliografických dat.
            field: Název kontrolovaného pole.

        Returns:
            True pokud je pole vyplněné nebo platné, jinak False.
        """
        if field == "standard_number":
            return bool(self._stdnum(src))
        if field == "year":
            return self._year_ok(str(src.year or ""))
        if field == "access_date":
            return self._access_date_ok(src)

        return bool(str(getattr(src, field, "") or "").strip())

    def run(self, document, assignment=None):
        sources = list(document.iter_bibliography_sources())
        if not sources:
            return CheckResult(
                True,
                self.msg("ok_no_sources", "V dokumentu nejsou načtené zdroje."),
                0,
            )

        cited = set(document.get_unique_citation_tags())
        problems: list[str] = []

        for src in sources:
            tag = (src.tag or "").strip()
            if cited and tag and tag not in cited:
                continue

            typ = self._norm_type(src.type or "")
            required = self.REQUIRED_FIELDS.get(typ)
            if not required:
                continue

            missing = sorted(f for f in required if not self._field_ok(src, f))
            if not missing:
                continue

            who = (src.title or tag or self.msg("fallback_name", "zdroj")).strip()
            missing_labels = [self.FIELD_LABELS.get(f, f) for f in missing]

            problems.append(
                self.msg(
                    "missing_fields_item",
                    'Zdroj "{who}" ({type}) nemá vyplněno: {fields}.',
                ).format(
                    who=who,
                    type=typ,
                    fields=", ".join(missing_labels),
                )
            )

        if not problems:
            return CheckResult(
                True,
                self.msg("ok", "Zdroje mají vyplněna povinná bibliografická pole."),
                0,
            )

        lines = [
            self.msg(
                "fail_header",
                "Některé zdroje nemají vyplněna povinná bibliografická pole:",
            )
        ]
        lines += [f"- {p}" for p in problems[:25]]

        if len(problems) > 25:
            lines.append(
                self.msg("more", "… a dalších {n}").format(n=len(problems) - 25)
            )

        return CheckResult(False, "\n".join(lines), None, len(problems))