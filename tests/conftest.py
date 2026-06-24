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
