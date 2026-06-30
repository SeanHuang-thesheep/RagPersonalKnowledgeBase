from dataclasses import dataclass, field

import fitz


@dataclass
class Line:
    page_no: int
    text: str
    y0: float
    y1: float
    page_height: float
    x0: float
    x1: float


@dataclass
class BlockLine:
    text: str
    bbox: tuple          # (x0, y0, x1, y1)
    sizes: list          # list[float]，该行各 span 字号
    flags: list          # list[int]，每个 span 的 flags（PyMuPDF bit0=上标）


@dataclass
class Block:
    page_no: int
    page_height: float
    kind: str            # "text" | "image"
    bbox: tuple
    lines: list          # list[BlockLine]；image 块为 []
    image_bytes: bytes | None
    image_ext: str | None
    is_math: bool = False
    math_png: bytes | None = None
    math_ext: str | None = None


MATH_SYMBOLS = set("∫∑∏√∞≤≥≠≈±×÷→←↔∂∇∈∉⊂⊆∀∃αβγδεζηθλμνξπρστφχψω·")


def _h_segments(page):
    segs = []
    for d in page.get_drawings():
        for item in d.get("items", []):
            if item[0] == "l":
                p1, p2 = item[1], item[2]
                if abs(p1.y - p2.y) < 1.0:
                    segs.append((min(p1.x, p2.x), max(p1.x, p2.x), (p1.y + p2.y) / 2))
            elif item[0] == "re":
                r = item[1]
                if abs(r.y1 - r.y0) < 2.0:
                    segs.append((r.x0, r.x1, (r.y0 + r.y1) / 2))
    return segs


def _dominant_size(page):
    from collections import Counter
    counter = Counter()
    data = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT)
    for b in data.get("blocks", []):
        for ln in b.get("lines", []):
            for s in ln.get("spans", []):
                counter[round(s.get("size", 0))] += 1
    return float(counter.most_common(1)[0][0]) if counter else 0.0


def block_is_math(block, h_segments, dominant_size: float) -> bool:
    text = " ".join(ln.text for ln in block.lines)
    has_symbol = any(ch in MATH_SYMBOLS for ch in text)
    small_or_super = False
    for ln in block.lines:
        for fl in ln.flags:
            if fl & 1:
                small_or_super = True
        for sz in ln.sizes:
            if dominant_size and sz < 0.8 * dominant_size:
                small_or_super = True
    x0, y0, x1, y1 = block.bbox
    has_frac = any(sx1 > x0 and sx0 < x1 and y0 <= sy <= y1 for (sx0, sx1, sy) in h_segments)
    if has_symbol or has_frac:
        return True
    if small_or_super:
        return len(text.split()) <= 8
    return False


def extract_blocks(pdf_path: str, *, render_math: bool = False, math_dpi: int = 200) -> tuple[list, int]:
    """按块抽取（文本块含每行 bbox+字号、图片块含字节），返回 (blocks, num_pages)。"""
    doc = fitz.open(pdf_path)
    try:
        blocks: list = []
        for page_no, page in enumerate(doc):
            page_height = page.rect.height
            h_segments = _h_segments(page) if render_math else []
            dom_size = _dominant_size(page) if render_math else 0.0
            data = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT | fitz.TEXT_PRESERVE_IMAGES)
            for raw_block in data.get("blocks", []):
                btype = raw_block.get("type")
                bbox = tuple(raw_block.get("bbox", (0, 0, 0, 0)))
                if btype == 0:  # 文本块
                    blines = []
                    for line in raw_block.get("lines", []):
                        spans = line.get("spans", [])
                        text = "".join(s["text"] for s in spans).strip()
                        if not text:
                            continue
                        sizes = [float(s["size"]) for s in spans]
                        flags = [int(s.get("flags", 0)) for s in spans]
                        blines.append(BlockLine(text, tuple(line["bbox"]), sizes, flags))
                    if blines:
                        block = Block(page_no, page_height, "text", bbox, blines, None, None)
                        if render_math:
                            block.is_math = block_is_math(block, h_segments, dom_size)
                            if block.is_math:
                                pix = page.get_pixmap(clip=fitz.Rect(bbox), dpi=math_dpi)
                                block.math_png = pix.tobytes("png")
                                block.math_ext = "png"
                        blocks.append(block)
                elif btype == 1:  # 图片块
                    img = raw_block.get("image")
                    if img:
                        blocks.append(Block(page_no, page_height, "image", bbox, [], img, raw_block.get("ext", "png")))
        return blocks, doc.page_count
    finally:
        doc.close()


def extract_lines(pdf_path: str) -> tuple[list[Line], int]:
    """抽取 PDF 全部文本行及坐标，返回 (lines, num_pages)。"""
    doc = fitz.open(pdf_path)
    try:
        lines: list[Line] = []
        for page_no, page in enumerate(doc):
            page_height = page.rect.height
            data = page.get_text("dict")
            for block in data.get("blocks", []):
                if block.get("type") != 0:  # 0 = 文本块
                    continue
                for line in block.get("lines", []):
                    text = "".join(s["text"] for s in line.get("spans", [])).strip()
                    if not text:
                        continue
                    x0, y0, x1, y1 = line["bbox"]
                    lines.append(Line(page_no, text, y0, y1, page_height, x0, x1))
        return lines, doc.page_count
    finally:
        doc.close()
