import base64
import io
from typing import Protocol


def _image_mime(image_bytes: bytes) -> str:
    try:
        from PIL import Image

        with Image.open(io.BytesIO(image_bytes)) as im:
            fmt = (im.format or "PNG").lower()
    except Exception:
        fmt = "png"
    if fmt == "jpg":
        fmt = "jpeg"
    return f"image/{fmt}"


class CaptionClient(Protocol):
    def caption(self, image_bytes: bytes, context_text: str, language: str) -> str: ...


_PROMPT = (
    "You are labeling an image for a search index. Write ONE concise sentence "
    "describing what the image shows. {lang}. Use the surrounding document text "
    "only as context.\n\nSurrounding text:\n{ctx}"
)


def _lang_clause(language: str) -> str:
    if language == "auto":
        return "Write it in the same language as the surrounding text"
    return f"Write it in {language}"


class OpenAICaptionClient:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None, _client=None):
        self._model = model
        if _client is not None:
            self._client = _client
        else:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)

    def caption(self, image_bytes: bytes, context_text: str, language: str) -> str:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        mime = _image_mime(image_bytes)
        prompt = _PROMPT.format(lang=_lang_clause(language), ctx=context_text or "(none)")
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=150,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
        )
        return resp.choices[0].message.content.strip()
