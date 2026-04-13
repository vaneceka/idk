import re
from urllib.parse import urlparse

from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import normalize_spaces


class OnlineSourceUrlCheck(BaseCheck):
    code = "T_L07"

    _URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
    _BAD = {"internet", "online", "web", "www", "url", "odkaz", "link"}

    def _extract_url(self, src) -> tuple[str, str]:
        """
        Zkusí ze zdroje získat URL a název pole, ve kterém byla nalezena.

        Args:
            src: Bibliografický zdroj.

        Returns:
            Dvojici URL a názvu pole, nebo prázdné řetězce pokud URL nenajde.
        """
        for k in ("url", "note", "title", "publisher", "isbn"):
            v = (getattr(src, k, "") or "").strip()
            if not v:
                continue

            m = self._URL_RE.search(v)
            if m:
                url = m.group(1).strip().strip(".,;)]}>\"'")
                return (url, k)

            if v.lower().startswith(("http://", "https://", "www.")):
                url = v.strip().strip(".,;)]}>\"'")
                return (url, k)

        return ("", "")

    def _is_online_type(self, t: str) -> bool:
        """
        Ověří, zda typ zdroje označuje online zdroj.

        Args:
            t: Typ zdroje.

        Returns:
            True pokud jde o online typ, jinak False.
        """
        t = (t or "").strip().lower()
        return t in {"online", "www", "website", "internet", "web", "internetsite"}

    def _is_online(self, src, url: str) -> bool:
        """
        Ověří, zda je zdroj považován za online.

        Args:
            src: Bibliografický zdroj.
            url: URL nalezená u zdroje.

        Returns:
            True pokud je zdroj online nebo obsahuje URL, jinak False.
        """
        t = (src.type or "").strip().lower()
        return self._is_online_type(t) or bool(url)

    def _normalize_url_for_compare(self, url: str) -> str:
        """
        Normalizuje URL pro porovnávání.

        Args:
            url: URL adresa.

        Returns:
            Normalizovaná URL.
        """
        u = (url or "").strip()
        if not u:
            return ""

        if u.lower().startswith("www."):
            u = "https://" + u

        p = urlparse(u)
        scheme = (p.scheme or "").lower()
        netloc = (p.netloc or "").lower()
        path = (p.path or "").rstrip("/")

        rebuilt = f"{scheme}://{netloc}{path}"
        if p.query:
            rebuilt += "?" + p.query
        return rebuilt

    def _ok_url(self, url: str) -> tuple[bool, str, str]:
        """
        Ověří, zda URL vypadá jako platná adresa konkrétní stránky.

        Args:
            url: URL adresa.

        Returns:
            Informaci o platnosti, popis problému a doménu.
        """
        u = (url or "").strip()
        low = u.lower()

        if not u or low in self._BAD:
            return False, self.msg("bad_missing", "chybí URL / je to jen text"), ""

        if low.startswith("www."):
            u = "https://" + u

        p = urlparse(u)
        if p.scheme not in ("http", "https"):
            return False, self.msg("bad_scheme", "URL nemá http/https"), ""
        if not p.netloc:
            return False, self.msg("bad_no_domain", "URL nemá doménu"), ""

        host = p.netloc.lower().split(":")[0]

        if "." not in host:
            return False, self.msg("bad_domain_shape", "URL nevypadá jako doména"), host

        path = (p.path or "").strip()
        if path in ("", "/"):
            return (
                False,
                self.msg(
                    "bad_only_domain", "URL je jen doména (chybí konkrétní stránka)"
                ),
                host,
            )

        return True, "", host

    def _assignment_online_items(self, assignment):
        """
        Vrátí online položky bibliografie ze zadání.

        Args:
            assignment: Zadání obsahující bibliografii.

        Returns:
            Seznam online bibliografických položek.
        """
        if assignment is None or not getattr(assignment, "bibliography", None):
            return []
        out = []
        for item in assignment.bibliography:
            if not isinstance(item, dict):
                continue
            t = (item.get("type") or "").strip().lower()
            if t in {"online", "www", "website", "internet", "web", "internetsite"}:
                data = item.get("data", {}) or {}
                out.append({"type": t, "data": data})
        return out

    def _norm(self, s: str) -> str:
        """
        Normalizuje text pro porovnání.

        Args:
            s: Vstupní text.

        Returns:
            Text převedený na malá písmena a s normalizovanými mezerami.
        """
        s = (s or "").strip().lower()
        s = normalize_spaces(s)
        return s

    def _key_for_match(self, typ: str, data) -> tuple[str, str, str, str]:
        """
        Sestaví porovnávací klíč pro bibliografickou položku.

        Args:
            typ: Typ zdroje.
            data: Data zdroje jako slovník nebo objekt.

        Returns:
            Klíč složený z typu, autora, názvu a roku.
        """
        if isinstance(data, dict):
            author = data.get("author", "")
            title = data.get("title", "")
            year = str(data.get("year", "") or "")
        else:
            author = data.author
            title = data.title
            year = str(data.year or "")

        t = self._norm(typ)
        author = self._norm(author)
        title = self._norm(title)
        year = self._norm(year)

        if title.endswith("."):
            title = title[:-1].strip()

        return (t, author, title, year)

    def run(self, document, assignment=None):
        sources = list(document.iter_bibliography_sources())
        if not sources:
            return CheckResult(
                True, self.msg("ok_no_sources", "V dokumentu nejsou načtené zdroje."), 0
            )

        doc_index: dict[tuple[str, str, str, str], dict] = {}
        for s in sources:
            url, _field = self._extract_url(s)
            if not self._is_online(s, url):
                continue

            k = self._key_for_match(s.type, s)
            if k not in doc_index:
                doc_index[k] = {
                    "src": s,
                    "url": url,
                    "url_norm": self._normalize_url_for_compare(url),
                }

        assignment_online = self._assignment_online_items(assignment)

        if assignment_online:
            problems = []

            for it in assignment_online:
                typ = it["type"]
                data = it["data"]

                asg_key = self._key_for_match(typ, data)
                doc_hit = doc_index.get(asg_key)

                asg_url = (data.get("url") or "").strip()
                asg_url_norm = self._normalize_url_for_compare(asg_url)

                who = (
                    data.get("title")
                    or data.get("author")
                    or self.msg("fallback_name", "zdroj")
                )

                if doc_hit is None:
                    problems.append(
                        (
                            who,
                            self.msg(
                                "missing_source",
                                "Online pramen ze zadání není v dokumentu mezi zdroji.",
                            ),
                            asg_url or "—",
                        )
                    )
                    continue

                ok_asg, why_asg, _ = self._ok_url(asg_url)
                if not ok_asg:
                    problems.append(
                        (
                            who,
                            self.msg(
                                "asg_bad_url", "URL v zadání je nevalidní: {why}"
                            ).format(why=why_asg),
                            asg_url or "—",
                        )
                    )
                    continue

                ok_doc, why_doc, _ = self._ok_url(doc_hit["url"])
                if not ok_doc:
                    problems.append(
                        (
                            who,
                            self.msg(
                                "doc_bad_url", "URL v dokumentu je nevalidní: {why}"
                            ).format(why=why_doc),
                            doc_hit["url"] or "—",
                        )
                    )
                    continue

                if asg_url_norm and doc_hit["url_norm"] != asg_url_norm:
                    problems.append(
                        (
                            who,
                            self.msg(
                                "url_mismatch",
                                "URL v dokumentu se neshoduje se zadáním.",
                            ),
                            f'doc="{doc_hit["url"]}" vs asg="{asg_url}"',
                        )
                    )

            if not problems:
                return CheckResult(
                    True,
                    self.msg(
                        "ok", "Online prameny ze zadání mají správně vyplněné URL."
                    ),
                    0,
                )

            lines = [
                self.msg(
                    "fail_header", "Některé online prameny nemají správně vyplněné URL:"
                )
            ]
            for who, why, url in problems[:15]:
                lines.append(
                    self.msg("item", '- {who}: {why} | "{url}"').format(
                        who=who, why=why, url=url
                    )
                )
            if len(problems) > 15:
                lines.append(
                    self.msg("more", "… a dalších {n}").format(n=len(problems) - 15)
                )

            return CheckResult(False, "\n".join(lines), None, len(problems))

        problems = []
        for s in sources:
            url, from_field = self._extract_url(s)
            if not self._is_online(s, url):
                continue

            ok, why, _host = self._ok_url(url)
            if not ok:
                who = s.title or s.tag or self.msg("fallback_name", "zdroj")
                where = (
                    self.msg("from_field", "(z pole: {field})").format(field=from_field)
                    if from_field
                    else self.msg("from_none", "(URL nenalezena)")
                )
                problems.append((who, why, where, url or "—"))

        if not problems:
            return CheckResult(
                True, self.msg("ok", "Online prameny mají řádně vyplněné URL."), 0
            )

        lines = [
            self.msg(
                "fail_header", "Některé online prameny nemají správně vyplněné URL:"
            )
        ]
        for who, why, where, url in problems[:15]:
            lines.append(
                self.msg("item", '- {who}: {why} {where} | "{url}"').format(
                    who=who, why=why, where=where, url=url
                )
            )
        if len(problems) > 15:
            lines.append(
                self.msg("more", "… a dalších {n}").format(n=len(problems) - 15)
            )

        return CheckResult(False, "\n".join(lines), None, len(problems))
