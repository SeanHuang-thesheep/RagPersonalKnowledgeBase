import argparse
import sys

from .enrich import math_fill_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="把 markdown 中的 ![math] 图用视觉模型转写为线性公式。"
    )
    parser.add_argument("input", help="输入 .md 路径（数学图在 <名>_assets/）")
    parser.add_argument("-o", "--output", help="输出 .md（默认 <名>.math.md）")
    parser.add_argument("--language", default="auto")
    args = parser.parse_args(argv)

    try:
        result = math_fill_markdown(args.input, output_path=args.output, language=args.language)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(
        f"filled: {result.filled} | failed: {result.failed} -> {result.output_path}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
