"""CLI entrypoint for AccessVision."""

import argparse
import asyncio
import sys


async def run_audit(url: str, pages: int, output: str):
    """Run the complete accessibility audit pipeline."""
    # TODO: Wire up full pipeline in Slice 6
    print(f"Auditing {url} (top {pages} pages) → {output}")
    print("Pipeline not yet implemented.")


def main():
    """Parse arguments and run the audit."""
    parser = argparse.ArgumentParser(
        description="AccessVision - AI-powered visual WCAG accessibility auditing"
    )
    parser.add_argument("url", help="Root URL to audit")
    parser.add_argument(
        "--pages", "-n",
        type=int,
        default=5,
        help="Number of top pages to audit (default: 5)"
    )
    parser.add_argument(
        "--output", "-o",
        default="report.html",
        help="Output report path (default: report.html)"
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_audit(args.url, args.pages, args.output))
    except KeyboardInterrupt:
        print("\nAudit cancelled.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
