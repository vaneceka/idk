import json
from dataclasses import asdict, is_dataclass
from typing import Any

from checks.base_check import CheckResult
from checks.checks_meta_registry import get_check_meta
from models.core_models import ReportEntry


class Report:
    """
    Uchovává výsledky kontrol a umí je převést do textové i JSON podoby.
    """

    def __init__(self, include_passed: bool = False) -> None:
        self.include_passed = include_passed
        self.entries: list[ReportEntry] = []

    def _finalize_points(self, code: str, result: CheckResult) -> CheckResult:
        """
        Doplní bodovou sankci výsledku podle metadat kontroly.

        Args:
            code: Kód kontroly.
            result: Výsledek kontroly.

        Returns:
            Upravený výsledek s doplněnými body.
        """
        if getattr(result, "passed", False) and getattr(result, "points", None) is None:
            result.points = 0
            return result

        if (not getattr(result, "passed", False)) and getattr(
            result, "points", None
        ) is None:
            meta = get_check_meta(code)
            if meta is None or meta.penalty is None:
                result.points = -100
                return result

            count = getattr(result, "count", 1)
            if not isinstance(count, int):
                count = 1

            result.points = (
                meta.penalty * count if meta.per_occurrence else meta.penalty
            )

        return result

    def add(self, code: str, result: CheckResult) -> None:
        """
        Přidá výsledek kontroly do reportu.

        Args:
            code: Kód kontroly.
            result: Výsledek kontroly.
        """
        result = self._finalize_points(code, result)

        passed = bool(getattr(result, "passed", False))
        if passed and not self.include_passed:
            return

        self.entries.append(ReportEntry(code=code, result=result))

    def _result_to_dict(self, result: Any) -> dict[str, Any]:
        """
        Převede výsledek kontroly na slovník.

        Args:
            result: Výsledek kontroly v libovolné podporované podobě.

        Returns:
            Slovník se základními údaji o výsledku.
        """
        if isinstance(result, dict):
            return dict(result)

        if is_dataclass(result) and not isinstance(result, type):
            return asdict(result)

        pts = getattr(result, "points", 0)
        pts_out = None if pts is None else int(pts)

        return {
            "passed": bool(getattr(result, "passed", False)),
            "message": str(getattr(result, "message", "")),
            "points": pts_out,
        }

    def _compute_total_penalty(self) -> int:
        """
        Spočítá celkovou bodovou sankci reportu.

        Returns:
            Celkovou sankci jako záporné číslo omezené maximální hodnotou.
        """
        total = 0
        for item in self.entries:
            r = self._result_to_dict(item.result)
            pts = r.get("points", 0)

            if not r.get("passed", False):
                if pts is None:
                    pts = 0
                total += abs(int(pts))

        return -int(total) 

    def _label(self, code: str) -> str:
        """
        Vrátí textový popisek kontroly.

        Args:
            code: Kód kontroly.

        Returns:
            Popisek ve tvaru kód nebo kód s názvem kontroly.
        """
        meta = get_check_meta(code)
        return code if not meta else f"{code} - {meta.title}"

    def print(self) -> None:
        """
        Vypíše report do standardního výstupu.
        """
        total = self._compute_total_penalty()
        print("\n=== VÝSLEDKY HODNOCENÍ ===\n")

        for i, item in enumerate(self.entries, start=1):
            code = item.code
            result = item.result
            status = "OK" if getattr(result, "passed", False) else "CHYBA"
            print(f"{i}. {status}: {self._label(code)}")
            print(f"  {getattr(result, 'message', '')}")
            print(f"  Body: {getattr(result, 'points', 0)}\n")

        print(f"CELKOVÁ BODOVÁ SANKCE: {total}")

    def to_text(self) -> str:
        """
        Převede report do textové podoby.

        Returns:
            Textová reprezentace reportu.
        """
        total = self._compute_total_penalty()
        lines = ["=== VÝSLEDKY HODNOCENÍ ===\n"]

        for i, item in enumerate(self.entries, start=1):
            code = item.code
            result = item.result
            status = "OK" if getattr(result, "passed", False) else "CHYBA"
            lines.append(f"{i}. {status}: {self._label(code)}")
            lines.append(f"  {getattr(result, 'message', '')}")
            lines.append(f"  Body: {getattr(result, 'points', 0)}")
            lines.append("")

        lines.append(f"CELKOVÁ BODOVÁ SANKCE: {total}")
        return "\n".join(lines)

    def save_txt(self, path) -> None:
        """
        Uloží report do textového souboru.

        Args:
            path: Cesta k výstupnímu souboru.
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_text())

    def to_dict(self) -> dict[str, Any]:
        """
        Převede report do slovníkové podoby.

        Returns:
            Slovník obsahující celkovou sankci a jednotlivé položky reportu.
        """
        entries = []
        for item in self.entries:
            code = item.code
            r = self._result_to_dict(item.result)
            meta = get_check_meta(code)

            entries.append(
                {
                    "code": code,
                    "name": meta.title if meta else None,
                    "category": meta.category if meta else None,
                    "passed": bool(r.get("passed", False)),
                    "message": r.get("message", ""),
                    "points": r.get("points", 0) or 0,
                }
            )

        return {
            "total_penalty": self._compute_total_penalty(),
            "entries": entries,
        }

    def to_json(self, pretty: bool = True) -> str:
        """
        Převede report do JSON řetězce.

        Args:
            pretty: Určuje, zda má být JSON formátovaný pro lepší čitelnost.

        Returns:
            JSON reprezentace reportu.
        """
        return json.dumps(
            self.to_dict(), ensure_ascii=False, indent=2 if pretty else None
        )

    def save_json(self, path, pretty: bool = True) -> None:
        """
        Uloží report do JSON souboru.

        Args:
            path: Cesta k výstupnímu souboru.
            pretty: Určuje, zda má být JSON formátovaný pro lepší čitelnost.
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json(pretty=pretty))
