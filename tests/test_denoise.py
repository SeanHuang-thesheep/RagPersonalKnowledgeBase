import warnings

import pytest

from denoise.clean import denoise_pdf
from denoise.clean import denoise_pdf_report, DenoiseResult


def test_removes_headers_footers_keeps_body(make_pdf):
    markers = ["alpha", "bravo", "charlie"]
    pages = []
    for p in range(3):
        pages.append([
            (50, 30, "ACME Confidential"),            # 页眉（顶部，重复）
            (50, 400, f"Body content {markers[p]}"),   # 正文（中部，唯一）
            (180, 770, str(p + 1)),                    # 页码（底部）
        ])
    path = make_pdf(pages)
    text = denoise_pdf(path)
    assert "ACME Confidential" not in text
    tokens = text.split()
    assert "1" not in tokens and "2" not in tokens and "3" not in tokens
    for m in markers:
        assert f"Body content {m}" in text


def test_single_page_removes_page_number_only(make_pdf):
    path = make_pdf([[
        (50, 30, "Confidential"),
        (50, 400, "Only body line"),
        (180, 770, "5"),
    ]])
    text = denoise_pdf(path)
    assert "Only body line" in text
    assert "5" not in text.split()


def test_scanned_pdf_warns_and_returns_empty(make_pdf):
    path = make_pdf([[]])  # 无文字层
    with pytest.warns(UserWarning, match="scanned"):
        text = denoise_pdf(path)
    assert text == ""


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        denoise_pdf("no_such_file.pdf")


def test_corrupt_pdf_raises_value_error(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"this is not a valid pdf")
    with pytest.raises(ValueError):
        denoise_pdf(str(bad))


def test_report_counts_blank_pages(make_pdf):
    pages = [
        [(50, 400, "page zero body")],
        [],  # 空白页（无文字）
        [(50, 400, "page two body")],
    ]
    path = make_pdf(pages)
    result = denoise_pdf_report(path)
    assert isinstance(result, DenoiseResult)
    assert result.num_pages == 3
    assert result.blank_pages == [1]
    assert result.raw_lines == 2
    assert result.kept_lines == 2
    assert result.removed_lines == 0
    assert "page zero body" in result.text
    assert "page two body" in result.text


def test_report_scanned_pdf(make_pdf):
    path = make_pdf([[], []])  # 全空白
    with pytest.warns(UserWarning, match="scanned"):
        result = denoise_pdf_report(path)
    assert result.text == ""
    assert result.blank_pages == [0, 1]
    assert result.raw_lines == 0
