import fitz

from caption.cli import main


def _png(w, h):
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w, h))
    pix.set_rect(pix.irect, (10, 20, 30))
    return pix.tobytes("png")


def _setup(tmp_path):
    assets = tmp_path / "doc_assets"
    assets.mkdir()
    (assets / "tiny.png").write_bytes(_png(10, 10))   # 会被过滤，不触发 API
    md = tmp_path / "doc.md"
    md.write_text("text\n\n![](doc_assets/tiny.png)\n", encoding="utf-8")
    return str(md)


def test_cli_writes_output_and_summary(tmp_path, capsys):
    md = _setup(tmp_path)
    out = str(tmp_path / "doc.captioned.md")
    rc = main([md, "-o", out])
    assert rc == 0
    assert open(out, encoding="utf-8").read()
    err = capsys.readouterr().err
    assert "captioned:" in err and "skipped:" in err and "failed:" in err


def test_cli_missing_file_returns_error(capsys):
    rc = main(["nope.md"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err
