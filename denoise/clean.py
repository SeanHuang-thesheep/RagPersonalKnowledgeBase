import os
import warnings

from .detect import flag_noise
from .extract import extract_lines


def denoise_pdf(
    pdf_path: str,
    *,
    edge_ratio: float = 0.12,
    repeat_threshold: float = 0.5,
) -> str:
    """去除页眉/页脚/页码/跨页重复文字，返回干净纯文本。"""
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        lines, num_pages = extract_lines(pdf_path)
    except Exception as e:  # 损坏/加密
        raise ValueError(f"Cannot open PDF (corrupt or encrypted?): {pdf_path}") from e

    if num_pages > 0 and not lines:
        warnings.warn(
            "No text layer detected; scanned PDFs are not supported (OCR required).",
            UserWarning,
        )
        return ""

    noise = flag_noise(
        lines, num_pages, edge_ratio=edge_ratio, repeat_threshold=repeat_threshold
    )
    kept = [ln for i, ln in enumerate(lines) if i not in noise]
    kept.sort(key=lambda ln: (ln.page_no, ln.y0, ln.x0))
    return "\n".join(ln.text for ln in kept)
