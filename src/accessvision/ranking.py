"""LLM-based page ranking for audit prioritization."""


async def rank_pages(pages: list[dict], n: int) -> list[dict]:
    """
    Use Gemini Flash to rank pages by accessibility audit priority.

    Returns top N pages with added fields: priority_score (1-10), reason.
    Implementation in Slice 2.
    """
    raise NotImplementedError("Slice 2")
