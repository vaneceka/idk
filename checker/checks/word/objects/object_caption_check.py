from checks.base_check import BaseCheck, CheckResult


class ObjectCaptionCheck(BaseCheck):
    code = "T_V05"

    def _caption_text_matches_allowed(
        self, caption_text: str | None, allowed: set[str]
    ) -> bool:
        """
        Ověří, zda viditelný text titulku začíná povoleným návěštím.

        Args:
            caption_text: Viditelný text titulku.
            allowed: Množina povolených návěští.

        Returns:
            True, pokud text titulku začíná některým povoleným návěštím.
        """
        text = (caption_text or "").strip().lower()
        if not text:
            return False

        for label in allowed:
            if (
                text.startswith(label + " ")
                or text.startswith(label + "\u00a0")
                or text == label
            ):
                return True

        return False

    def run(self, document, assignment=None):
        if assignment is None:
            return CheckResult(
                True,
                self.msg("skip_no_assignment", "Chybí assignment - check přeskočen."),
                0,
            )
        
        errors = []
        penalized_errors = 0

        allowed_labels = {
            "image": {"obrázek", "figure"},
            "chart": {"graf", "chart"},
            "table": {"tabulka", "table"},
        }

        pretty = {"image": "Obrázek", "chart": "Graf", "table": "Tabulka"}
        counters = {"image": 0, "chart": 0, "table": 0}

        for obj in document.iter_objects():
            obj_type = obj.type
            if obj_type not in allowed_labels:
                continue

            counters[obj_type] += 1
            obj_index = counters[obj_type]

            obj_name = pretty[obj_type]
            info = document.get_object_caption_info(obj, accept_manual=True)

            if info is None:
                errors.append(
                    self.msg(
                        "no_caption",
                        "{obj} č. {i} nemá žádný titulek.",
                    ).format(obj=obj_name, i=obj_index)
                )
                continue

            if not info.is_seq:
                errors.append(
                    self.msg(
                        "manual_caption",
                        "{obj} č. {i} má titulek vytvořený ručně.",
                    ).format(obj=obj_name, i=obj_index)
                )
                penalized_errors += 1
                continue

            label_raw = info.label
            label = (label_raw or "").strip().lower()

            if label not in allowed_labels[obj_type]:
                if self._caption_text_matches_allowed(
                    info.text, allowed_labels[obj_type]
                ):
                    continue

                errors.append(
                    self.msg(
                        "wrong_label",
                        '{obj} č. {i} má špatný typ návěští ("{label}").',
                    ).format(obj=obj_name, i=obj_index, label=label_raw)
                )
                penalized_errors += 1

        if errors:
            return CheckResult(
                False,
                self.msg("errors_header", "Vložené objekty mají chybné titulky:")
                + "\n"
                + "\n".join(f"- {e}" for e in errors),
                None,
                penalized_errors,
            )

        return CheckResult(
            True,
            self.msg("ok", "Všechny objekty mají správné titulky."),
            0,
        )