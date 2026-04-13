import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Union

from assignment.spreadsheet.spreadsheet_assignment_model import SpreadsheetAssignment
from assignment.text.text_assignment_model import TextAssignment
from checks.messages import MESSAGES


@dataclass
class CheckResult:
    """
    Uchovává výsledek jedné kontroly.

    Attributes:
        passed: Určuje, zda kontrola dopadla úspěšně.
        message: Textová zpráva s výsledkem kontroly.
        points: Bodová hodnota nebo sankce přiřazená výsledku kontroly.
        count: Počet nalezených výskytů nebo problémů.
    """

    passed: bool
    message: str
    points: int | None
    count: int = 1


Assignment = Union[TextAssignment, SpreadsheetAssignment]


class BaseCheck(ABC):
    """
    Základní abstraktní třída pro všechny kontroly.

    Attributes:
        YEAR_RE: Regulární výraz pro rozpoznání roku v textu.
        code: Jedinečný kód konkrétní kontroly.
    """

    YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
    code: str

    @abstractmethod
    def run(
        self,
        document: Any,
        assignment: Assignment | None = None,
        context: Any = None,
    ) -> CheckResult:
        """
        Spustí kontrolu nad dokumentem.

        Args:
            document: Kontrolovaný dokument.
            assignment: Volitelné zadání použité při vyhodnocení.
            context: Volitelný doplňkový kontext kontroly.

        Returns:
            Výsledek kontroly.
        """
        pass

    def msg(self, key: str, default: str = "") -> str:
        """
        Vrátí text zprávy pro daný klíč z registru zpráv kontroly.

        Args:
            key: Klíč požadované zprávy.
            default: Výchozí text použitý, pokud zpráva neexistuje.

        Returns:
            Text zprávy nebo výchozí hodnota.
        """
        if not self.code:
            return default
        return MESSAGES.get(self.code, {}).get(key, default)
