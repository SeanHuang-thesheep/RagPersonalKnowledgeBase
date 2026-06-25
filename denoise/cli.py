import argparse
import sys

from .clean import denoise_pdf_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="去除 PDF 的页眉/页脚/页码并输出干净文本。"
    )
    parser.add_argument("input", help="输入 PDF 路径")
    parser.add_argument("-o", "--output", help="输出文本文件（默认打印到 stdout）")
    parser.add_argument("--edge-ratio", type=float, default=0.12)
    parser.add_argument("--repeat-threshold", type=float, default=0.5)
    args = parser.parse_args(argv)

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


if __name__ == "__main__":
    sys.exit(main())
