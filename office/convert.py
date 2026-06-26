import os

from .docx_convert import docx_to_markdown
from .pptx_convert import pptx_to_markdown
from .result import ConvertResult


def convert_to_markdown(path: str, *, asset_dir: str | None = None) -> ConvertResult:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return docx_to_markdown(path, asset_dir=asset_dir)
    if ext == ".pptx":
        return pptx_to_markdown(path, asset_dir=asset_dir)
    raise ValueError(f"Unsupported file type: {ext or path} (expected .docx or .pptx)")
