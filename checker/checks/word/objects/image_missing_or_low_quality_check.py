import io

from PIL import Image

from checks.base_check import BaseCheck, CheckResult


class ImageMissingOrLowQualityCheck(BaseCheck):
    code = "T_V03"

    MIN_WIDTH = 150
    MIN_HEIGHT = 150

    def run(self, document, assignment=None):
        expected_count = 0
        if assignment is not None and getattr(assignment, "objects", None):
            expected_count = sum(
                1 for o in assignment.objects if o.get("type") == "image"
            )

        objs = list(document.iter_objects())
        doc_images = [o for o in objs if o.type == "image"]
        actual_count = len(doc_images)

        if expected_count > 0 and actual_count < expected_count:
            return CheckResult(
                False,
                self.msg(
                    "missing_images",
                    "V dokumentu je méně obrázků ({actual}) než v zadání ({expected}).",
                ).format(actual=actual_count, expected=expected_count),
                None,
            )

        if actual_count == 0:
            return CheckResult(
                False, self.msg("no_images", "Není vložen žádný obrázek."), None
            )

        images = list(document.iter_image_bytes())

        if not images:
            return CheckResult(
                True,
                self.msg(
                    "ok_count_only",
                    "Počet obrázků je v pořádku (kontrola rozlišení není v tomto formátu podporována).",
                ),
                0,
            )

        for image_item in images:
            if isinstance(image_item, tuple):
                name, img_bytes = image_item
            else:
                name, img_bytes = None, image_item

            try:
                image = Image.open(io.BytesIO(img_bytes))
                width, height = image.size
            except Exception:
                continue

            if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                if name:
                    return CheckResult(
                        False,
                        self.msg(
                            "low_quality_named",
                            'Obrázek "{name}" má nízké rozlišení ({width}×{height} px).',
                        ).format(name=name, width=width, height=height),
                        None,
                    )

                return CheckResult(
                    False,
                    self.msg(
                        "low_quality",
                        "Obrázek má nízké rozlišení ({width}×{height} px).",
                    ).format(width=width, height=height),
                    None,
                )

        return CheckResult(
            True,
            self.msg("ok", "Všechny obrázky jsou vložené a mají dostatečné rozlišení."),
            0,
        )