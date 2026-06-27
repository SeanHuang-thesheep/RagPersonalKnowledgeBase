import fitz  # 已装，用于生成合法 PNG

from caption.filter import should_caption


def _png(w, h):
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w, h))
    pix.set_rect(pix.irect, (10, 20, 30))
    return pix.tobytes("png")


def test_keeps_real_image():
    assert should_caption(_png(100, 100)) is True


def test_skips_tiny():
    assert should_caption(_png(10, 10), min_side=64) is False


def test_skips_extreme_ratio():
    assert should_caption(_png(400, 5), min_side=1, max_ratio=20.0) is False


def test_skips_corrupt_bytes():
    assert should_caption(b"not an image") is False
