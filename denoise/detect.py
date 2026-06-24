import re

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
