import os
import re
from dataclasses import dataclass

from office import MATH_NOTATION_RULES

# math 转写不要 $ 包裹（本模块自己包裹），剥掉规则里关于 $ 的那行
_MATH_RULES = "\n".join(l for l in MATH_NOTATION_RULES.splitlines() if "$" not in l)

_MATH_RE = re.compile(r"!\[math\]\(([^)]+)\)")


@dataclass
class MathFillResult:
    output_path: str
    filled: int
    failed: int


def _clean(text: str) -> str:
    return " ".join(text.replace("$", " ").split())


def _resolve_local(path: str, asset_dir: str, md_path: str):
    if path.startswith(("http://", "https://")):
        return None
    for cand in (path, os.path.join(os.path.dirname(md_path), path),
                 os.path.join(asset_dir, os.path.basename(path))):
        if os.path.isfile(cand):
            return os.path.abspath(cand)
    return os.path.join(asset_dir, os.path.basename(path))


def math_fill_markdown(md_path, *, output_path=None, asset_dir=None, client=None) -> MathFillResult:
    if not os.path.isfile(md_path):
        raise FileNotFoundError(f"Markdown not found: {md_path}")
    stem = os.path.splitext(md_path)[0]
    if asset_dir is None:
        asset_dir = stem + "_assets"
    if output_path is None:
        output_path = stem + ".math.md"
    with open(md_path, encoding="utf-8") as f:
        md = f.read()

    stats = {"filled": 0, "failed": 0}
    cache: dict = {}
    decided: set = set()

    def _get_client():
        nonlocal client
        if client is None:
            from .client import OpenAIMathClient
            client = OpenAIMathClient()
        return client

    def _process(local):
        if not os.path.isfile(local):
            stats["failed"] += 1
            return
        with open(local, "rb") as f:
            data = f.read()
        try:
            out = _get_client().transcribe(data, _MATH_RULES)
        except Exception:
            stats["failed"] += 1
            return
        cleaned = _clean(out)
        if cleaned:
            cache[local] = cleaned
            stats["filled"] += 1
        else:
            stats["failed"] += 1

    def _repl(m):
        path = m.group(1).strip()
        local = _resolve_local(path, asset_dir, md_path)
        if local is None:
            return m.group(0)
        if local not in decided:
            decided.add(local)
            _process(local)
        cap = cache.get(local)
        return f"${cap}$" if cap else m.group(0)

    new_md = _MATH_RE.sub(_repl, md)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_md)
    return MathFillResult(output_path, stats["filled"], stats["failed"])
