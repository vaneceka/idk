import re
from collections import defaultdict

from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import remove_all_spaces


class NonCopyableFormulasCheck(BaseCheck):
    code = "S_D04"

    CELL_RE = re.compile(r"(\$?)([A-Z]{1,3})(\$?)(\d+)")
    RANGE_RE = re.compile(r"(\$?[A-Z]{1,3}\$?\d+):(\$?[A-Z]{1,3}\$?\d+)")

    def _normalize_formula(self, f: str | None) -> str:
        """
        Normalizuje vzorec do jednotného formátu pro porovnání.

        Args:
            f: Vzorec k úpravě.

        Returns:
            Upravený vzorec ve sjednocené podobě.
        """
        if not f:
            return ""
        f = f.strip()
        if f.startswith("of:="):
            f = "=" + f[4:]
        f = re.sub(r"\[\.(\w+\$?\d+)\]", r"\1", f)
        f = re.sub(r"\[\.(\w+):\.(\w+)\]", r"\1:\2", f)
        f = f.replace(";", ",")
        f = remove_all_spaces(f)
        return f.upper()

    def _col_to_num(self, col: str) -> int:
        """
        Převede označení sloupce na číslo.

        Args:
            col: Označení sloupce.

        Returns:
            Číselná hodnota sloupce.
        """
        n = 0
        for ch in col:
            n = n * 26 + (ord(ch) - 64)
        return n

    def _addr_to_rc(self, addr: str) -> tuple[int, int, bool, bool]:
        """
        Převede adresu buňky na řádek, sloupec a informaci o absolutním odkazu.

        Args:
            addr: Adresa buňky.

        Returns:
            Číslo řádku, číslo sloupce a příznaky absolutního řádku a sloupce.

        Raises:
            ValueError: Pokud adresa nemá platný formát.
        """
        m = self.CELL_RE.fullmatch(addr)
        if not m:
            raise ValueError(f"Bad addr: {addr}")
        col_abs = bool(m.group(1))
        col = self._col_to_num(m.group(2))
        row_abs = bool(m.group(3))
        row = int(m.group(4))
        return row, col, col_abs, row_abs

    def _r1c1_token(self, base_r: int, base_c: int, ref: str) -> str:
        """
        Převede odkaz buňky do formátu R1C1 vůči zadané základní buňce.

        Args:
            base_r: Výchozí řádek.
            base_c: Výchozí sloupec.
            ref: Odkaz na buňku.

        Returns:
            Odkaz ve formátu R1C1.
        """
        r, c, col_abs, row_abs = self._addr_to_rc(ref)
        r_part = f"R{r}" if row_abs else f"R[{r - base_r}]"
        c_part = f"C{c}" if col_abs else f"C[{c - base_c}]"
        return r_part + c_part

    def _formula_signature_r1c1(self, base_r: int, base_c: int, formula: str) -> str:
        """
        Převede odkazy ve vzorci do formátu R1C1 pro porovnání struktury vzorců.

        Args:
            base_r: Výchozí řádek.
            base_c: Výchozí sloupec.
            formula: Vzorec k úpravě.

        Returns:
            Vzorec s odkazy převedenými do formátu R1C1.
        """

        def repl_range(m):
            return (
                f"{self._r1c1_token(base_r, base_c, m.group(1))}:"
                f"{self._r1c1_token(base_r, base_c, m.group(2))}"
            )

        tmp = self.RANGE_RE.sub(repl_range, formula)

        def repl_cell(m):
            ref = (m.group(1) or "") + m.group(2) + (m.group(3) or "") + m.group(4)
            return self._r1c1_token(base_r, base_c, ref)

        return self.CELL_RE.sub(repl_cell, tmp)

    def _extract_ref_targets(self, formula: str):
        """
        Vytáhne ze vzorce odkazy na jednotlivé buňky.

        Args:
            formula: Vzorec ke zpracování.

        Returns:
            Seznam odkazů převedených na řádek, sloupec a absolutnost.
        """
        out = []
        formula_wo_ranges = self.RANGE_RE.sub("", formula)
        for m in self.CELL_RE.finditer(formula_wo_ranges):
            ref = (m.group(1) or "") + m.group(2) + (m.group(3) or "") + m.group(4)
            out.append(self._addr_to_rc(ref))
        return out

    def _split_into_vertical_blocks(self, items):
        """
        Rozdělí položky do souvislých vertikálních bloků podle řádků.

        Args:
            items: Seznam položek seřazených podle řádků.

        Returns:
            Seznam bloků s navazujícími řádky.
        """
        blocks = []
        current = [items[0]]

        for prev, cur in zip(items, items[1:]):
            if cur[0] == prev[0] + 1:
                current.append(cur)
            else:
                if len(current) >= 2:
                    blocks.append(current)
                current = [cur]

        if len(current) >= 2:
            blocks.append(current)

        return blocks

    def run(self, document, assignment=None):
        cells = document.cells_with_formulas()
        if not cells:
            return CheckResult(
                True, self.msg("no_formulas", "Žádné vzorce k ověření."), 0
            )

        parsed = []
        for cell in cells:
            f = self._normalize_formula(cell["formula"])
            if not f:
                continue

            m = re.fullmatch(r"([A-Z]{1,3})(\d+)", cell["address"])
            if not m:
                continue

            col = self._col_to_num(m.group(1))
            row = int(m.group(2))

            parsed.append((cell["sheet"], row, col, cell["address"], f))

        groups = defaultdict(list)
        for sheet, row, col, addr, f in parsed:
            groups[(sheet, col)].append((row, addr, f))

        problems = []

        for (sheet, col), items in groups.items():
            items.sort(key=lambda x: x[0])
            blocks = self._split_into_vertical_blocks(items)

            for block in blocks:
                base_row, base_addr, base_f = block[0]

                signatures = []
                targets = []

                ranges = set()
                for _, _, f in block:
                    for m in self.RANGE_RE.finditer(f):
                        ranges.add(m.group(0))

                if len(ranges) > 1:
                    continue

                for r, addr, f in block:
                    sig = self._formula_signature_r1c1(r, col, f)
                    signatures.append(sig)
                    targets.append(self._extract_ref_targets(f))

                if any(sig != signatures[0] for sig in signatures[1:]):
                    problems.append(
                        self.msg(
                            "diff_copy_pattern",
                            "{sheet}!{addr}: vzorec se liší od copy vzoru ve sloupci",
                        ).format(sheet=sheet, addr=block[1][1])
                    )
                    continue

                max_refs = max(len(t) for t in targets)
                for i in range(max_refs):
                    rows = []
                    row_abs = []

                    for t in targets:
                        if i >= len(t):
                            continue
                        r, c, ca, ra = t[i]
                        rows.append(r)
                        row_abs.append(ra)

                    if len(rows) >= 2 and len(set(rows)) == 1 and not all(row_abs):
                        problems.append(
                            self.msg(
                                "missing_row_dollar",
                                "{sheet}!{addr}: chybí $ na řádku u konstantního odkazu (např. ...${row})",
                            ).format(sheet=sheet, addr=base_addr, row=rows[0])
                        )
                        break

                if problems:
                    msg = (
                        self.msg("errors_header", "Vzorce nelze bezpečně kopírovat:")
                        + "\n"
                        + "\n".join(f"- {p}" for p in problems)
                    )
                    return CheckResult(False, msg, None)

        return CheckResult(True, self.msg("ok", "Vzorce jsou kopírovatelné."), 0)
