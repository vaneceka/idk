import re

from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import remove_all_spaces, replace_nbsp


class MissingOrWrongFormulaOrNotCalculatedCheck(BaseCheck):
    code = "S_D05"

    CELL_RE = re.compile(r"\$?([A-Z]{1,3})\$?(\d+)")
    RANGE_RE = re.compile(r"(\$?[A-Z]{1,3}\$?\d+):(\$?[A-Z]{1,3}\$?\d+)")
    COMPARE_RE = re.compile(
        r"^\s*(.+?)\s*(>=|<=|<>|!=|=|>|<)\s*(.+?)\s*$", re.IGNORECASE
    )
    IF_RE = re.compile(r"^\s*=?IF\((.+),(.+),(.+)\)\s*$", re.IGNORECASE)
    REF_TOKEN_RE = re.compile(r"\$?[A-Z]{1,3}\$?\d+")

    def _col_to_num(self, col: str) -> int:
        """
        Převede označení sloupce na jeho číselnou hodnotu.

        Args:
            col: Označení sloupce, například A nebo AB.

        Returns:
            Číselná hodnota sloupce.
        """
        n = 0
        for ch in col.upper():
            n = n * 26 + (ord(ch) - 64)
        return n

    def _num_to_col(self, n: int) -> str:
        """
        Převede číslo sloupce na jeho písmenné označení.

        Args:
            n: Číselná hodnota sloupce.

        Returns:
            Označení sloupce, například A nebo AB.
        """
        out = ""
        while n > 0:
            n, r = divmod(n - 1, 26)
            out = chr(65 + r) + out
        return out

    def _expand_range(self, a: str, b: str) -> list[str]:
        """
        Rozbalí rozsah buněk na seznam jednotlivých adres.

        Args:
            a: Počáteční adresa rozsahu.
            b: Koncová adresa rozsahu.

        Returns:
            Seznam adres buněk v rozsahu.
        """
        ma = self.CELL_RE.fullmatch(a)
        mb = self.CELL_RE.fullmatch(b)
        if not ma or not mb:
            return []

        c1 = self._col_to_num(ma.group(1))
        r1 = int(ma.group(2))
        c2 = self._col_to_num(mb.group(1))
        r2 = int(mb.group(2))

        c_from, c_to = sorted((c1, c2))
        r_from, r_to = sorted((r1, r2))

        cells = []
        for r in range(r_from, r_to + 1):
            for c in range(c_from, c_to + 1):
                cells.append(f"{self._num_to_col(c)}{r}")
        return cells

    def _normalize_lo_refs(self, f: str) -> str:
        """
        Převede odkazy LibreOffice do sjednoceného formátu.

        Args:
            f: Vzorec nebo výraz s odkazy.

        Returns:
            Výraz s normalizovanými odkazy.
        """
        f = re.sub(r"\[\.(\$?[A-Z]{1,3}\$?\d+)\]", r"\1", f)
        f = re.sub(r"\[\.(\$?[A-Z]{1,3}\$?\d+):\.(\$?[A-Z]{1,3}\$?\d+)\]", r"\1:\2", f)
        return f

    def _to_number(self, v):
        """
        Převede hodnotu na číslo, pokud je to možné.

        Args:
            v: Vstupní hodnota.

        Returns:
            Hodnotu typu float, nebo None pokud převod není možný.
        """
        if v is None:
            return None
        if isinstance(v, bool):
            return 1.0 if v else 0.0
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            s = remove_all_spaces(replace_nbsp(v.strip()))
            s = s.replace(",", ".")
            try:
                return float(s)
            except Exception:
                return None
        return None

    def _normalize_operand(self, s: str) -> str:
        """
        Normalizuje operand pro porovnání výrazů.

        Args:
            s: Operand k úpravě.

        Returns:
            Normalizovaný operand.
        """
        s = (s or "").strip()
        s = self._normalize_lo_refs(s)
        s = s.replace(";", ",")
        s = remove_all_spaces(s)
        return s.upper()

    def _normalize_text_literal(self, s: str) -> str:
        """
        Normalizuje textový literál pro porovnání.

        Args:
            s: Textový literál.

        Returns:
            Normalizovaný text bez uvozovek a nadbytečných mezer.
        """
        s = (s or "").strip()
        if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
            s = s[1:-1]
        return s.strip().lower()

    def _flip_op(self, op: str) -> str | None:
        """
        Vrátí opačný směr porovnávacího operátoru.

        Args:
            op: Porovnávací operátor.

        Returns:
            Ekvivalentní operátor pro prohozené strany, nebo None.
        """
        return {
            ">": "<",
            "<": ">",
            ">=": "<=",
            "<=": ">=",
            "=": "=",
            "==": "==",
            "<>": "<>",
            "!=": "!=",
        }.get(op)

    def _same_comparison_expr(self, actual_expr: str, expected_expr: str) -> bool:
        """
        Ověří, zda jsou dva porovnávací výrazy ekvivalentní.

        Args:
            actual_expr: Skutečný výraz.
            expected_expr: Očekávaný výraz.

        Returns:
            True pokud jsou výrazy ekvivalentní, jinak False.
        """
        ma = self.COMPARE_RE.match(actual_expr)
        me = self.COMPARE_RE.match(expected_expr)

        if not ma or not me:
            return False

        a_left, a_op, a_right = ma.groups()
        e_left, e_op, e_right = me.groups()

        a_left = self._normalize_operand(a_left)
        a_right = self._normalize_operand(a_right)
        e_left = self._normalize_operand(e_left)
        e_right = self._normalize_operand(e_right)

        if a_left == e_left and a_op == e_op and a_right == e_right:
            return True

        flipped = self._flip_op(e_op)
        if flipped is None:
            return False

        return a_left == e_right and a_op == flipped and a_right == e_left

    def _negate_op(self, op: str) -> str | None:
        """
        Vrátí negaci porovnávacího operátoru.

        Args:
            op: Porovnávací operátor.

        Returns:
            Negovaný operátor, nebo None.
        """
        return {
            ">": "<=",
            "<": ">=",
            ">=": "<",
            "<=": ">",
            "=": "<>",
            "==": "!=",
            "<>": "=",
            "!=": "==",
        }.get(op)

    def _same_negated_comparison_expr(
        self, actual_expr: str, expected_expr: str
    ) -> bool:
        """
        Ověří, zda skutečný výraz odpovídá negaci očekávaného výrazu.

        Args:
            actual_expr: Skutečný výraz.
            expected_expr: Očekávaný výraz.

        Returns:
            True pokud je skutečný výraz negací očekávaného, jinak False.
        """
        ma = self.COMPARE_RE.match(actual_expr)
        me = self.COMPARE_RE.match(expected_expr)

        if not ma or not me:
            return False

        a_left, a_op, a_right = ma.groups()
        e_left, e_op, e_right = me.groups()

        a_left = self._normalize_operand(a_left)
        a_right = self._normalize_operand(a_right)
        e_left = self._normalize_operand(e_left)
        e_right = self._normalize_operand(e_right)

        neg = self._negate_op(e_op)
        if neg is not None and a_left == e_left and a_right == e_right and a_op == neg:
            return True

        flipped = self._flip_op(e_op)
        if flipped is None:
            return False

        neg_flipped = self._negate_op(flipped)
        if neg_flipped is None:
            return False

        return a_left == e_right and a_right == e_left and a_op == neg_flipped

    def _same_if_formula(self, actual: str, expected: str) -> bool:
        """
        Ověří, zda jsou dva IF vzorce logicky ekvivalentní.

        Args:
            actual: Skutečný vzorec.
            expected: Očekávaný vzorec.

        Returns:
            True pokud jsou vzorce ekvivalentní, jinak False.
        """
        a = actual.strip().replace(";", ",")
        e = expected.strip().replace(";", ",")

        ma = self.IF_RE.match(a)
        me = self.IF_RE.match(e)

        if not ma or not me:
            return False

        a_cond, a_true, a_false = ma.groups()
        e_cond, e_true, e_false = me.groups()

        a_true_n = self._normalize_text_literal(a_true)
        a_false_n = self._normalize_text_literal(a_false)
        e_true_n = self._normalize_text_literal(e_true)
        e_false_n = self._normalize_text_literal(e_false)

        if a_true_n == e_true_n and a_false_n == e_false_n:
            if self._same_comparison_expr(a_cond, e_cond):
                return True

        if a_true_n == e_false_n and a_false_n == e_true_n:
            if self._same_negated_comparison_expr(a_cond, e_cond):
                return True

        return False

    def _values_equal(self, a, b) -> bool:
        """
        Porovná dvě hodnoty s ohledem na číselný převod.

        Args:
            a: První hodnota.
            b: Druhá hodnota.

        Returns:
            True pokud jsou hodnoty považovány za stejné, jinak False.
        """
        na = self._to_number(a)
        nb = self._to_number(b)

        if na is not None and nb is not None:
            return na == nb

        if isinstance(a, str) and isinstance(b, str):
            return a.strip().lower() == b.strip().lower()

        return a == b

    def _flatten_numbers(self, args) -> list[float]:
        """
        Z argumentů rekurzivně vybere všechny číselné hodnoty.

        Args:
            args: Hodnoty nebo vnořené seznamy hodnot.

        Returns:
            Seznam čísel převedených na float.
        """
        out = []
        for a in args:
            if isinstance(a, (list, tuple)):
                out.extend(self._flatten_numbers(a))
                continue
            n = self._to_number(a)
            if n is not None:
                out.append(n)
        return out

    def _min_func(self, *args):
        """
        Vrátí minimum z číselných argumentů.

        Args:
            *args: Hodnoty nebo seznamy hodnot.

        Returns:
            Nejmenší číslo, nebo None pokud nejsou k dispozici žádná čísla.
        """
        vals = self._flatten_numbers(args)
        return min(vals) if vals else None

    def _max_func(self, *args):
        """
        Vrátí maximum z číselných argumentů.

        Args:
            *args: Hodnoty nebo seznamy hodnot.

        Returns:
            Největší číslo, nebo None pokud nejsou k dispozici žádná čísla.
        """
        vals = self._flatten_numbers(args)
        return max(vals) if vals else None

    def _average_func(self, *args):
        """
        Vrátí průměr z číselných argumentů.

        Args:
            *args: Hodnoty nebo seznamy hodnot.

        Returns:
            Aritmetický průměr, nebo None pokud nejsou k dispozici žádná čísla.
        """
        vals = self._flatten_numbers(args)
        return (sum(vals) / len(vals)) if vals else None

    def _median_func(self, *args):
        """
        Vrátí medián z číselných argumentů.

        Args:
            *args: Hodnoty nebo seznamy hodnot.

        Returns:
            Medián, nebo None pokud nejsou k dispozici žádná čísla.
        """
        vals = sorted(self._flatten_numbers(args))
        if not vals:
            return None
        mid = len(vals) // 2
        return vals[mid] if len(vals) % 2 == 1 else (vals[mid - 1] + vals[mid]) / 2

    def _if_func(self, cond, a, b):
        """
        Vrátí jednu ze dvou hodnot podle podmínky.

        Args:
            cond: Vyhodnocená podmínka.
            a: Hodnota pro pravdivou podmínku.
            b: Hodnota pro nepravdivou podmínku.

        Returns:
            Hodnotu a nebo b podle výsledku podmínky.
        """
        return a if bool(cond) else b

    def _power_func(self, a, b):
        """
        Umocní první hodnotu na druhou.

        Args:
            a: Základ mocniny.
            b: Exponent.

        Returns:
            Výsledek mocnění, nebo None pokud některá hodnota není číslo.
        """
        na = self._to_number(a)
        nb = self._to_number(b)
        if na is None or nb is None:
            return None
        return na**nb

    def _abs_func(self, a):
        """
        Vrátí absolutní hodnotu čísla.

        Args:
            a: Vstupní hodnota.

        Returns:
            Absolutní hodnota, nebo None pokud vstup není číslo.
        """
        na = self._to_number(a)
        return abs(na) if na is not None else None

    def _replace_range_refs(self, formula: str, document, sheet: str) -> str:
        """
        Nahradí odkazy na rozsahy jejich aktuálními hodnotami.

        Args:
            formula: Vzorec k úpravě.
            document: Dokument tabulky.
            sheet: Název listu.

        Returns:
            Vzorec s nahrazenými odkazy na rozsahy.
        """

        def repl_range(m):
            a = m.group(1)
            b = m.group(2)
            cells = self._expand_range(a, b)

            vals = []
            for addr in cells:
                v = document.get_cell_value(sheet, addr)
                n = self._to_number(v)
                vals.append(n if n is not None else v)

            return "(" + ",".join(repr(v) for v in vals) + ")"

        return self.RANGE_RE.sub(repl_range, formula)

    def _replace_cell_refs(self, formula: str, document, sheet: str) -> str:
        """
        Nahradí odkazy na buňky jejich aktuálními hodnotami.

        Args:
            formula: Vzorec k úpravě.
            document: Dokument tabulky.
            sheet: Název listu.

        Returns:
            Vzorec s nahrazenými odkazy na buňky.
        """

        def repl_cell(m):
            col = m.group(1)
            row = m.group(2)
            addr = f"{col}{row}"

            v = document.get_cell_value(sheet, addr)
            n = self._to_number(v)
            return repr(n if n is not None else v)

        return self.CELL_RE.sub(repl_cell, formula)

    def _eval_formula(self, document, sheet: str, formula: str):
        """
        Zkusí vyhodnotit jednoduchý tabulkový vzorec.

        Args:
            document: Dokument tabulky.
            sheet: Název listu.
            formula: Vzorec k vyhodnocení.

        Returns:
            Vyhodnocenou hodnotu, nebo None pokud se vzorec nepodaří zpracovat.
        """
        if not formula:
            return None

        f = formula.strip()
        f = self._normalize_lo_refs(f)
        if f.startswith("of:="):
            f = "=" + f[4:]
        if f.startswith("="):
            f = f[1:]

        f = f.replace(";", ",")
        f = f.replace("^", "**")
        f = f.replace("<>", "!=")
        f = re.sub(r"(?<![<>=!])=(?![<>=])", "==", f)

        f = self._replace_range_refs(f, document, sheet)
        f = self._replace_cell_refs(f, document, sheet)

        env = {
            "MIN": self._min_func,
            "MAX": self._max_func,
            "AVERAGE": self._average_func,
            "MEDIAN": self._median_func,
            "IF": self._if_func,
            "POWER": self._power_func,
            "POW": self._power_func,
            "ABS": self._abs_func,
            "TRUE": True,
            "FALSE": False,
        }

        try:
            return eval(f, {"__builtins__": {}}, env)
        except Exception:
            return None

    def _extract_ref_tokens(self, f: str | None) -> list[str]:
        """
        Vytáhne z výrazu odkazy na buňky.

        Args:
            f: Vzorec nebo výraz.

        Returns:
            Seznam nalezených odkazů na buňky.
        """
        if not f:
            return []
        f = self._normalize_lo_refs(f)
        f = f.strip().upper()
        if f.startswith("OF:="):
            f = "=" + f[4:]
        return self.REF_TOKEN_RE.findall(f)

    def _same_ref_tokens(self, actual: str, expected: str) -> bool:
        """
        Ověří, zda dva výrazy obsahují stejné odkazy na buňky.

        Args:
            actual: Skutečný výraz.
            expected: Očekávaný výraz.

        Returns:
            True pokud obsahují stejné reference ve stejném pořadí, jinak False.
        """
        return self._extract_ref_tokens(actual) == self._extract_ref_tokens(expected)

    def run(self, document, assignment=None):
        if assignment is None or not hasattr(assignment, "cells"):
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."),
                0,
            )

        sheet = "data"

        if sheet not in document.sheet_names():
            return CheckResult(
                False,
                self.msg(
                    "missing_sheet", 'List "{sheet}" chybí - nelze ověřit vzorce.'
                ).format(sheet=sheet),
                None,
            )

        errors = []

        for addr, spec in assignment.cells.items():
            expected = getattr(spec, "expression", None)
            if not expected:
                continue

            info = document.get_cell_info(sheet, addr)
            if info is None:
                errors.append(
                    self.msg("cell_missing", "{sheet}!{addr}: buňka neexistuje").format(
                        sheet=sheet, addr=addr
                    )
                )
                continue

            actual = info.get("formula")
            if not actual or not isinstance(actual, str) or not actual.startswith("="):
                errors.append(
                    self.msg("formula_missing", "{sheet}!{addr}: chybí vzorec").format(
                        sheet=sheet, addr=addr
                    )
                )
                continue

            if info.get("is_error"):
                errors.append(
                    self.msg(
                        "result_error", "{sheet}!{addr}: výsledek je chyba"
                    ).format(sheet=sheet, addr=addr)
                )
                continue

            act = document.normalize_formula(self._normalize_lo_refs(actual))
            exp = document.normalize_formula(self._normalize_lo_refs(expected))

            if act != exp:
                if self._same_if_formula(actual, expected):
                    continue

                act_expr = actual.strip()
                exp_expr = expected.strip()

                if act_expr.startswith("="):
                    act_expr = act_expr[1:]
                if exp_expr.startswith("="):
                    exp_expr = exp_expr[1:]

                if self._same_comparison_expr(act_expr, exp_expr):
                    continue

                if self._same_ref_tokens(actual, expected):
                    actual_val = self._eval_formula(document, sheet, actual)
                    expected_val = self._eval_formula(document, sheet, expected)

                    if self._values_equal(actual_val, expected_val):
                        continue

                errors.append(
                    self.msg(
                        "formula_wrong",
                        "{sheet}!{addr}: špatný vzorec (oček. {expected}, nalezeno {actual})",
                    ).format(sheet=sheet, addr=addr, expected=exp, actual=actual)
                )

        if errors:
            header = self.msg("errors_header", "Problémy se vzorci / výpočtem:")
            return CheckResult(
                False, header + "\n" + "\n".join("- " + e for e in errors), None
            )

        return CheckResult(
            True,
            self.msg(
                "ok", "Všechny požadované vzorce existují a mají uložený výsledek."
            ),
            0,
        )
