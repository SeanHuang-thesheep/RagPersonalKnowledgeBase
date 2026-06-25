import fitz
import pytest


@pytest.fixture
def make_pdf(tmp_path):
    """生成 PDF。pages: list[list[(x, y, text)]]，page 尺寸 400x800。"""
    def _make(pages, name="sample.pdf"):
        doc = fitz.open()
        for items in pages:
            page = doc.new_page(width=400, height=800)
            for x, y, text in items:
                page.insert_text((x, y), text, fontsize=11)
        path = str(tmp_path / name)
        doc.save(path)
        doc.close()
        return path
    return _make


@pytest.fixture
def make_rich_pdf(tmp_path):
    """生成含不同字号文本与图片的 PDF（页 400x800）。
    pages: list[list[item]]，item 形如:
      ("text", x, y, text, fontsize)   # text 可含 \n 形成多行块
      ("image", x, y, w, h)            # 插入一张 w×h 纯色小图
    """
    def _make(pages, name="rich.pdf"):
        doc = fitz.open()
        for items in pages:
            page = doc.new_page(width=400, height=800)
            for item in items:
                if item[0] == "text":
                    _, x, y, text, size = item
                    page.insert_text((x, y), text, fontsize=size)
                elif item[0] == "image":
                    _, x, y, w, h = item
                    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w, h))
                    pix.set_rect(pix.irect, (200, 100, 50))
                    page.insert_image(fitz.Rect(x, y, x + w, y + h), pixmap=pix)
        path = str(tmp_path / name)
        doc.save(path)
        doc.close()
        return path
    return _make
