# RAG Personal Knowledge Base — 文档转换与增强管线

把 **PDF / Word / PowerPoint** 转换成干净的文本或 Markdown，并为其中的图片生成描述，作为 RAG 知识库的入库处理。

| 阶段 | 模块 | 作用 |
|---|---|---|
| 解析 / 去噪 | `denoise` | 文字版 PDF → 去噪纯文本 / 结构化 Markdown |
| 解析 | `office` | `.docx` / `.pptx` → 结构化 Markdown（含 OMML 公式线性化） |
| 内容增强 | `caption` | 为 Markdown 中的图片生成描述，填入 alt（OpenAI 视觉） |
| 内容增强 | `pdfmath` | 把 PDF 渲染出的 `![math]` 公式图转写为线性式 `$...$`（OpenAI 视觉） |

入库管线：`PDF/docx/pptx → (denoise/office) Markdown+图片 → (caption/pdfmath) 图片描述+公式填入 → 待分块 / 向量化 / 索引`。

## 安装
```
python -m pip install -r requirements.txt
```
依赖：PyMuPDF、python-docx、python-pptx、openai、Pillow、pytest。

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
- 公式（OMML）线性化为内联记法并用 `$...$` 包裹（上下标 `x^2`/`x_n`、分数 `(a)/(b)`、矩阵 `[(a,b),(c,d)]`、`sqrt`/积分/求和等）；线性化约定可用 `python -m office.cli --math-rules` 打印，写进检索用的 tool description。
- 仅支持现代格式 `.docx` / `.pptx`。

---

## 图片 Caption 增强（`caption`）

吃已产出的 Markdown + 其 `_assets/` 图片，用 OpenAI 视觉模型（`gpt-4o-mini`）为图片生成描述、填入空 alt 槽，输出 `<名>.captioned.md`，让图片内容进入纯文本检索。

**CLI:**
```
# 需先设置环境变量 OPENAI_API_KEY
python -m caption.cli doc.md -o doc.captioned.md
```

**作为库:**
```python
from caption import caption_markdown

result = caption_markdown("doc.md")   # 默认 OpenAI 客户端 -> CaptionResult
```

要点：
- 把图片所在 page/slide 区块的邻近文本一并发给模型，caption 更贴语境；`language` 可配，`auto` 随文档语言。
- 按尺寸/比例过滤装饰小图；同一图片去重，只调一次 API。
- 单图失败隔离（缺图 / API 异常 → 计入 `failed`、保留空 alt，不中断整轮）。
- 只处理空 alt `![]()`，重跑幂等。

---

## PDF 公式识别（`pdfmath`）

PDF 里的数学是二维散落字形，直接抽取会碎裂（`y²`→`y2`、`dy/dt` 拆行）。两段式处理：

1. **denoise 端**（开 `math_mode=True`）：用几何信号（上标 flag / 小字号 / 数学符号 / 分数线）在块级检测数学，把数学块**渲染成图**，在 markdown 原位输出 `![math](...)`，跳过乱码文本。
2. **pdfmath 端**：把这些 `![math]` 图用视觉模型按 office 的 `MATH_NOTATION_RULES` 约定转写为 `$线性式$`。

```python
from denoise import denoise_pdf_to_markdown
denoise_pdf_to_markdown("book.pdf", asset_dir="assets", math_mode=True)  # 产出含 ![math]
```
```
# 需先设置环境变量 OPENAI_API_KEY
python -m pdfmath.cli book.md -o book.math.md
```

要点：
- `math_mode` 默认关闭，开启才渲染数学块（向后兼容、零额外开销）。
- 块级检测是启发式：误判只多一次视觉调用，漏判则该公式仍保留为原文本。
- 标记隔离：`pdfmath` 只认 `![math]`，`caption` 只填空 alt `![]()`，互不干扰、可任意顺序跑。

---

## 测试
```
python -m pytest
```
（`caption` / `pdfmath` 的测试默认全程 mock，不联网、不产生 API 费用。）

## 路线图（已规划，未实现）
- 分块 + 向量化 + 向量库（入库管线第 4–6 步）
