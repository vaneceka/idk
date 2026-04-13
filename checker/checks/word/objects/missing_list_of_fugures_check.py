from checks.base_check import BaseCheck, CheckResult


class MissingListOfFiguresCheck(BaseCheck):
    code = "T_V01"

    def run(self, document, assignment=None):
        images = [o for o in document.iter_objects() if o.type == "image"]

        if not images:
            return CheckResult(
                True, self.msg("no_images", "Dokument neobsahuje obrázky."), 0
            )

        for i in range(document.section_count()):
            if document.has_list_of_figures_in_section(i):
                return CheckResult(True, self.msg("ok", "Seznam obrázků existuje."), 0)

        return CheckResult(False, self.msg("fail", "Seznam obrázků zcela chybí."), None)
