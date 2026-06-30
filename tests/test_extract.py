from denoise.extract import extract_lines, Line
from denoise.extract import extract_blocks, BlockLine
from denoise.extract import (
    Block, block_is_math, MATH_SYMBOLS,
)


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


def _bl(text, sizes, flags, bbox=(50, 100, 200, 115)):
    return BlockLine(text=text, bbox=bbox, sizes=sizes, flags=flags)


def _blk(lines, bbox=(50, 100, 200, 130)):
    return Block(page_no=0, page_height=800, kind="text", bbox=bbox,
                 lines=lines, image_bytes=None, image_ext=None)


def test_math_symbol_block_detected():
    blk = _blk([_bl("∫ x dx", [12.0], [0])])
    assert block_is_math(blk, [], 12.0) is True


def test_superscript_short_block_detected():
    blk = _blk([_bl("E = mc", [12.0, 8.0], [0, 1])])
    assert block_is_math(blk, [], 12.0) is True


def test_small_size_span_detected():
    blk = _blk([_bl("x n", [12.0, 7.0], [0, 0])])
    assert block_is_math(blk, [], 12.0) is True


def test_fraction_bar_overlap_detected():
    blk = _blk([_bl("dy dt", [12.0], [0])], bbox=(50, 100, 120, 140))
    segs = [(55, 115, 120.0)]
    assert block_is_math(blk, segs, 12.0) is True


def test_plain_prose_not_math():
    blk = _blk([_bl("the quick brown fox jumps", [12.0], [0])])
    assert block_is_math(blk, [], 12.0) is False


def test_superscript_in_long_prose_not_math():
    blk = _blk([_bl("see footnote one for the long detailed explanation here", [12.0, 8.0], [0, 1])])
    assert block_is_math(blk, [], 12.0) is False


def test_extract_blocks_renders_math(tmp_path):
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=400, height=800)
    page.insert_text((50, 400), "∫ x dx", fontsize=14)
    p = str(tmp_path / "m.pdf")
    doc.save(p); doc.close()
    blocks, _ = extract_blocks(p, render_math=True)
    math_blocks = [b for b in blocks if b.is_math]
    assert len(math_blocks) >= 1
    assert math_blocks[0].math_png
    assert math_blocks[0].math_ext == "png"


def test_extract_blocks_no_render_by_default(tmp_path):
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=400, height=800)
    page.insert_text((50, 400), "∫ x dx", fontsize=14)
    p = str(tmp_path / "m.pdf")
    doc.save(p); doc.close()
    blocks, _ = extract_blocks(p)
    for b in blocks:
        assert b.math_png is None
