from checks.base_check import BaseCheck, CheckResult


class ObjectCaptionBindingCheck(BaseCheck):
    code = "T_V08"

    def run(self, document, assignment=None):
        errors = []
        notes = []

        expected_labels = {
            "image": {"obrázek", "figure"},
            "chart": {"graf", "chart"},
            "table": {"tabulka", "table"},
        }

        pretty_map = {"image": "Obrázek", "chart": "Graf", "table": "Tabulka"}
        counters = {"image": 0, "chart": 0, "table": 0}

        for obj in document.iter_objects():
            obj_type = obj.type
            labels = expected_labels.get(obj_type)
            if not labels:
                continue

            counters[obj_type] += 1
            obj_index = counters[obj_type]

            pretty = pretty_map.get(obj_type, obj_type)
            info = document.get_object_caption_info(obj, accept_manual=True)

            if info is None:
                notes.append(
                    self.msg(
                        "missing_caption_note",
                        "{pretty} č. {i}: nepodařilo se dohledat titulek, vazba se nekontrolovala.",
                    ).format(pretty=pretty, i=obj_index)
                )
                continue

            is_bound = document.object_has_caption(obj, labels)

            if info.is_manual:
                if not is_bound:
                    errors.append(
                        self.msg(
                            "item",
                            "{pretty} č. {i} není s titulkem spojen.",
                        ).format(pretty=pretty, i=obj_index)
                    )
                else:
                    notes.append(
                        self.msg(
                            "manual_caption_note",
                            "{pretty} č. {i}: titulek je vytvořený ručně, ale je s objektem spojen.",
                        ).format(pretty=pretty, i=obj_index)
                    )
                continue

            if not is_bound:
                errors.append(
                    self.msg(
                        "item",
                        "{pretty} č. {i} není s titulkem spojen.",
                    ).format(pretty=pretty, i=obj_index)
                )

        if errors:
            msg = (
                self.msg(
                    "errors_header",
                    "Některé objekty nejsou s titulky správně spojeny:",
                )
                + "\n"
                + "\n".join(f"- {e}" for e in errors)
            )

            if notes:
                msg += (
                    "\n"
                    + self.msg("notes_header", "Informativně:")
                    + "\n"
                    + "\n".join(f"- {n}" for n in notes[:10])
                )

            return CheckResult(False, msg, None, len(errors))

        if notes:
            return CheckResult(
                True,
                self.msg(
                    "ok",
                    "Všechny nalezené objekty jsou správně spojeny s titulky.",
                )
                + "\n"
                + self.msg("notes_header", "Informativně:")
                + "\n"
                + "\n".join(f"- {n}" for n in notes[:10]),
                0,
            )

        return CheckResult(
            True,
            self.msg("ok", "Všechny objekty jsou správně spojeny s titulky."),
            0,
        )