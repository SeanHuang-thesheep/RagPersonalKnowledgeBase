import argparse
import sys

from .enrich import caption_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="为 Markdown 中的图片生成 caption 填入 alt（OpenAI 视觉）。"
    )
    parser.add_argument("input", help="输入 .md 路径（其图片在 <名>_assets/）")
    parser.add_argument("-o", "--output", help="输出 .md（默认 <名>.captioned.md）")
    parser.add_argument("--language", default="auto", help="caption 语言；auto=随周边文字")
    parser.add_argument("--min-side", type=int, default=64, help="过滤：最小边像素")
    args = parser.parse_args(argv)

    try:
        result = caption_markdown(
            args.input,
            output_path=args.output,
            language=args.language,
            min_side=args.min_side,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(
        f"captioned: {result.captioned} | skipped: {result.skipped} | "
        f"failed: {result.failed} -> {result.output_path}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
