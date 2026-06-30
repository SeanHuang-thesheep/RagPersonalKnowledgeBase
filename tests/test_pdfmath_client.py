from pdfmath.client import OpenAIMathClient


class _Comp:
    def __init__(self):
        self.last = None

    def create(self, **kwargs):
        self.last = kwargs

        class R:
            class _C:
                class _M:
                    content = "  (dy)/(dt) + y^2 = 0  "
                message = _M()
            choices = [_C()]
        return R()


class _Chat:
    def __init__(self):
        self.completions = _Comp()


class _Fake:
    def __init__(self):
        self.chat = _Chat()


def test_transcribe_builds_request_and_strips():
    fake = _Fake()
    c = OpenAIMathClient(_client=fake)
    out = c.transcribe(b"IMG", "RULES_TEXT [( sqrt")
    assert out == "(dy)/(dt) + y^2 = 0"
    kw = fake.chat.completions.last
    content = kw["messages"][0]["content"]
    text = [p for p in content if p["type"] == "text"][0]["text"]
    img = [p for p in content if p["type"] == "image_url"][0]
    assert "RULES_TEXT" in text
    assert img["image_url"]["url"].startswith("data:image/")
