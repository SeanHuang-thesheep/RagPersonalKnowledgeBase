# RAG Personal Knowledge Base — 文档转换管线

把 **PDF / Word / PowerPoint** 转换成干净的文本或 Markdown，作为 RAG 知识库的输入处理。

| 输入 | 模块 | 输出 |
|---|---|---|
| `.pdf`（文字版） | `denoise` | 去噪纯文本 / 结构化 Markdown |
| `.docx` / `.pptx` | `office` | 结构化 Markdown |

## 安装
```
python -m pip install -r requirements.txt
```
依赖：PyMuPDF、python-docx、python-pptx、pytest。

---

## PDF 去噪与导出（`denoise`）

去除文字版 PDF 的页眉 / 页脚 / 页码 / 跨页重复版权，输出干净文本；或导出结构化 Markdown（段落合并、标题推断、图片抽取、页码标记）。

**CLI:**
```
python -m denoise.cli input.pdf -o output.txt              # 纯文本
python -m denoise.cli input.pdf -o output.md --format md   # Markdown（图片落 output_assets/）
```

**作为库:**
```python
from denoise import denoise_pdf, denoise_pdf_report, denoise_pdf_to_markdown

text = denoise_pdf("input.pdf")                      # -> str
report = denoise_pdf_report("input.pdf")             # -> DenoiseResult（含空白页/行数统计）
md = denoise_pdf_to_markdown("input.pdf", asset_dir="assets")  # -> MarkdownResult
```

要点：
- 页码采用「跨页门控」，仅当页码行覆盖足够多页面时才删，避免误删正文数字。
- 单页文档跳过跨页重复检测，防止删掉靠边的正文。
- 仅支持文字版 PDF；扫描件会给出提示（OCR 暂不支持）。

---

## Office 转换（`office`）

把 `.docx` / `.pptx` 转成 Markdown：标题、段落、列表、表格、图片；PPT 额外含演讲者备注。

**CLI:**
```
python -m office.cli slides.pptx -o slides.md     # 图片落 slides_assets/
python -m office.cli report.docx -o report.md
```

**作为库:**
```python
from office import convert_to_markdown, docx_to_markdown, pptx_to_markdown

result = convert_to_markdown("deck.pptx", asset_dir="assets")  # 按扩展名分派 -> ConvertResult
```

要点：
- 图片抽取为文件 + `![]()` 引用，并按内容哈希**去重**（重复 logo 只存一份）。
- 公式（OMML）本期不解析，但检测到即输出 `[equation]` 占位，不静默丢失。
- 仅支持现代格式 `.docx` / `.pptx`。

---

## 测试
```
python -m pytest
```

## 路线图（已规划，未实现）
- PDF 数学公式识别（几何启发式 / 视觉模型）
- Office OMML 公式线性化
- 图片的 LLM 识别 / caption（图片已抽取并留有空 alt 槽）
