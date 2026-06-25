import os
import warnings
from collections import Counter
from dataclasses import dataclass
from statistics import median

from .detect import flag_noise
from .extract import Line, extract_blocks


@dataclass
class MarkdownResult:
    markdown: str
    images: list          # list[str] 写出的图片路径
    num_pages: int
    blank_pages: list     # list[int]
    removed_lines: int
    image_count: int


def _base_font_size(blocks) -> float:
    counter: Counter = Counter()
    for b in blocks:
        if b.kind != "text":
            continue
        for ln in b.lines:
            for s in ln.sizes:
                counter[round(s)] += 1
    if not counter:
        return 0.0
    return float(counter.most_common(1)[0][0])


def _heading_prefix(block, base: float) -> str:
    sizes = [s for ln in block.lines for s in ln.sizes]
    if not sizes or base <= 0:
        return ""
    s = median(sizes)
    if s >= 1.6 * base:
        return "# "
    if s >= 1.3 * base:
        return "## "
    return ""


def denoise_pdf_to_markdown(
    pdf_path: str,
    *,
    asset_dir: str | None = None,
    edge_ratio: float = 0.12,
    repeat_threshold: float = 0.5,
) -> MarkdownResult:
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    try:
        blocks, num_pages = extract_blocks(pdf_path)
    except RuntimeError as e:
        raise ValueError(f"Cannot open PDF (corrupt or encrypted?): {pdf_path}") from e

    pages_with_content = {b.page_no for b in blocks}
    blank_pages = [p for p in range(num_pages) if p not in pages_with_content]

    if not blocks:
        warnings.warn(
            "No text layer detected; scanned PDFs are not supported (OCR required).",
            UserWarning,
        )
        return MarkdownResult("", [], num_pages, blank_pages, 0, 0)

    # 去噪：从块构造行喂给 flag_noise，记录扁平行索引 -> (块号, 行号)
    detect_lines = []
    flat = []
    for bi, b in enumerate(blocks):
        if b.kind != "text":
            continue
        for li, ln in enumerate(b.lines):
            x0, y0, x1, y1 = ln.bbox
            detect_lines.append(Line(b.page_no, ln.text, y0, y1, b.page_height, x0, x1))
            flat.append((bi, li))
    noise_idx = flag_noise(
        detect_lines, num_pages, edge_ratio=edge_ratio, repeat_threshold=repeat_threshold
    )
    noise_pairs = {flat[i] for i in noise_idx}

    base = _base_font_size(blocks)
    by_page: dict = {}
    for bi, b in enumerate(blocks):
        by_page.setdefault(b.page_no, []).append(bi)

    parts: list = []
    for page_no in range(num_pages):
        parts.append(f"<!-- page {page_no + 1} -->")
        bidxs = sorted(
            by_page.get(page_no, []),
            key=lambda i: (blocks[i].bbox[1], blocks[i].bbox[0]),
        )
        for bi in bidxs:
            b = blocks[bi]
            if b.kind == "image":
                continue  # 图片在后续任务处理
            kept = [ln.text for li, ln in enumerate(b.lines) if (bi, li) not in noise_pairs]
            if not kept:
                continue
            parts.append(_heading_prefix(b, base) + " ".join(kept))

    markdown = "\n\n".join(parts)
    return MarkdownResult(markdown, [], num_pages, blank_pages, len(noise_idx), 0)
