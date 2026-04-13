import difflib
import re
from pathlib import Path

from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import replace_nbsp


class Section2TextCheck(BaseCheck):
    code = "T_C07"

    MIN_WORDS = 400
    SNIP = 180

    def _normalize(self, s: str) -> str:
        """
        Normalizuje text odstraněním nadbytečných mezer a sjednocením konců řádků.

        Args:
            s: Vstupní text.

        Returns:
            Upravený text ve sjednocené podobě.
        """
        if not s:
            return ""
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        s = replace_nbsp(s)
        s = re.sub(r"[ \t]+", " ", s)
        s = re.sub(r"\n+", "\n", s)
        return s.strip()

    def _snip(self, s: str) -> str:
        """
        Vrátí zkrácenou ukázku textu.

        Args:
            s: Vstupní text.

        Returns:
            Text zkrácený na maximální délku.
        """
        s = (s or "").strip()
        if len(s) <= self.SNIP:
            return s
        return s[: self.SNIP].rstrip() + "…"

    def _split_blocks(self, s: str) -> list[str]:
        """
        Rozdělí text na neprázdné bloky po jednotlivých řádcích.

        Args:
            s: Vstupní text.

        Returns:
            Seznam textových bloků.
        """
        s = self._normalize(s)
        if not s:
            return []
        blocks: list[str] = []
        for line in s.split("\n"):
            line = line.strip()
            if line:
                blocks.append(line)
        return blocks

    def _find_original_text_file(
        self, assignment_dir: Path, submitted_path: Path, document
    ) -> Path | None:
        """
        Najde původní textový soubor zadání pro porovnání se studentským souborem.

        Args:
            assignment_dir: Složka se zadáním.
            submitted_path: Cesta k odevzdanému souboru.
            document: Otevřený dokument použitý pro načítání kandidátů.

        Returns:
            Cestu k nejvhodnějšímu původnímu souboru, nebo None.
        """
        same_name = assignment_dir / submitted_path.name
        if same_name.is_file():
            return same_name

        preferred = submitted_path.suffix.lower()
        exts = [preferred] if preferred in (".docx", ".odt") else []
        exts += [".docx", ".odt"]

        cands: list[Path] = []
        for ext in exts:
            for p in assignment_dir.iterdir():
                if p.is_file() and p.suffix.lower() == ext:
                    cands.append(p)

        if not cands:
            return None

        best: Path | None = None
        best_len = -1

        for p in cands:
            try:
                d = type(document).from_path(str(p))
                txt = d.get_full_text()
                text_len = len(txt or "")
                if text_len > best_len:
                    best_len, best = text_len, p
            except Exception:
                continue

        return best

    def _compact_block_diff(
        self, orig_blocks: list[str], stud_blocks: list[str]
    ) -> str:
        """
        Vrátí stručný popis prvního rozdílu mezi bloky původního a studentského textu.

        Args:
            orig_blocks: Bloky původního textu.
            stud_blocks: Bloky studentského textu.

        Returns:
            Textový popis prvního nalezeného rozdílu, nebo informaci o shodě.
        """
        sm = difflib.SequenceMatcher(a=orig_blocks, b=stud_blocks)

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue

            pos_orig = i1 + 1
            pos_stud = j1 + 1

            if tag in ("delete", "replace"):
                if i1 < len(orig_blocks):
                    line = orig_blocks[i1]
                    return self.msg(
                        "diff_missing_block",
                        "CHYBÍ blok (orig #{n}): {text}",
                    ).format(
                        n=pos_orig,
                        text=self._snip(line),
                    )

            if tag in ("insert", "replace"):
                if j1 < len(stud_blocks):
                    line = stud_blocks[j1]
                    return self.msg(
                        "diff_extra_block",
                        "NAVÍC blok (stud #{n}): {text}",
                    ).format(
                        n=pos_stud,
                        text=self._snip(line),
                    )

            return self.msg("diff_equal", "Texty jsou shodné.")

        return self.msg("diff_equal", "Texty jsou shodné.")

    def run(self, document, assignment=None, context=None):
        if not document.has_text_in_section(1, self.MIN_WORDS):
            return CheckResult(
                False,
                self.msg("missing_text", "Ve druhém oddílu chybí text dokumentu."),
                None,
            )

        assignment_dir = None
        submitted_path = None
        if isinstance(context, dict):
            assignment_dir = context.get("assignment_dir")
            submitted_path = context.get("submitted_path")

        if not assignment_dir or not submitted_path:
            return CheckResult(
                True,
                self.msg(
                    "ok_no_context",
                    "Text ve 2. oddílu OK (chybí context pro porovnání).",
                ),
                0,
            )

        assignment_dir = Path(assignment_dir)
        submitted_path = Path(submitted_path)

        original_path = self._find_original_text_file(
            assignment_dir, submitted_path, document
        )
        if not original_path:
            return CheckResult(
                True,
                self.msg(
                    "ok_no_original",
                    "Text ve 2. oddílu OK (originál pro porovnání nenalezen).",
                ),
                0,
            )

        try:
            original_doc = type(document).from_path(str(original_path))
        except Exception as e:
            return CheckResult(
                True,
                self.msg(
                    "ok_original_open_failed",
                    "Text ve 2. oddílu OK (originál nelze otevřít: {err}).",
                ).format(err=str(e)),
                0,
            )

        student_raw = document.get_text_of_section(1)

        if original_doc.section_count() >= 2:
            orig_raw = original_doc.get_text_of_section(1)
        else:
            orig_raw = original_doc.get_full_text()

        orig_blocks = self._split_blocks(orig_raw)
        stud_blocks = self._split_blocks(student_raw)

        if orig_blocks != stud_blocks:
            msg = self.msg(
                "different_text",
                "Text ve 2. oddílu neodpovídá původnímu zadání (liší se).",
            )
            msg += "\n" + self._compact_block_diff(orig_blocks, stud_blocks)
            return CheckResult(False, msg, None)

        return CheckResult(True, self.msg("ok", "Text ve 2. oddílu OK"), 0)
