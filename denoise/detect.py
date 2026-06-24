import re
from collections import defaultdict

from .extract import Line

_PAGE_NUMBER_PATTERNS = [
    re.compile(r"^\d+$"),
    re.compile(r"^[-–—]\s*\d+\s*[-–—]$"),
    re.compile(r"^第\s*\d+\s*页$"),
    re.compile(r"^(?:page|p\.?)\s*\d+$", re.IGNORECASE),
    re.compile(r"^\d+\s*/\s*\d+$"),
]


def _is_page_number(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    return any(p.match(t) for p in _PAGE_NUMBER_PATTERNS)


def _normalize(text: str) -> str:
    """折叠空白并将数字串替换为占位符，使仅数字不同的行归为一类。"""
    t = re.sub(r"\s+", " ", text.strip())
    return re.sub(r"\d+", "#", t)


def _in_edge_zone(line: Line, edge_ratio: float) -> bool:
    top = line.page_height * edge_ratio
    bottom = line.page_height * (1 - edge_ratio)
    return line.y1 <= top or line.y0 >= bottom


def flag_noise(
    lines: list[Line],
    num_pages: int,
    *,
    edge_ratio: float = 0.12,
    repeat_threshold: float = 0.5,
) -> set[int]:
    """返回应删除的行索引集合。"""
    noise: set[int] = set()
    edge_idx = [i for i, ln in enumerate(lines) if _in_edge_zone(ln, edge_ratio)]

    # 规则1：边缘区页码
    for i in edge_idx:
        if _is_page_number(lines[i].text):
            noise.add(i)

    # 规则2：跨页重复（仅多页有意义）
    if num_pages > 1:
        pages_by_norm: dict[str, set[int]] = defaultdict(set)
        idx_by_norm: dict[str, list[int]] = defaultdict(list)
        for i in edge_idx:
            norm = _normalize(lines[i].text)
            if not norm:
                continue
            pages_by_norm[norm].add(lines[i].page_no)
            idx_by_norm[norm].append(i)
        for norm, pages in pages_by_norm.items():
            if len(pages) / num_pages >= repeat_threshold:
                noise.update(idx_by_norm[norm])

    return noise
