import os

from office.images import ImageWriter


def test_dedup_same_bytes_written_once(tmp_path):
    w = ImageWriter(str(tmp_path / "assets"))
    ref1 = w.add(b"PNGDATA", "png", "img1")
    ref2 = w.add(b"PNGDATA", "png", "img2")  # 相同字节
    assert ref1 == ref2                       # 复用同一文件
    assert w.count == 1
    assert len(w.paths) == 1
    assert os.path.isfile(w.paths[0])
    assert "![" not in ref1 and ref1.endswith(".png")


def test_distinct_bytes_two_files(tmp_path):
    w = ImageWriter(str(tmp_path / "assets"))
    w.add(b"AAA", "png", "img1")
    w.add(b"BBB", "png", "img2")
    assert w.count == 2
    assert len(w.paths) == 2


def test_no_asset_dir_placeholder(tmp_path):
    w = ImageWriter(None)
    ref = w.add(b"AAA", "png", "img1")
    assert ref == "img1.png"      # 占位文件名
    assert w.paths == []
    assert w.count == 1
