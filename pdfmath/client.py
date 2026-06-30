import base64
import io
from typing import Protocol


class MathClient(Protocol):
    def transcribe(self, image_bytes: bytes, rules: str) -> str: ...


_PROMPT = (
    "Transcribe the mathematics in this image into a single-line formula using "
    "EXACTLY the following notation rules. Output ONLY the formula text, no prose, "
    "no surrounding $.\n\n{rules}"
)


def _mime(image_bytes: bytes) -> str:
    try:
        from PIL import Image
        with Image.open(io.BytesIO(image_bytes)) as im:
            fmt = (im.format or "PNG").lower()
    except Exception:
        fmt = "png"
    return f"image/{'jpeg' if fmt == 'jpg' else fmt}"


class OpenAIMathClient:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None, _client=None):
        self._model = model
        if _client is not None:
            self._client = _client
        else:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)

    def transcribe(self, image_bytes: bytes, rules: str) -> str:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        prompt = _PROMPT.format(rules=rules)
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{_mime(image_bytes)};base64,{b64}"}},
                    ],
                }
            ],
        )
        return resp.choices[0].message.content.strip()
