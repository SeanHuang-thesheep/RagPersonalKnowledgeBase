import warnings

import pytest

from denoise.clean import denoise_pdf


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
