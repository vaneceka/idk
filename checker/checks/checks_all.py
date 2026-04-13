from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

# WORD
from checks.base_check import BaseCheck
from checks.excel.chart.chart_formatting_check import ChartFormattingCheck
from checks.excel.chart.chart_type_check import ChartTypeCheck
from checks.excel.chart.missing_chart_check import MissingChartCheck
from checks.excel.chart.threeD_chart_check import ThreeDChartCheck
from checks.excel.data_process.array_formula_check import ArrayFormulaCheck
from checks.excel.data_process.descriptive_statistic_check import (
    DescriptiveStatisticsCheck,
)
from checks.excel.data_process.missing_desciptive_statistic_check import (
    MissingDescriptiveStatisticsCheck,
)
from checks.excel.data_process.missing_wrong_formula_check import (
    MissingOrWrongFormulaOrNotCalculatedCheck,
)
from checks.excel.data_process.named_range_usage_check import NamedRangeUsageCheck
from checks.excel.data_process.non_copyable_formula_check import (
    NonCopyableFormulasCheck,
)
from checks.excel.data_process.redundant_absolute_reference_check import (
    RedundantAbsoluteReferenceCheck,
)
from checks.excel.data_process.required_data_worksheet_check import (
    RequiredDataWorksheetCheck,
)

# EXCEL
from checks.excel.data_process.required_source_worksheet_check import (
    RequiredSourceWorksheetCheck,
)
from checks.excel.formatting.cells_merge_check import MergedCellsCheck
from checks.excel.formatting.conditional_formatting_check import (
    ConditionalFormattingExistsCheck,
)
from checks.excel.formatting.conditional_formatting_is_correct_check import (
    ConditionalFormattingCorrectnessCheck,
)
from checks.excel.formatting.header_formatting_check import HeaderFormattingCheck
from checks.excel.formatting.number_formatting_check import NumberFormattingCheck
from checks.excel.formatting.table_border_check import TableBorderCheck
from checks.excel.formatting.wrap_text_check import WrapTextCheck
from checks.word.bibliography.bibliography_exist_check import MissingBibliographyCheck
from checks.word.bibliography.bibliography_up_to_date_check import (
    BibliographyNotUpdatedCheck,
)
from checks.word.bibliography.citation_in_wrong_place_check import (
    CitationInWrongPlaceCheck,
)
from checks.word.bibliography.missing_bibliography_filed_check import (
    MissingBibliographyFieldsCheck,
)
from checks.word.bibliography.online_source_url_check import OnlineSourceUrlCheck
from checks.word.bibliography.unused_bibliography_source_check import (
    UnusedBibliographySourceCheck,
)
from checks.word.formatting.bibliography_style_check import BibliographyStyleCheck
from checks.word.formatting.caption_style_check import CaptionStyleCheck
from checks.word.formatting.content_style_check import ContentHeadingStyleCheck
from checks.word.formatting.cover_styles_check import CoverStylesCheck
from checks.word.formatting.custom_style_inheritance_check import (
    CustomStyleInheritanceCheck,
)
from checks.word.formatting.custom_style_usage_check import (
    RequiredCustomStylesUsageCheck,
)
from checks.word.formatting.custom_style_with_tabs_check import CustomStyleWithTabsCheck
from checks.word.formatting.excessive_inline_formatting_check import (
    ExcessiveInlineFormattingCheck,
)
from checks.word.formatting.frontpage_styles_check import FrontpageStylesCheck
from checks.word.formatting.heading_hierarchical_numbering_check import (
    HeadingHierarchicalNumberingCheck,
)
from checks.word.formatting.heading_style_check import HeadingStyleCheck
from checks.word.formatting.headings_used_corretcly_check import (
    HeadingsUsedCorrectlyCheck,
)
from checks.word.formatting.incosistent_formatting_check import (
    InconsistentFormattingCheck,
)
from checks.word.formatting.list_level_used_check import ListLevelUsedCheck
from checks.word.formatting.main_chapter_starts_on_new_page_check import (
    MainChapterStartsOnNewPageCheck,
)
from checks.word.formatting.manual_horizontal_formatting_check import (
    ManualHorizontalSpacingCheck,
)
from checks.word.formatting.manual_vertical_formatting_check import (
    ManualVerticalSpacingCheck,
)
from checks.word.formatting.normal_style_check import NormalStyleCheck
from checks.word.formatting.original_formatting_check import OriginalFormattingCheck
from checks.word.formatting.toc_heading_numbering_check import TocHeadingNumberingCheck
from checks.word.formatting.unnumbered_special_headings_check import (
    UnnumberedSpecialHeadingsCheck,
)
from checks.word.general.range_matches_assignment_check import (
    RangeMatchesAssignmentCheck,
)
from checks.word.header_footer.header_footer_missing_check import (
    HeaderFooterMissingCheck,
)
from checks.word.header_footer.second_section_header_text_check import (
    SecondSectionHeaderHasTextCheck,
)
from checks.word.header_footer.second_section_page_num_start_at_one_check import (
    SecondSectionPageNumberStartsAtOneCheck,
)
from checks.word.header_footer.section_emty_footer_check import SectionFooterEmptyCheck
from checks.word.header_footer.section_emty_header_check import SectionHeaderEmptyCheck
from checks.word.header_footer.section_footer_linked_check import (
    FooterLinkedToPreviousCheck,
)
from checks.word.header_footer.section_footer_page_number_check import (
    SectionFooterHasPageNumberCheck,
)
from checks.word.header_footer.section_header_linked_check import (
    HeaderNotLinkedToPreviousCheck,
)
from checks.word.objects.image_missing_or_low_quality_check import (
    ImageMissingOrLowQualityCheck,
)
from checks.word.objects.list_of_figures_not_up_to_date_check import (
    ListOfFiguresNotUpdatedCheck,
)
from checks.word.objects.missing_list_of_fugures_check import MissingListOfFiguresCheck
from checks.word.objects.object_caption_bindings_check import ObjectCaptionBindingCheck
from checks.word.objects.object_caption_check import ObjectCaptionCheck
from checks.word.objects.object_caption_description_check import (
    ObjectCaptionDescriptionCheck,
)
from checks.word.objects.object_cross_reference_check import ObjectCrossReferenceCheck
from checks.word.sections.missing_cover_page_check import MissingCoverPageCheck
from checks.word.sections.missing_intro_page_check import MissingIntroPageCheck
from checks.word.sections.section1_toc_check import Section1TOCCheck
from checks.word.sections.section2_text_check import Section2TextCheck
from checks.word.sections.section3_bibliography_check import Section3BibliographyCheck
from checks.word.sections.section3_figure_list_check import Section3FigureListCheck
from checks.word.sections.section3_object_list_check import Section3ObjectsListsCheck
from checks.word.sections.section_count_check import SectionCountCheck
from checks.word.sections.sections_missing_check import SectionsMissingCheck
from checks.word.structure.chapter3_numbering_continuity_check import (
    ThirdSectionPageNumberingContinuesCheck,
)
from checks.word.structure.document_structure_check import DocumentStructureCheck
from checks.word.structure.first_chapter_page1_check import (
    FirstChapterStartsOnPageOneCheck,
)
from checks.word.structure.toc_exists_check import TOCExistsCheck
from checks.word.structure.toc_first_section_check import TOCFirstSectionContentCheck
from checks.word.structure.toc_heading_levels_check import TOCHeadingLevelsCheck
from checks.word.structure.toc_illegal_content_check import TOCIllegalContentCheck
from checks.word.structure.toc_up_to_date_check import TOCUpToDateCheck

CheckFactory = Callable[[], BaseCheck]

WORD_CHECK_FACTORIES: dict[str, CheckFactory] = {
    # sections
    "T_C01": lambda: SectionsMissingCheck(),
    "T_C02": lambda: SectionCountCheck(),
    "T_C04": lambda: MissingCoverPageCheck(),
    "T_C05": lambda: MissingIntroPageCheck(),
    "T_C06": lambda: Section1TOCCheck(),
    "T_C07": lambda: Section2TextCheck(),
    "T_C08": lambda: Section3FigureListCheck(),
    "T_C09": lambda: Section3ObjectsListsCheck(),
    "T_C10": lambda: Section3BibliographyCheck(),
    # general
    "T_X04": lambda: RangeMatchesAssignmentCheck(),
    # formatting styles
    "T_F01": lambda: OriginalFormattingCheck(),
    "T_F02": lambda: ExcessiveInlineFormattingCheck(),
    "T_F03": lambda: InconsistentFormattingCheck(),
    "T_F04": lambda: NormalStyleCheck(),
    "T_F05": lambda: HeadingStyleCheck(1),
    "T_F06": lambda: HeadingStyleCheck(2),
    "T_F07": lambda: HeadingStyleCheck(3),
    "T_F08": lambda: ContentHeadingStyleCheck(),
    "T_F09": lambda: ListLevelUsedCheck(1),
    "T_F10": lambda: ListLevelUsedCheck(2),
    "T_F11": lambda: CaptionStyleCheck(),
    "T_F12": lambda: BibliographyStyleCheck(),
    "T_F14": lambda: HeadingHierarchicalNumberingCheck(),
    "T_F15": lambda: TocHeadingNumberingCheck(),
    "T_F16": lambda: UnnumberedSpecialHeadingsCheck(),
    "T_F19": lambda: CustomStyleInheritanceCheck(),
    "T_F18": lambda: RequiredCustomStylesUsageCheck(),
    "T_F20": lambda: CustomStyleWithTabsCheck(),
    "T_F21": lambda: MainChapterStartsOnNewPageCheck(),
    "T_F22": lambda: ManualHorizontalSpacingCheck(),
    "T_F23": lambda: ManualVerticalSpacingCheck(),
    "T_F24": lambda: CoverStylesCheck(),
    "T_F25": lambda: FrontpageStylesCheck(),
    "T_F26": lambda: HeadingsUsedCorrectlyCheck(),
    # toc / structure
    "T_O01": lambda: TOCExistsCheck(),
    "T_O02": lambda: TOCUpToDateCheck(),
    "T_O03": lambda: DocumentStructureCheck(),
    "T_O04": lambda: TOCHeadingLevelsCheck(),
    "T_O05": lambda: TOCFirstSectionContentCheck(),
    "T_O06": lambda: TOCIllegalContentCheck(),
    "T_O07": lambda: FirstChapterStartsOnPageOneCheck(),
    "T_O08": lambda: ThirdSectionPageNumberingContinuesCheck(),
    # objects
    "T_V01": lambda: MissingListOfFiguresCheck(),
    "T_V02": lambda: ListOfFiguresNotUpdatedCheck(),
    "T_V03": lambda: ImageMissingOrLowQualityCheck(),
    "T_V05": lambda: ObjectCaptionCheck(),
    "T_V06": lambda: ObjectCaptionDescriptionCheck(),
    "T_V07": lambda: ObjectCrossReferenceCheck(),
    "T_V08": lambda: ObjectCaptionBindingCheck(),
    # bibliography
    "T_L01": lambda: MissingBibliographyCheck(),
    "T_L02": lambda: BibliographyNotUpdatedCheck(),
    "T_L04": lambda: UnusedBibliographySourceCheck(),
    "T_L05": lambda: CitationInWrongPlaceCheck(),
    "T_L07": lambda: OnlineSourceUrlCheck(),
    "T_L08": lambda: MissingBibliographyFieldsCheck(),
    # header/footer
    "T_Z01": lambda: HeaderFooterMissingCheck(),
    "T_Z02": lambda: SectionHeaderEmptyCheck(1),
    "T_Z03": lambda: SectionFooterEmptyCheck(1),
    "T_Z04": lambda: HeaderNotLinkedToPreviousCheck(2),
    "T_Z05": lambda: FooterLinkedToPreviousCheck(2),
    "T_Z06": lambda: SecondSectionHeaderHasTextCheck(),
    "T_Z07": lambda: SectionFooterHasPageNumberCheck(2),
    "T_Z08": lambda: SecondSectionPageNumberStartsAtOneCheck(),
    "T_Z09": lambda: HeaderNotLinkedToPreviousCheck(3),
    "T_Z10": lambda: FooterLinkedToPreviousCheck(3),
    "T_Z11": lambda: SectionHeaderEmptyCheck(3),
    "T_Z12": lambda: SectionFooterHasPageNumberCheck(3),
}

EXCEL_CHECK_FACTORIES: dict[str, CheckFactory] = {
    # data process
    "S_D01": lambda: RequiredSourceWorksheetCheck(),
    "S_D03": lambda: RequiredDataWorksheetCheck(),
    "S_D04": lambda: NonCopyableFormulasCheck(),
    "S_D05": lambda: MissingOrWrongFormulaOrNotCalculatedCheck(),
    "S_D06": lambda: ArrayFormulaCheck(),
    "S_D07": lambda: NamedRangeUsageCheck(),
    "S_D08": lambda: RedundantAbsoluteReferenceCheck(),
    "S_D09": lambda: MissingDescriptiveStatisticsCheck(),
    "S_D11": lambda: DescriptiveStatisticsCheck(),
    # formatting
    "S_F01": lambda: NumberFormattingCheck(),
    "S_F03": lambda: TableBorderCheck(),
    "S_F04": lambda: MergedCellsCheck(),
    "S_F05": lambda: HeaderFormattingCheck(),
    "S_F06": lambda: WrapTextCheck(),
    "S_F07": lambda: ConditionalFormattingExistsCheck(),
    "S_F08": lambda: ConditionalFormattingCorrectnessCheck(),
    # chart
    "S_G01": lambda: MissingChartCheck(),
    "S_G02": lambda: ThreeDChartCheck(),
    "S_G03": lambda: ChartFormattingCheck(),
    "S_G04": lambda: ChartTypeCheck(),
}


def default_word_codes() -> list[str]:
    return [
        # sections
        "T_C01",
        "T_C02",
        "T_C04",
        "T_C05",
        "T_C06",
        "T_C07",
        "T_C08",
        "T_C09",
        "T_C10",
        # general
        "T_X04",
        # formatting styles
        "T_F01",
        "T_F02",
        "T_F03",
        "T_F04",
        "T_F05",
        "T_F06",
        "T_F07",
        "T_F08",
        "T_F09",
        "T_F10",
        "T_F11",
        "T_F12",
        "T_F14",
        "T_F15",
        "T_F16",
        "T_F18",
        "T_F19",
        "T_F20",
        "T_F21",
        "T_F22",
        "T_F23",
        "T_F24",
        "T_F25",
        "T_F26",
        # toc / structure
        "T_O01",
        "T_O02",
        "T_O03",
        "T_O04",
        "T_O05",
        "T_O06",
        "T_O07",
        "T_O08",
        # objects
        "T_V01",
        "T_V02",
        "T_V03",
        "T_V05",
        "T_V06",
        "T_V07",
        "T_V08",
        # bibliography
        "T_L01",
        "T_L02",
        "T_L04",
        "T_L05",
        "T_L07",
        "T_L08",
        # header/footer
        "T_Z01",
        "T_Z02",
        "T_Z03",
        "T_Z04",
        "T_Z05",
        "T_Z06",
        "T_Z07",
        "T_Z08",
        "T_Z09",
        "T_Z10",
        "T_Z11",
        "T_Z12",
    ]


def default_excel_codes() -> list[str]:
    return [
        # data process
        "S_D01",
        "S_D03",
        "S_D04",
        "S_D05",
        "S_D06",
        "S_D07",
        "S_D08",
        "S_D09",
        "S_D11",
        # formatting
        "S_F01",
        "S_F03",
        "S_F04",
        "S_F05",
        "S_F06",
        "S_F07",
        "S_F08",
        # chart
        "S_G01",
        "S_G02",
        "S_G03",
        "S_G04",
    ]


DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent / "checks_config" / "checks_registry.json"
)


def load_default_config() -> dict:
    data = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("default_checks_config.json musí být JSON objekt")
    return data


def sanitize_enabled_map(raw: dict | None, ordered_codes: list[str]) -> dict[str, bool]:
    out = {c: True for c in ordered_codes}

    if not raw or not isinstance(raw, dict):
        return out

    for k, v in raw.items():
        if isinstance(k, str) and isinstance(v, bool):
            kk = k.strip()
            if kk in out:
                out[kk] = v

    return out


def default_word_enabled_map() -> dict[str, bool]:
    data = load_default_config()
    raw = data.get("text")
    return sanitize_enabled_map(
        raw if isinstance(raw, dict) else None, default_word_codes()
    )


def default_excel_enabled_map() -> dict[str, bool]:
    data = load_default_config()
    raw = data.get("spreadsheet")
    return sanitize_enabled_map(
        raw if isinstance(raw, dict) else None, default_excel_codes()
    )


def build_word_checks(config: dict[str, bool] | None = None) -> list[BaseCheck]:
    enabled = (
        default_word_enabled_map()
        if config is None
        else sanitize_enabled_map(config, default_word_codes())
    )

    out: list[BaseCheck] = []
    for code in default_word_codes():
        if enabled.get(code, False):
            factory = WORD_CHECK_FACTORIES.get(code)
            if factory:
                out.append(factory())
    return out


def build_excel_checks(config: dict[str, bool] | None = None) -> list[BaseCheck]:
    enabled = (
        default_excel_enabled_map()
        if config is None
        else sanitize_enabled_map(config, default_excel_codes())
    )

    out: list[BaseCheck] = []
    for code in default_excel_codes():
        if enabled.get(code, False):
            factory = EXCEL_CHECK_FACTORIES.get(code)
            if factory:
                out.append(factory())
    return out
