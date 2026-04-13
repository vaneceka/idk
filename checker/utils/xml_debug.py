import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

PRETTY_EXTS = (".xml", ".rels", ".rdf")


def _pretty_xml_bytes(raw: bytes) -> bytes:
    """
    Převede XML data do formátované podoby s odsazením.

    Args:
        raw: Původní XML obsah v bajtech.

    Returns:
        Formátované XML v bajtech.
    """
    root = ET.fromstring(raw)
    return minidom.parseString(ET.tostring(root, encoding="utf-8")).toprettyxml(
        indent="  ", encoding="utf-8"
    )


def dump_zip_structure_pretty(
    zip_path: str | Path,
    out_dir: str | Path,
    *,
    pretty_exts: tuple[str, ...] = PRETTY_EXTS,
    copy_non_xml: bool = False,
) -> None:
    """
    Rozbalí archiv do složky a XML soubory uloží v čitelně formátované podobě.

    Args:
        zip_path: Cesta ke vstupnímu ZIP archivu.
        out_dir: Výstupní složka.
        pretty_exts: Přípony souborů, které se mají formátovat jako XML.
        copy_non_xml: Určuje, zda se mají kopírovat i ostatní soubory.
    """
    zip_path = Path(zip_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            target = out_dir / name

            if name.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue

            target.parent.mkdir(parents=True, exist_ok=True)

            lower_name = name.lower()

            try:
                raw = z.read(name)
            except Exception:
                continue

            if lower_name.endswith(pretty_exts):
                try:
                    pretty = _pretty_xml_bytes(raw)
                    target.write_bytes(pretty)
                    continue
                except Exception:
                    pass

            if copy_non_xml:
                target.write_bytes(raw)
