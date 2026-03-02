"""CLI entrypoint for AccessVision."""

import argparse
import asyncio
import sys


async def main_async(args):
    """Main async execution flow."""
    print(f"AccessVision: Auditing {args.url}", file=sys.stderr)
    print(f"Pages to audit: {args.pages}", file=sys.stderr)
    print(f"Output: {args.output}", file=sys.stderr)
    # Pipeline orchestration will be wired here in Slice 6


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="AccessVision - AI-powered visual WCAG accessibility auditing"
    )
    parser.add_argument("url", help="Root URL to audit")
    parser.add_argument(
        "--pages",
        type=int,
        default=5,
        help="Number of pages to audit (default: 5)"
    )
    parser.add_argument(
        "--output",
        default="report.html",
        help="Output report path (default: report.html)"
    )

    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
