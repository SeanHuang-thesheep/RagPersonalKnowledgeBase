import argparse
import os
import sys

from .convert import convert_to_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="将 docx/pptx 转换为 Markdown。"
    )
    parser.add_argument("input", help="输入 .docx 或 .pptx 路径")
    parser.add_argument("-o", "--output", help="输出 .md 文件（默认打印到 stdout）")
    args = parser.parse_args(argv)

    if args.output:
        asset_dir = os.path.splitext(args.output)[0] + "_assets"
    else:
        asset_dir = "output_assets"

    try:
        result = convert_to_markdown(args.input, asset_dir=asset_dir)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    ext = os.path.splitext(args.input)[1].lower().lstrip(".")
    print(
        f"Format: {ext} | units: {result.unit_count} | images: {result.image_count}",
        file=sys.stderr,
    )

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


if __name__ == "__main__":
    sys.exit(main())
