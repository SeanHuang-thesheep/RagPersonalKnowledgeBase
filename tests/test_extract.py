from denoise.extract import extract_lines, Line


def test_extracts_lines_with_coords(make_pdf):
    path = make_pdf([[(50, 400, "Hello body text")]])
    lines, num_pages = extract_lines(path)
    assert num_pages == 1
    assert len(lines) == 1
    ln = lines[0]
    assert isinstance(ln, Line)
    assert ln.text == "Hello body text"
    assert ln.page_no == 0
    assert ln.page_height == 800
    assert ln.y0 < ln.y1  # 包围盒有效


def test_skips_empty_pages(make_pdf):
    path = make_pdf([[]])  # 一页无文字（模拟扫描件）
    lines, num_pages = extract_lines(path)
    assert num_pages == 1
    assert lines == []
