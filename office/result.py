from dataclasses import dataclass


@dataclass
class ConvertResult:
    markdown: str
    images: list        # list[str] 写出的图片路径（去重后）
    image_count: int    # 去重后写出的图片数
    unit_count: int     # pptx=幻灯片数；docx=顶层块数
