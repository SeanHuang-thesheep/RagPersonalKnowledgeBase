import os

import fitz
import pytest

from caption.enrich import caption_markdown, CaptionResult


def _png(w=100, h=100):
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w, h))
    pix.set_rect(pix.irect, (10, 20, 30))
    return pix.tobytes("png")


class FakeClient:
    def __init__(self, text="a chart", fail_on=None):
        self.calls = []
        self._text = text
        self._fail_on = fail_on

    def caption(self, image_bytes, context_text, language):
        self.calls.append({"ctx": context_text, "lang": language})
        if self._fail_on is not None and len(self.calls) == self._fail_on:
            raise RuntimeError("api boom")
        return self._text


def _setup(tmp_path, md_text, images: dict):
    assets = tmp_path / "doc_assets"
    assets.mkdir()
    for name, data in images.items():
        (assets / name).write_bytes(data)
    md = tmp_path / "doc.md"
    md.write_text(md_text, encoding="utf-8")
    return str(md)


def test_fills_alt_and_counts(tmp_path):
    md_text = "<!-- page 1 -->\n\nRevenue grew in 2024.\n\n![](doc_assets/img1.png)\n"
    md = _setup(tmp_path, md_text, {"img1.png": _png()})
    client = FakeClient("a red bar chart")
    result = caption_markdown(md, client=client)
    assert isinstance(result, CaptionResult)
    assert result.captioned == 1
    out = open(result.output_path, encoding="utf-8").read()
    assert "![a red bar chart](doc_assets/img1.png)" in out
    assert result.output_path.endswith(".captioned.md")
    assert "Revenue grew" in client.calls[0]["ctx"]


def test_dedup_same_image(tmp_path):
    md_text = "![](doc_assets/img1.png)\n\nmid\n\n![](doc_assets/img1.png)\n"
    md = _setup(tmp_path, md_text, {"img1.png": _png()})
    client = FakeClient("desc")
    result = caption_markdown(md, client=client)
    assert len(client.calls) == 1
    assert result.captioned == 1
    out = open(result.output_path, encoding="utf-8").read()
    assert out.count("![desc](doc_assets/img1.png)") == 2


def test_filters_tiny_no_client_call(tmp_path):
    md_text = "![](doc_assets/small.png)\n"
    md = _setup(tmp_path, md_text, {"small.png": _png(10, 10)})
    client = FakeClient("x")
    result = caption_markdown(md, client=client, min_side=64)
    assert result.skipped == 1
    assert result.captioned == 0
    assert client.calls == []
    out = open(result.output_path, encoding="utf-8").read()
    assert "![](doc_assets/small.png)" in out


def test_missing_image_failed(tmp_path):
    md_text = "![](doc_assets/ghost.png)\n"
    md = _setup(tmp_path, md_text, {})
    client = FakeClient("x")
    result = caption_markdown(md, client=client)
    assert result.failed == 1
    assert result.captioned == 0


def test_api_failure_isolated(tmp_path):
    md_text = "![](doc_assets/a.png)\n\nx\n\n![](doc_assets/b.png)\n"
    md = _setup(tmp_path, md_text, {"a.png": _png(), "b.png": _png(120, 120)})
    client = FakeClient("ok", fail_on=1)
    result = caption_markdown(md, client=client)
    assert result.failed == 1
    assert result.captioned == 1


def test_language_passed(tmp_path):
    md_text = "![](doc_assets/img1.png)\n"
    md = _setup(tmp_path, md_text, {"img1.png": _png()})
    client = FakeClient("d")
    caption_markdown(md, client=client, language="English")
    assert client.calls[0]["lang"] == "English"


def test_missing_md_raises():
    with pytest.raises(FileNotFoundError):
        caption_markdown("nope.md", client=FakeClient())
