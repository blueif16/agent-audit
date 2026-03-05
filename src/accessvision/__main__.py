"""CLI entrypoint for AccessVision."""

import argparse
import asyncio
import sys
import time
from pathlib import Path

from google import genai

from accessvision import config
from accessvision.models import PageAudit, SeverityLevel, Violation
from accessvision.discovery import discover_pages
from accessvision.ranking import rank_pages
from accessvision.capture.pipeline import capture_pages
from accessvision.analysis.vision import analyze_page_vision
from accessvision.analysis.merge import merge_violations
from accessvision.output.annotator import annotate_screenshot
from accessvision.output.solution_pr import generate_solution_pr
from accessvision.report.builder import build_report


async def run_audit(url: str, pages: int, output: str):
    """Run the complete accessibility audit pipeline."""
    start_time = time.time()
    phase_start = start_time

    print(f"AccessVision: Auditing {url}", file=sys.stderr)
    print(f"Pages to audit: {pages}", file=sys.stderr)
    print(f"Output: {output}", file=sys.stderr)
    print("-" * 50, file=sys.stderr)

    # Validate config
    config.validate_config()

    # Initialize Gemini client
    client = genai.Client(api_key=config.GOOGLE_API_KEY)

    # Phase 1: Discovery
    print("[Phase 1/5] Discovering pages...", file=sys.stderr)
    discovered = await discover_pages(url)
    print(f"  Found {len(discovered)} pages", file=sys.stderr)
    phase1_time = time.time() - phase_start
    print(f"  Completed in {phase1_time:.1f}s", file=sys.stderr)
    phase_start = time.time()

    # Phase 2: Ranking
    print("\n[Phase 2/5] Ranking pages by priority...", file=sys.stderr)
    ranked = await rank_pages(discovered, pages)
    print(f"  Selected top {len(ranked)} pages", file=sys.stderr)
    phase2_time = time.time() - phase_start
    print(f"  Completed in {phase2_time:.1f}s", file=sys.stderr)
    phase_start = time.time()

    # Phase 3: Capture
    print("\n[Phase 3/5] Capturing pages (screenshots, axe-core)...", file=sys.stderr)
    captures = await capture_pages(ranked)
    print(f"  Captured {len(captures)} pages", file=sys.stderr)
    phase3_time = time.time() - phase_start
    print(f"  Completed in {phase3_time:.1f}s", file=sys.stderr)
    phase_start = time.time()

    # Phase 4: Analysis + Output generation (parallel per page)
    print("\n[Phase 4/5] Analyzing violations & generating fixes...", file=sys.stderr)
    audits: list[PageAudit] = []

    semaphore = asyncio.Semaphore(3)  # Limit parallel API calls

    async def process_page(idx: int, capture):
        async with semaphore:
            # Vision analysis
            vision_violations = await analyze_page_vision(capture, client)

            # Extract axe-core violations
            axe_violations = _extract_axe_violations(capture.axe_results)

            # Merge violations
            violations = merge_violations(vision_violations, axe_violations)

            # Annotate screenshot
            annotated = annotate_screenshot(
                capture.screenshot,
                violations,
                config.SCREENSHOT_WIDTH,
                config.SCREENSHOT_HEIGHT,
            )

            # Generate solution PR
            solution = await generate_solution_pr(capture, violations)

            return PageAudit(
                url=capture.url,
                title=capture.title,
                priority_score=capture.priority_score,
                violations=violations,
                annotated_screenshot=annotated,
                solution_pr=solution,
            )

    tasks = [process_page(idx, cap) for idx, cap in enumerate(captures)]
    audits = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions
    valid_audits = [a for a in audits if isinstance(a, PageAudit)]
    errors = [a for a in audits if not isinstance(a, PageAudit)]

    if errors:
        print(f"  Warning: {len(errors)} pages failed to process", file=sys.stderr)

    print(f"  Processed {len(valid_audits)} pages", file=sys.stderr)
    phase4_time = time.time() - phase_start
    print(f"  Completed in {phase4_time:.1f}s", file=sys.stderr)
    phase_start = time.time()

    # Phase 5: Report generation
    print("\n[Phase 5/5] Generating HTML report...", file=sys.stderr)
    html = build_report(valid_audits)
    output_path = Path(output)
    output_path.write_text(html)
    print(f"  Saved to {output}", file=sys.stderr)
    phase5_time = time.time() - phase_start
    print(f"  Completed in {phase5_time:.1f}s", file=sys.stderr)

    # Summary
    total_time = time.time() - start_time
    total_violations = sum(len(a.violations) for a in valid_audits)
    print("\n" + "=" * 50, file=sys.stderr)
    print(f"Audit complete!", file=sys.stderr)
    print(f"  Pages: {len(valid_audits)}", file=sys.stderr)
    print(f"  Violations: {total_violations}", file=sys.stderr)
    print(f"  Total time: {total_time:.1f}s", file=sys.stderr)
    print("=" * 50, file=sys.stderr)


def _extract_axe_violations(axe_results: dict) -> list[Violation]:
    """Extract violations from axe-core results."""
    violations = []

    if not axe_results:
        return violations

    # Handle different axe result formats
    passes = axe_results.get("passes", [])
    violations_list = axe_results.get("violations", [])

    # Only process actual violations (not passes)
    for v in violations_list:
        # Map axe impact to our severity
        impact = v.get("impact", "minor")
        severity_map = {
            "critical": SeverityLevel.CRITICAL,
            "serious": SeverityLevel.SERIOUS,
            "moderate": SeverityLevel.MODERATE,
            "minor": SeverityLevel.MINOR,
        }
        severity = severity_map.get(impact.lower(), SeverityLevel.MINOR)

        violation = Violation(
            id=v.get("id", ""),
            element_index=None,
            box_2d=None,  # Axe doesn't provide bbox in our format
            criterion=v.get("id", ""),
            criterion_name=v.get("description", "")[:100],
            severity=severity,
            description=v.get("description", ""),
            remediation_hint=v.get("helpUrl", ""),
            detected_by="axe-core",
        )
        violations.append(violation)

    return violations


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="AccessVision - AI-powered visual WCAG accessibility auditing"
    )
    parser.add_argument("url", help="Root URL to audit")
    parser.add_argument(
        "--pages", "-n",
        type=int,
        default=5,
        help="Number of pages to audit (default: 5)"
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
