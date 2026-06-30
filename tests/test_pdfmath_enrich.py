import fitz
import pytest

from pdfmath.enrich import math_fill_markdown, MathFillResult


def _png():
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 20))
    pix.set_rect(pix.irect, (240, 240, 240))
    return pix.tobytes("png")


class FakeMath:
    def __init__(self, text="(dy)/(dt) + y^2 = 0", fail=False):
        self.calls = []
        self._text = text
        self._fail = fail

    def transcribe(self, image_bytes, rules):
        self.calls.append(rules)
        if self._fail:
            raise RuntimeError("boom")
        return self._text


def _setup(tmp_path, md_text, images):
    assets = tmp_path / "doc_assets"
    assets.mkdir()
    for name, data in images.items():
        (assets / name).write_bytes(data)
    md = tmp_path / "doc.md"
    md.write_text(md_text, encoding="utf-8")
    return str(md)


def test_fills_math_marker(tmp_path):
    md = _setup(tmp_path, "intro\n\n![math](doc_assets/p1_math1.png)\n", {"p1_math1.png": _png()})
    client = FakeMath()
    res = math_fill_markdown(md, client=client)
    assert isinstance(res, MathFillResult)
    assert res.filled == 1
    out = open(res.output_path, encoding="utf-8").read()
    assert "$(dy)/(dt) + y^2 = 0$" in out
    assert "![math](" not in out
    assert "[(" in client.calls[0]


def test_dedup(tmp_path):
    md = _setup(tmp_path, "![math](doc_assets/m.png)\n\nx\n\n![math](doc_assets/m.png)\n", {"m.png": _png()})
    client = FakeMath("X")
    res = math_fill_markdown(md, client=client)
    assert len(client.calls) == 1
    assert open(res.output_path, encoding="utf-8").read().count("$X$") == 2


def test_missing_image_failed(tmp_path):
    md = _setup(tmp_path, "![math](doc_assets/ghost.png)\n", {})
    res = math_fill_markdown(md, client=FakeMath())
    assert res.failed == 1
    assert res.filled == 0


def test_api_failure_kept(tmp_path):
    md = _setup(tmp_path, "![math](doc_assets/m.png)\n", {"m.png": _png()})
    res = math_fill_markdown(md, client=FakeMath(fail=True))
    assert res.failed == 1
    out = open(res.output_path, encoding="utf-8").read()
    assert "![math](doc_assets/m.png)" in out


def test_missing_md_raises():
    with pytest.raises(FileNotFoundError):
        math_fill_markdown("nope.md", client=FakeMath())
