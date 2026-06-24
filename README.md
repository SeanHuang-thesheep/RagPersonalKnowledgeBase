# RAG Personal Knowledge Base — PDF 去噪模块

去除文字版 PDF 的页眉/页脚/页码/跨页重复版权，输出干净文本。

## 安装
```
python -m pip install -r requirements.txt
```

## 用法
CLI:
```
python -m denoise.cli input.pdf -o output.txt
```
作为库:
```python
from denoise import denoise_pdf
text = denoise_pdf("input.pdf")
```
