from documents.spreadsheet.calc_document import CalcDocument
from documents.spreadsheet.excel_document import ExcelDocument
from documents.text.word_document import WordDocument
from documents.text.writer_document import WriterDocument


def load_document(path):
    """
    Načte dokument podle přípony souboru.

    Args:
        path: Cesta k souboru dokumentu.

    Returns:
        Instance odpovídajícího dokumentu podle typu souboru.

    Raises:
        ValueError: Pokud formát souboru není podporován.
    """
    if path.suffix == ".odt":
        return WriterDocument(str(path))
    if path.suffix == ".docx":
        return WordDocument(str(path))

    if path.suffix == ".xlsx":
        return ExcelDocument(str(path))

    if path.suffix == ".ods":
        return CalcDocument(str(path))
    raise ValueError(f"Unsupported format: {path}")
