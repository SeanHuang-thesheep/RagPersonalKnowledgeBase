import pytest

from pdfmath.cli import main


def test_cli_missing_file_returns_error(capsys):
    rc = main(["nope.md"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_cli_no_math_markers_writes_output(tmp_path, capsys):
    md = tmp_path / "doc.md"
    md.write_text("just text, no math here\n", encoding="utf-8")
    out = tmp_path / "doc.math.md"
    rc = main([str(md), "-o", str(out)])
    assert rc == 0
    assert out.read_text(encoding="utf-8")
    err = capsys.readouterr().err
    assert "filled:" in err and "failed:" in err
