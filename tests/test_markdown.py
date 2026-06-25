import os

import pytest

from denoise.markdown import denoise_pdf_to_markdown, MarkdownResult


def test_paragraph_merge(make_rich_pdf):
    path = make_rich_pdf([[("text", 50, 200, "line one\nline two\nline three", 11)]])
    result = denoise_pdf_to_markdown(path)
    assert "line one line two line three" in result.markdown


def test_heading_levels(make_rich_pdf):
    path = make_rich_pdf([[
        ("text", 50, 100, "Huge Title", 24),
        ("text", 50, 200, "Sub Title", 15),
        ("text", 50, 400, "ordinary body text here that is long", 11),
        ("text", 50, 450, "more ordinary body text to set base", 11),
    ]])
    md = denoise_pdf_to_markdown(path).markdown
    assert "# Huge Title" in md
    assert "## Sub Title" in md


def test_page_markers(make_rich_pdf):
    path = make_rich_pdf([
        [("text", 50, 200, "page zero content here", 11)],
        [("text", 50, 200, "page one content here", 11)],
    ])
    md = denoise_pdf_to_markdown(path).markdown
    assert "<!-- page 1 -->" in md
    assert "<!-- page 2 -->" in md


def test_repeated_header_removed_from_md(make_rich_pdf):
    pages = []
    for p in range(3):
        pages.append([
            ("text", 50, 30, "ACME Confidential", 11),
            ("text", 50, 400, f"unique body {p} with several words here", 11),
        ])
    result = denoise_pdf_to_markdown(make_rich_pdf(pages))
    assert "ACME Confidential" not in result.markdown
    assert "unique body 0" in result.markdown


def test_md_returns_result_type(make_rich_pdf):
    result = denoise_pdf_to_markdown(make_rich_pdf([[("text", 50, 200, "hello world body", 11)]]))
    assert isinstance(result, MarkdownResult)
    assert result.num_pages == 1
    assert result.image_count == 0


def test_md_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        denoise_pdf_to_markdown("nope.pdf")


def test_md_scanned_warns(make_rich_pdf):
    path = make_rich_pdf([[]])
    with pytest.warns(UserWarning, match="scanned"):
        result = denoise_pdf_to_markdown(path)
    assert result.markdown == ""
    assert result.blank_pages == [0]


def test_image_extracted_and_referenced(make_rich_pdf, tmp_path):
    path = make_rich_pdf([[
        ("text", 50, 100, "some intro text with words", 11),
        ("image", 50, 400, 20, 20),
    ]])
    asset_dir = str(tmp_path / "assets")
    result = denoise_pdf_to_markdown(path, asset_dir=asset_dir)
    assert result.image_count == 1
    assert len(result.images) == 1
    assert os.path.isfile(result.images[0])
    assert "![](" in result.markdown


def test_image_placeholder_without_asset_dir(make_rich_pdf):
    path = make_rich_pdf([[("image", 50, 400, 20, 20)]])
    result = denoise_pdf_to_markdown(path)  # asset_dir 为 None
    assert result.image_count == 1
    assert result.images == []
    assert "![](p1_img1." in result.markdown
