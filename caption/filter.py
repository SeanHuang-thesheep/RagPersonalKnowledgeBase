import io

from PIL import Image


def should_caption(image_bytes: bytes, *, min_side: int = 64, max_ratio: float = 20.0) -> bool:
    """判断一张图是否值得 caption（过滤装饰小图/损坏图）。"""
    try:
        with Image.open(io.BytesIO(image_bytes)) as im:
            w, h = im.size
    except Exception:
        return False
    if w <= 0 or h <= 0:
        return False
    if min(w, h) < min_side:
        return False
    if max(w, h) / min(w, h) > max_ratio:
        return False
    return True
