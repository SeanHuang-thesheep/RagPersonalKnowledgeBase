from denoise.extract import extract_lines, Line
from denoise.extract import extract_blocks, BlockLine


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


def test_extract_blocks_text_and_image(make_rich_pdf):
    path = make_rich_pdf([[
        ("text", 50, 100, "Big Heading", 24),
        ("text", 50, 400, "normal body text", 11),
        ("image", 50, 600, 20, 20),
    ]])
    blocks, num_pages = extract_blocks(path)
    assert num_pages == 1
    text_blocks = [b for b in blocks if b.kind == "text"]
    image_blocks = [b for b in blocks if b.kind == "image"]
    assert len(image_blocks) == 1
    assert image_blocks[0].image_bytes
    assert image_blocks[0].image_ext
    sizes = [s for b in text_blocks for ln in b.lines for s in ln.sizes]
    assert any(round(s) >= 20 for s in sizes)
    assert any(round(s) == 11 for s in sizes)
    bl = text_blocks[0].lines[0]
    assert isinstance(bl, BlockLine)
    assert bl.text
    assert len(bl.bbox) == 4
    assert text_blocks[0].page_height == 800
