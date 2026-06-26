import hashlib
import os


class ImageWriter:
    """按内容哈希去重的图片写盘助手。asset_dir 为 None 时只产占位引用、不写文件。"""

    def __init__(self, asset_dir: str | None):
        self._asset_dir = asset_dir
        self._by_hash: dict = {}   # sha1 -> ref 路径
        self._paths: list = []
        if asset_dir:
            os.makedirs(asset_dir, exist_ok=True)

    def add(self, data: bytes, ext: str, name_hint: str) -> str:
        key = hashlib.sha1(data).hexdigest()
        if key in self._by_hash:
            return self._by_hash[key]
        fname = f"{name_hint}.{ext}"
        if self._asset_dir:
            fpath = os.path.join(self._asset_dir, fname)
            with open(fpath, "wb") as f:
                f.write(data)
            ref = fpath.replace("\\", "/")
            self._paths.append(fpath)
        else:
            ref = fname
        self._by_hash[key] = ref
        return ref

    @property
    def paths(self) -> list:
        return self._paths

    @property
    def count(self) -> int:
        return len(self._by_hash)
