from checks.base_check import BaseCheck, CheckResult
from utils.text_utils import normalize_spaces


class ObjectCaptionDescriptionCheck(BaseCheck):
    code = "T_V06"

    SUPPORTED_TYPES = {"image", "table", "chart"}

    def _norm(self, text: str) -> str:
        """
        Normalizuje text pro porovnání.

        Args:
            text: Vstupní text.

        Returns:
            Text se sjednocenými mezerami a převedený na malá písmena.
        """
        return normalize_spaces(text).lower()

    def _object_label(self, obj_type: str) -> str:
        """
        Vrátí lidsky čitelný název typu objektu.

        Args:
            obj_type: Interní typ objektu.

        Returns:
            Český název objektu.
        """
        return {
            "image": "Obrázek",
            "table": "Tabulka",
            "chart": "Graf",
        }.get(obj_type, "Objekt")

    def run(self, document, assignment=None):
        if assignment is None or not hasattr(assignment, "objects"):
            errors = []
            counters = {t: 0 for t in self.SUPPORTED_TYPES}

            for obj in document.iter_objects():
                if obj.type not in self.SUPPORTED_TYPES:
                    continue

                counters[obj.type] += 1
                caption = document.get_object_caption_text(obj, accept_manual=True)

                if caption is None or not caption.strip():
                    errors.append(
                        self.msg(
                            "missing_caption_generic",
                            "{label} č. {i}: chybí titulek.",
                        ).format(
                            label=self._object_label(obj.type),
                            i=counters[obj.type],
                        )
                    )

            if errors:
                return CheckResult(
                    False,
                    self.msg("errors_header_generic", "Chyby v titulcích objektů:")
                    + "\n"
                    + "\n".join("- " + e for e in errors),
                    None,
                    len(errors),
                )

            return CheckResult(
                True,
                self.msg(
                    "ok_generic",
                    "Všechny podporované objekty mají vyplněný titulek.",
                ),
                0,
            )

        expected_objects = [
            obj for obj in assignment.objects if obj["type"] in self.SUPPORTED_TYPES
        ]
        errors = []

        doc_objects_by_type_and_data = {t: {} for t in self.SUPPORTED_TYPES}
        fallback_objects_by_type = {t: [] for t in self.SUPPORTED_TYPES}

        for obj in document.iter_objects():
            if obj.type not in self.SUPPORTED_TYPES:
                continue

            data_id = document.get_object_data_id(obj)
            if data_id:
                doc_objects_by_type_and_data[obj.type][data_id] = obj
            else:
                fallback_objects_by_type[obj.type].append(obj)

        expected_counts = {t: 0 for t in self.SUPPORTED_TYPES}
        actual_counts = {
            t: len(doc_objects_by_type_and_data[t]) + len(fallback_objects_by_type[t])
            for t in self.SUPPORTED_TYPES
        }

        for obj in expected_objects:
            expected_counts[obj["type"]] += 1

        for obj_type in self.SUPPORTED_TYPES:
            if actual_counts[obj_type] < expected_counts[obj_type]:
                errors.append(
                    self.msg(
                        "less_objects",
                        "V dokumentu je méně objektů typu {label} ({doc}) než v zadání ({exp}).",
                    ).format(
                        label=self._object_label(obj_type).lower(),
                        doc=actual_counts[obj_type],
                        exp=expected_counts[obj_type],
                    )
                )

        used_fallback_index_by_type = {t: 0 for t in self.SUPPORTED_TYPES}
        object_index_by_type = {t: 0 for t in self.SUPPORTED_TYPES}

        for expected in expected_objects:
            obj_type = expected["type"]
            object_index_by_type[obj_type] += 1

            expected_data = expected.get("data")
            expected_caption = expected.get("caption", "")

            actual_obj = None

            if expected_data:
                actual_obj = doc_objects_by_type_and_data[obj_type].get(expected_data)

            if actual_obj is None:
                fallback_index = used_fallback_index_by_type[obj_type]
                fallback_list = fallback_objects_by_type[obj_type]

                if fallback_index < len(fallback_list):
                    actual_obj = fallback_list[fallback_index]
                    used_fallback_index_by_type[obj_type] += 1

            if actual_obj is None:
                errors.append(
                    self.msg(
                        "missing_object",
                        "{label} č. {i}: nebyl nalezen odpovídající objekt pro data '{data}'.",
                    ).format(
                        label=self._object_label(obj_type),
                        i=object_index_by_type[obj_type],
                        data=expected_data,
                    )
                )
                continue

            actual = document.get_object_caption_text(actual_obj, accept_manual=True)

            if actual is None or not actual.strip():
                errors.append(
                    self.msg(
                        "missing_caption",
                        "{label} č. {i}: chybí titulek.",
                    ).format(
                        label=self._object_label(obj_type),
                        i=object_index_by_type[obj_type],
                    )
                )
                continue

            if self._norm(actual) != self._norm(expected_caption):
                errors.append(
                    self.msg(
                        "caption_mismatch",
                        '{label} č. {i}:\n  očekáváno: "{expected}"\n  nalezeno:  "{actual}"',
                    ).format(
                        label=self._object_label(obj_type),
                        i=object_index_by_type[obj_type],
                        expected=expected_caption,
                        actual=actual,
                    )
                )

        if errors:
            return CheckResult(
                False,
                self.msg("errors_header", "Chyby v titulcích objektů:")
                + "\n"
                + "\n".join("- " + e for e in errors),
                None,
                len(errors),
            )

        return CheckResult(
            True,
            self.msg("ok", "Všechny titulky objektů odpovídají zadání."),
            0,
        )