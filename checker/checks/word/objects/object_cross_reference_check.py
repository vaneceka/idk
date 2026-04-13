from checks.base_check import BaseCheck, CheckResult


class ObjectCrossReferenceCheck(BaseCheck):
    code = "T_V07"

    TYPE_LABEL = {
        "image": "Obrázek",
        "table": "Tabulka",
        "chart": "Graf",
    }

    def _is_object_bookmark(self, name: str) -> bool:
        low = name.lower()
        return (
            low.startswith("_ref")
            or "figure" in low
            or "obrázek" in low
            or "tabulka" in low
            or "graf" in low
        )

    def run(self, document, assignment=None):
        counters = {"image": 0, "table": 0, "chart": 0}
        errors = []

        used_refs = set(document.iter_object_crossref_ids())

        for obj in document.iter_objects():
            if obj.type not in ("image", "chart", "table"):
                continue

            counters[obj.type] += 1
            index = counters[obj.type]

            label = self.TYPE_LABEL.get(obj.type, obj.type)
            name = f"{label} {index}"

            caption_text = document.get_object_caption_text(obj)
            if caption_text:
                caption_text = caption_text.strip()
                if len(caption_text) > 60:
                    caption_text = caption_text[:57] + "…"
                name += f' ("{caption_text}")'

            caption_refs_all = document.get_object_caption_ref_ids(obj)
            caption_refs = [
                ref for ref in caption_refs_all if self._is_object_bookmark(ref)
            ]

            if not caption_refs or not any(ref in used_refs for ref in caption_refs):
                errors.append(
                    self.msg(
                        "missing_xref_item",
                        "{name} není v textu zmíněn křížovým odkazem.",
                    ).format(name=name)
                )

        if errors:
            return CheckResult(
                False,
                self.msg(
                    "errors_header",
                    "V textu není prostřednictvím křížového odkazu zmíněn vložený objekt:",
                )
                + "\n"
                + "\n".join(f"- {e}" for e in errors),
                None,
                len(errors),
            )

        return CheckResult(
            True,
            self.msg(
                "ok", "Všechny objekty jsou v textu zmíněny pomocí křížových odkazů."
            ),
            0,
        )
