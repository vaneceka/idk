from typing import Any

from checks.base_check import BaseCheck, CheckResult


class Runner:
    """
    Spouští sadu kontrol nad dokumentem a sbírá jejich výsledky.
    """

    def __init__(self, checks: list[BaseCheck]):
        self.checks = checks

    def run(
        self,
        document: Any,
        assignment: Any,
        context: Any = None,
    ) -> list[tuple[Any, CheckResult]]:
        """
        Spustí všechny kontroly nad dokumentem.

        Args:
            document: Kontrolovaný dokument.
            assignment: Zadání použitá při vyhodnocení.
            context: Volitelný doplňkový kontext pro kontroly.

        Returns:
            Seznam dvojic ve tvaru (check, result).
        """
        results: list[tuple[Any, CheckResult]] = []

        for check in self.checks:
            print(f"[CHECK START] {check.code}")
            try:
                result = check.run(document, assignment, context)
            except TypeError:
                try:
                    result = check.run(document, assignment)
                except Exception as e2:
                    print(f"[CHECK ERROR] {check.code}: {e2}")
                    result = CheckResult(False, f"Check {check.code} spadl: {e2}", None)
            except Exception as e:
                print(f"[CHECK ERROR] {check.code}: {e}")
                result = CheckResult(False, f"Check {check.code} spadl: {e}", None)

            print(f"[CHECK END] {check.code}")
            results.append((check, result))

        return results
