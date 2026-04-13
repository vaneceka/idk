from checks.base_check import BaseCheck, CheckResult


class CitationInWrongPlaceCheck(BaseCheck):
    code = "T_L05"

    def run(self, document, assignment=None):
        problems = document.find_citations_in_wrong_places()

        if not problems:
            return CheckResult(True, self.msg("ok"), 0)

        lines = [self.msg("fail_header")]

        for p in problems[:15]:
            reason_key = p.get("reason_key") or "reason_in_heading"
            reason_txt = self.msg(reason_key)

            snippet = p.get("snippet") or ""
            snippet_txt = f' | "{snippet}"' if snippet else ""

            lines.append(
                self.msg("item").format(
                    num=p.get("num", "?"),
                    tag=p.get("tag", "?"),
                    reason=reason_txt,
                    snippet=snippet_txt,
                )
            )

        if len(problems) > 15:
            lines.append(self.msg("more").format(n=len(problems) - 15))

        return CheckResult(False, "\n".join(lines), None, len(problems))
