def table_to_markdown(table) -> str:
    """渲染 docx/pptx 表格为 Markdown（首行表头）。"""
    rows = list(table.rows)
    if not rows:
        return ""
    lines = []
    header = [c.text.strip() for c in rows[0].cells]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(c.text.strip() for c in row.cells) + " |")
    return "\n".join(lines)
