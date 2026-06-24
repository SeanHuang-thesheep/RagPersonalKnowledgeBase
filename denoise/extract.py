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
