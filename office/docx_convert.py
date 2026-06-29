import os

from docx import Document
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from .images import ImageWriter
from .omml import linearize_math_in
from .result import ConvertResult
from .tables import table_to_markdown

_MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
_DRAWING_BLIP = qn("a:blip")
_EMBED = qn("r:embed")


def _iter_block_items(doc):
    body = doc.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def _heading_prefix(style_name: str) -> str:
    if not style_name:
        return ""
    if style_name == "Title":
        return "# "
    if style_name.startswith("Heading "):
        try:
            level = int(style_name.split(" ", 1)[1])
        except ValueError:
            return ""
        level = max(1, min(level, 6))
        return "#" * level + " "
    return ""


def _list_prefix(style_name: str) -> str:
    if not style_name:
        return ""
    if "List Bullet" in style_name:
        return "- "
    if "List Number" in style_name:
        return "1. "
    return ""


def _para_has_math(para) -> bool:
    return para._p.find(f".//{{{_MATH_NS}}}oMath") is not None


def _para_image_refs(para, doc, writer, counter) -> list:
    refs = []
    for blip in para._p.findall(f".//{_DRAWING_BLIP}"):
        rid = blip.get(_EMBED)
        if not rid:
            continue
        part = doc.part.related_parts.get(rid)
        if part is None:
            continue
        ext = part.partname.ext.lstrip(".") if part.partname.ext else "png"
        counter[0] += 1
        ref = writer.add(part.blob, ext, f"img{counter[0]}")
        refs.append(f"![]({ref})")
    return refs


def docx_to_markdown(path: str, *, asset_dir: str | None = None) -> ConvertResult:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    try:
        doc = Document(path)
    except Exception as e:
        raise ValueError(f"Cannot open docx: {path}") from e

    writer = ImageWriter(asset_dir)
    parts: list = []
    unit_count = 0
    img_counter = [0]
    for block in _iter_block_items(doc):
        unit_count += 1
        if isinstance(block, Table):
            md = table_to_markdown(block)
            if md:
                parts.append(md)
            continue
        para = block
        math_parts = linearize_math_in(para._p)
        if math_parts:
            for m in math_parts:
                parts.append(f"${m}$" if m else "[equation]")
        elif _para_has_math(para):
            parts.append("[equation]")
        for ref in _para_image_refs(para, doc, writer, img_counter):
            parts.append(ref)
        text = para.text.strip()
        if not text:
            continue
        style = para.style.name if para.style else ""
        prefix = _heading_prefix(style) or _list_prefix(style)
        parts.append(prefix + text)

    return ConvertResult("\n\n".join(parts), writer.paths, writer.count, unit_count)
