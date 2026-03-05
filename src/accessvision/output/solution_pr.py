"""Solution PR generation using Gemini."""

from typing import Optional

from google import genai

from accessvision import config
from accessvision.models import PageCapture, Violation
from accessvision.prompts.solution_pr import build_solution_pr_prompt


async def generate_solution_pr(
    page_capture: PageCapture,
    violations: list[Violation],
) -> str:
    """Generate markdown fix document for a page.

    Args:
        page_capture: The captured page data
        violations: List of detected violations

    Returns:
        Markdown document with code fixes

    Raises:
        ValueError: If Gemini API key is not configured
    """
    api_key = config.GOOGLE_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not configured")

    client = genai.Client(api_key=api_key)

    # Build prompt
    prompt = build_solution_pr_prompt(
        page_url=page_capture.url,
        page_title=page_capture.title,
        priority_score=page_capture.priority_score,
        violations=violations,
        axe_results=page_capture.axe_results,
        markdown_description=page_capture.markdown_description,
        element_map=page_capture.element_map,
    )

    # Call Gemini Flash
    response = client.models.generate_content(
        model=config.GEMINI_FLASH_MODEL,
        contents=prompt,
    )

    return response.text or ""
