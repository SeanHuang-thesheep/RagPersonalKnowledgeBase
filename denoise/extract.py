from dataclasses import dataclass

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


@dataclass
class Block:
    page_no: int
    page_height: float
    kind: str            # "text" | "image"
    bbox: tuple
    lines: list          # list[BlockLine]；image 块为 []
    image_bytes: bytes | None
    image_ext: str | None


def extract_blocks(pdf_path: str) -> tuple[list, int]:
    """按块抽取（文本块含每行 bbox+字号、图片块含字节），返回 (blocks, num_pages)。"""
    doc = fitz.open(pdf_path)
    try:
        blocks: list = []
        for page_no, page in enumerate(doc):
            page_height = page.rect.height
            data = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT | fitz.TEXT_PRESERVE_IMAGES)
            for block in data.get("blocks", []):
                btype = block.get("type")
                bbox = tuple(block.get("bbox", (0, 0, 0, 0)))
                if btype == 0:  # 文本块
                    blines = []
                    for line in block.get("lines", []):
                        spans = line.get("spans", [])
                        text = "".join(s["text"] for s in spans).strip()
                        if not text:
                            continue
                        sizes = [float(s["size"]) for s in spans]
                        blines.append(BlockLine(text, tuple(line["bbox"]), sizes))
                    if blines:
                        blocks.append(Block(page_no, page_height, "text", bbox, blines, None, None))
                elif btype == 1:  # 图片块
                    img = block.get("image")
                    if img:
                        blocks.append(Block(page_no, page_height, "image", bbox, [], img, block.get("ext", "png")))
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
