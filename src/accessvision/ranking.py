"""LLM-based page ranking for audit prioritization."""

import json
import google.generativeai as genai
from accessvision.config import GOOGLE_API_KEY, GEMINI_FLASH_MODEL
from accessvision.prompts.ranking import build_ranking_prompt


async def rank_pages(pages: list[dict], n: int) -> list[dict]:
    """Rank discovered pages and return top N by audit priority.

    Args:
        pages: List of dicts with 'url' and 'title' keys
        n: Number of top pages to return

    Returns:
        List of top N pages with added 'priority_score' (1-10) and 'reason' fields

    Raises:
        ValueError: If GOOGLE_API_KEY is not set or if response parsing fails
    """
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in environment")

    # Configure the API
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(GEMINI_FLASH_MODEL)

    # Build prompt
    prompt = build_ranking_prompt(pages, n)

    # Generate response
    response = await model.generate_content_async(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.3,  # Lower temperature for more consistent ranking
            response_mime_type="application/json"
        )
    )

    # Parse JSON response
    try:
        ranked_pages = json.loads(response.text)

        # Validate structure
        if not isinstance(ranked_pages, list):
            raise ValueError("Response is not a list")

        for page in ranked_pages:
            if not all(k in page for k in ["url", "title", "priority_score", "reason"]):
                raise ValueError(f"Page missing required fields: {page}")

            # Validate priority_score range
            score = page["priority_score"]
            if not isinstance(score, int) or not (1 <= score <= 10):
                raise ValueError(f"Invalid priority_score: {score}")

        return ranked_pages[:n]  # Ensure we return at most N pages

    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to parse ranking response: {e}\nResponse: {response.text}")
