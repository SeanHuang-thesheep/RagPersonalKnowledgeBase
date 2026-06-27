from caption.client import OpenAICaptionClient, _lang_clause


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResp:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self):
        self.last = None

    def create(self, **kwargs):
        self.last = kwargs
        return _FakeResp("  a red bar chart  ")


class _FakeChat:
    def __init__(self):
        self.completions = _FakeCompletions()


class _FakeOpenAI:
    def __init__(self):
        self.chat = _FakeChat()


def test_lang_clause():
    assert "same language" in _lang_clause("auto")
    assert "English" in _lang_clause("English")


def test_caption_builds_request_and_strips():
    fake = _FakeOpenAI()
    c = OpenAICaptionClient(model="gpt-4o-mini", _client=fake)
    out = c.caption(b"IMGBYTES", "revenue 2020-2024", "auto")
    assert out == "a red bar chart"                      # stripped
    kwargs = fake.chat.completions.last
    assert kwargs["model"] == "gpt-4o-mini"
    content = kwargs["messages"][0]["content"]
    text_parts = [p for p in content if p["type"] == "text"]
    img_parts = [p for p in content if p["type"] == "image_url"]
    assert "revenue 2020-2024" in text_parts[0]["text"]
    assert img_parts[0]["image_url"]["url"].startswith("data:image/png;base64,")


def test_caption_jpeg_mime():
    import fitz

    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8))
    pix.set_rect(pix.irect, (1, 2, 3))
    jpg = pix.tobytes("jpg")
    fake = _FakeOpenAI()
    c = OpenAICaptionClient(_client=fake)
    c.caption(jpg, "ctx", "auto")
    url = fake.chat.completions.last["messages"][0]["content"][1]["image_url"]["url"]
    assert url.startswith("data:image/jpeg;base64,")
