from collections import Counter, defaultdict

from checks.base_check import BaseCheck, CheckResult

class RangeMatchesAssignmentCheck(BaseCheck):
    code = "T_X04"

    EXTRA_HEADINGS_ABS = 3
    EXTRA_HEADINGS_RATIO = 0.30

    EXTRA_OBJECTS_ABS = 1
    EXTRA_OBJECTS_RATIO = 0.50

    def _norm_heading(self, document, text: str) -> str:
        """
        Normalizuje text nadpisu pro porovnání.

        Args:
            document: Dokument, který poskytuje pravidla normalizace nadpisů.
            text: Text nadpisu.

        Returns:
            Normalizovaný text nadpisu.
        """
        return document.normalize_heading_text(text or "")

    def _allowed_extra(self, base: int, abs_extra: int, ratio: float) -> int:
        """
        Vypočítá povolený počet nadbytečných položek.

        Args:
            base: Základní počet položek.
            abs_extra: Minimální povolený absolutní přesah.
            ratio: Poměrný povolený přesah vůči základu.

        Returns:
            Povolený počet nadbytečných položek.
        """
        return max(abs_extra, int(round(base * ratio)))

    def run(self, document, assignment=None):
        if assignment is None:
            return CheckResult(
                True, self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."), 0
            )

        expected = getattr(assignment, "headlines", None) or []
        doc_heads = document.iter_headings() or []

        doc_index = defaultdict(set)
        doc_count_by_level = Counter()
        for txt, lvl in doc_heads:
            n = self._norm_heading(document, txt)
            if not n:
                continue
            try:
                lvli = int(lvl)
            except Exception:
                continue
            doc_index[n].add(lvli)
            doc_count_by_level[lvli] += 1

        missing_headings = []
        wrong_level = []

        expected_count_by_level = Counter()
        for h in expected:
            if isinstance(h, dict):
                exp_txt = h.get("text", "")
                exp_lvl = h.get("level", None)
            else:
                exp_txt = getattr(h, "text", "")
                exp_lvl = getattr(h, "level", None)

            n = self._norm_heading(document, exp_txt)
            if not n:
                continue
            try:
                exp_lvl_i = int(exp_lvl)
            except Exception:
                continue

            expected_count_by_level[exp_lvl_i] += 1

            levels_in_doc = doc_index.get(n)
            if not levels_in_doc:
                missing_headings.append(f'"{exp_txt}" (lvl {exp_lvl_i})')
                continue

            if exp_lvl_i not in levels_in_doc:
                wrong_level.append(
                    f'"{exp_txt}" má být lvl {exp_lvl_i}, ale v dokumentu je {sorted(levels_in_doc)}'
                )

        expected_total = sum(expected_count_by_level.values())
        doc_total = sum(doc_count_by_level.values())
        allowed_extra = self._allowed_extra(
            expected_total, self.EXTRA_HEADINGS_ABS, self.EXTRA_HEADINGS_RATIO
        )

        too_many_headings = None
        if expected_total > 0 and doc_total > expected_total + allowed_extra:
            too_many_headings = (doc_total, expected_total, allowed_extra)

        expected_objs = getattr(assignment, "objects", None) or []
        doc_objs = list(document.iter_objects() or [])

        exp_obj_counts = Counter()
        for o in expected_objs:
            if isinstance(o, dict):
                t = (o.get("type") or "").lower()
            else:
                t = (getattr(o, "type", "") or "").lower()
            if t:
                exp_obj_counts[t] += 1

        doc_obj_counts = Counter()
        for o in doc_objs:
            t = (o.type or "").lower()
            if t:
                doc_obj_counts[t] += 1

        missing_objects = []
        too_many_objects = []

        for t, need in exp_obj_counts.items():
            have = doc_obj_counts.get(t, 0)
            if have < need:
                missing_objects.append(f"{t}: {have}/{need}")

        for t, have in doc_obj_counts.items():
            need = exp_obj_counts.get(t, 0)
            if need == 0:
                allowed = self._allowed_extra(
                    0, self.EXTRA_OBJECTS_ABS, self.EXTRA_OBJECTS_RATIO
                )
                if have > allowed:
                    too_many_objects.append(
                        f"{t}: {have} (zadání 0, povoleno max {allowed})"
                    )
                continue

            allowed = self._allowed_extra(
                need, self.EXTRA_OBJECTS_ABS, self.EXTRA_OBJECTS_RATIO
            )
            if have > need + allowed:
                too_many_objects.append(
                    f"{t}: {have} (zadání {need}, povoleno max {need + allowed})"
                )

        problems = []

        if missing_headings:
            problems.append(self.msg("missing_headings", "Chybí nadpisy ze zadání:"))
            problems += [f"- {x}" for x in missing_headings[:20]]
            if len(missing_headings) > 20:
                problems.append(
                    self.msg("more", "… a dalších {n}").format(
                        n=len(missing_headings) - 20
                    )
                )

        if wrong_level:
            problems.append(self.msg("wrong_heading_level", "Nesedí úroveň nadpisu:"))
            problems += [f"- {x}" for x in wrong_level[:20]]
            if len(wrong_level) > 20:
                problems.append(
                    self.msg("more", "… a dalších {n}").format(n=len(wrong_level) - 20)
                )

        if too_many_headings:
            doc_total, exp_total, allowed = too_many_headings
            problems.append(
                self.msg(
                    "too_many_headings",
                    "V dokumentu je výrazně více nadpisů než v zadání (v doc: {doc}, v zadání: {exp}, tolerance: +{tol}).",
                ).format(doc=doc_total, exp=exp_total, tol=allowed)
            )

        if missing_objects:
            problems.append(
                self.msg(
                    "missing_objects",
                    "Chybí objekty ze zadání (typ: v doc / v zadání):",
                )
            )
            problems += [f"- {x}" for x in missing_objects]

        if too_many_objects:
            problems.append(
                self.msg(
                    "too_many_objects",
                    "V dokumentu je výrazně více objektů než v zadání:",
                )
            )
            problems += [f"- {x}" for x in too_many_objects[:20]]
            if len(too_many_objects) > 20:
                problems.append(
                    self.msg("more", "… a dalších {n}").format(
                        n=len(too_many_objects) - 20
                    )
                )

        if not problems:
            return CheckResult(True, self.msg("ok", "Rozsah odpovídá zadání."), 0)

        return CheckResult(
            False,
            "\n".join(
                [self.msg("fail_header", "Rozsah neodpovídá zadání:")] + problems
            ),
            None,
        )
