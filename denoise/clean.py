import os
import warnings
from dataclasses import dataclass

from .detect import flag_noise
from .extract import extract_lines


@dataclass
class DenoiseResult:
    text: str              # 去噪后的纯文本
    num_pages: int         # 总页数
    blank_pages: list[int] # 完全无文字的页码（0 基，升序）
    raw_lines: int         # 抽取到的总行数
    removed_lines: int     # 删除的噪声行数
    kept_lines: int        # 保留行数


def denoise_pdf_report(
    pdf_path: str,
    *,
    edge_ratio: float = 0.12,
    repeat_threshold: float = 0.5,
) -> DenoiseResult:
    """去噪并返回完整统计。"""
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        lines, num_pages = extract_lines(pdf_path)
    except RuntimeError as e:  # fitz 打开损坏/加密文件时抛 RuntimeError 子类
        raise ValueError(f"Cannot open PDF (corrupt or encrypted?): {pdf_path}") from e

    pages_with_text = {ln.page_no for ln in lines}
    blank_pages = [p for p in range(num_pages) if p not in pages_with_text]

    if not lines:
        warnings.warn(
            "No text layer detected; scanned PDFs are not supported (OCR required).",
            UserWarning,
        )
        return DenoiseResult(
            text="",
            num_pages=num_pages,
            blank_pages=blank_pages,
            raw_lines=0,
            removed_lines=0,
            kept_lines=0,
        )

    noise = flag_noise(
        lines, num_pages, edge_ratio=edge_ratio, repeat_threshold=repeat_threshold
    )
    kept = [ln for i, ln in enumerate(lines) if i not in noise]
    kept.sort(key=lambda ln: (ln.page_no, ln.y0, ln.x0))
    text = "\n".join(ln.text for ln in kept)
    return DenoiseResult(
        text=text,
        num_pages=num_pages,
        blank_pages=blank_pages,
        raw_lines=len(lines),
        removed_lines=len(noise),
        kept_lines=len(kept),
    )


def denoise_pdf(
    pdf_path: str,
    *,
    edge_ratio: float = 0.12,
    repeat_threshold: float = 0.5,
) -> str:
    """去除页眉/页脚/页码/跨页重复文字，返回干净纯文本。"""
    return denoise_pdf_report(
        pdf_path, edge_ratio=edge_ratio, repeat_threshold=repeat_threshold
    ).text
