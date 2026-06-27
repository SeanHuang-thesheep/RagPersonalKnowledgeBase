import os
import re
from dataclasses import dataclass

from .filter import should_caption

_IMG_RE = re.compile(r"!\[\]\(([^)]+)\)")          # 仅匹配空 alt 的图片引用
_BLOCK_MARKER = re.compile(r"<!--\s*(?:page|slide)\s+\d+\s*-->")


@dataclass
class CaptionResult:
    output_path: str
    captioned: int
    skipped: int
    failed: int


def _clean(text: str) -> str:
    return " ".join(text.replace("[", r"\[").replace("]", r"\]").split())


def _resolve_local(path: str, asset_dir: str, md_path: str):
    if path.startswith(("http://", "https://")):
        return None
    for cand in (
        path,
        os.path.join(os.path.dirname(md_path), path),
        os.path.join(asset_dir, os.path.basename(path)),
    ):
        if os.path.isfile(cand):
            return os.path.abspath(cand)
    # 都不存在：返回 asset_dir 下同名路径（不存在），让 _process 计为 failed
    return os.path.join(asset_dir, os.path.basename(path))


def _context_for(md: str, start: int, end: int, limit: int = 800) -> str:
    block_start = 0
    for m in _BLOCK_MARKER.finditer(md, 0, start):
        block_start = m.end()
    nxt = _BLOCK_MARKER.search(md, end)
    block_end = nxt.start() if nxt else len(md)
    block = md[block_start:block_end]
    block = _IMG_RE.sub(" ", block)
    block = _BLOCK_MARKER.sub(" ", block)
    return " ".join(block.split())[:limit]


def caption_markdown(
    md_path: str,
    *,
    output_path: str | None = None,
    asset_dir: str | None = None,
    client=None,
    language: str = "auto",
    min_side: int = 64,
    max_ratio: float = 20.0,
) -> CaptionResult:
    if not os.path.isfile(md_path):
        raise FileNotFoundError(f"Markdown not found: {md_path}")
    stem = os.path.splitext(md_path)[0]
    if asset_dir is None:
        asset_dir = stem + "_assets"
    if output_path is None:
        output_path = stem + ".captioned.md"

    with open(md_path, encoding="utf-8") as f:
        md = f.read()

    stats = {"captioned": 0, "skipped": 0, "failed": 0}
    cache: dict = {}
    decided: set = set()
    seen_ext: set = set()

    def _get_client():
        nonlocal client
        if client is None:
            from .client import OpenAICaptionClient
            client = OpenAICaptionClient()
        return client

    def _process(local: str, ctx: str):
        if not os.path.isfile(local):
            stats["failed"] += 1
            return
        with open(local, "rb") as f:
            data = f.read()
        if not should_caption(data, min_side=min_side, max_ratio=max_ratio):
            stats["skipped"] += 1
            return
        try:
            cap = _get_client().caption(data, ctx, language)
        except Exception:
            stats["failed"] += 1
            return
        cleaned = _clean(cap)
        if cleaned:
            cache[local] = cleaned
            stats["captioned"] += 1
        else:
            stats["failed"] += 1

    def _repl(m):
        path = m.group(1).strip()
        local = _resolve_local(path, asset_dir, md_path)
        if local is None:
            if path not in seen_ext:
                seen_ext.add(path)
                stats["skipped"] += 1
            return m.group(0)
        if local not in decided:
            decided.add(local)
            _process(local, _context_for(md, m.start(), m.end()))
        cap = cache.get(local)
        return f"![{cap}]({path})" if cap else m.group(0)

    new_md = _IMG_RE.sub(_repl, md)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_md)
    return CaptionResult(output_path, stats["captioned"], stats["skipped"], stats["failed"])
