from .convert import convert_to_markdown
from .docx_convert import docx_to_markdown
from .pptx_convert import pptx_to_markdown
from .result import ConvertResult

__all__ = [
    "ConvertResult",
    "docx_to_markdown",
    "pptx_to_markdown",
    "convert_to_markdown",
]
