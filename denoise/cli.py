import argparse
import os
import sys

from .clean import denoise_pdf_report
from .markdown import denoise_pdf_to_markdown


def _run_txt(args) -> int:
    try:
        result = denoise_pdf_report(
            args.input,
            edge_ratio=args.edge_ratio,
            repeat_threshold=args.repeat_threshold,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    summary = (
        f"Pages: {result.num_pages} | blank: {len(result.blank_pages)} | "
        f"raw lines: {result.raw_lines} | removed: {result.removed_lines} | "
        f"kept: {result.kept_lines}"
    )
    print(summary, file=sys.stderr)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result.text + "\n")
        except OSError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        print(result.text)
    return 0


def _run_md(args) -> int:
    if args.output:
        asset_dir = os.path.splitext(args.output)[0] + "_assets"
    else:
        asset_dir = "output_assets"
    try:
        result = denoise_pdf_to_markdown(
            args.input,
            asset_dir=asset_dir,
            edge_ratio=args.edge_ratio,
            repeat_threshold=args.repeat_threshold,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    summary = (
        f"Pages: {result.num_pages} | blank: {len(result.blank_pages)} | "
        f"removed: {result.removed_lines} | images: {result.image_count}"
    )
    print(summary, file=sys.stderr)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result.markdown + "\n")
        except OSError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        print(result.markdown)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="去除 PDF 的页眉/页脚/页码并输出干净文本或 Markdown。"
    )
    parser.add_argument("input", help="输入 PDF 路径")
    parser.add_argument("-o", "--output", help="输出文件（默认打印到 stdout）")
    parser.add_argument("--format", choices=["txt", "md"], default="txt", help="输出格式")
    parser.add_argument("--edge-ratio", type=float, default=0.12)
    parser.add_argument("--repeat-threshold", type=float, default=0.5)
    args = parser.parse_args(argv)

    if args.format == "md":
        return _run_md(args)
    return _run_txt(args)


if __name__ == "__main__":
    sys.exit(main())
