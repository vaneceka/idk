from __future__ import annotations

import json
from pathlib import Path

from checks import checks_all
from checks.checks_meta_registry import CHECKS


def build_section(codes: list[str]) -> list[dict]:
    out = []
    order = 1
    for code in codes:
        meta = CHECKS.get(code)
        title = meta.title if meta else ""
        out.append(
            {
                "code": code,
                "title": title,
                "default_enabled": True,
                "order": order,
            }
        )
        order += 1
    return out


def main():
    data = {
        "text": build_section(checks_all.default_word_codes()),
        "spreadsheet": build_section(checks_all.default_excel_codes()),
    }

    out_path = Path(__file__).resolve().parents[1] / "checks" / "checks_config" / "checks_registry.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
