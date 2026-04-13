from collections import defaultdict
import re

WHITESPACE_RE = re.compile(r"\s+")
NBSP = "\u00a0"


def normalize_spaces(text: str | None) -> str:
    """
    Nahradí vícenásobné bílé znaky jednou mezerou a ořízne okraje textu.

    Args:
        text: Vstupní text.

    Returns:
        Text s normalizovanými mezerami.
    """
    return WHITESPACE_RE.sub(" ", text or "").strip()


def remove_all_spaces(text: str | None) -> str:
    """
    Odstraní z textu všechny bílé znaky.

    Args:
        text: Vstupní text.

    Returns:
        Text bez bílých znaků.
    """
    return WHITESPACE_RE.sub("", text or "")


def replace_nbsp(text: str | None) -> str:
    """
    Nahradí pevné mezery běžnými mezerami.

    Args:
        text: Vstupní text.

    Returns:
        Text s nahrazenými pevnými mezerami.
    """
    return (text or "").replace(NBSP, " ")

def group_inline_formatting_by_text(errors: list[dict]) -> list[dict]:
    """
    Seskupí nalezené problémy podle textu.

    Args:
        errors: Seznam nalezených problémů.

    Returns:
        Seznam slovníků se skupinami podle textu.
    """
    grouped: dict[str, set[str]] = defaultdict(set)

    for item in errors:
        text = (item.get("text") or "").strip()
        problem = (item.get("problem") or "").strip()

        if not text or not problem:
            continue

        grouped[text].add(problem)

    result = []
    for text, problems in grouped.items():
        result.append(
            {
                "text": text,
                "problems": sorted(problems),
                "count": len(problems),
            }
        )

    return result
