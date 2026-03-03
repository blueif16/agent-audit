"""Prompt for LLM-based page ranking."""

RANKING_PROMPT = """You are an accessibility audit prioritization expert. Given a list of pages from a website, rank them by audit priority and return the top N most important pages to audit.

**Ranking Criteria:**

HIGH PRIORITY (scores 8-10):
- User-critical flows: login, signup, checkout, account settings, password reset
- High-traffic public pages: home page, main product/service pages, pricing
- Pages with heavy interaction: dashboards, search results, filters, configurators
- Onboarding flows and getting started pages
- Forms and data entry pages

MEDIUM PRIORITY (scores 5-7):
- Content pages with some interaction: FAQ with accordions, documentation with navigation
- Contact and support pages with forms
- Product listing and category pages
- User profile and settings pages

LOW PRIORITY (scores 1-4):
- Blog posts (usually templated, low interaction)
- Legal pages: terms of service, privacy policy (mostly static text)
- Deep-nested pages unlikely to receive direct traffic
- Duplicate or variant pages: pagination, tag archives, date archives
- About us, company history, press releases

**Instructions:**
1. Analyze each page's URL path and title
2. Assign a priority_score from 1-10 based on the criteria above
3. Provide a brief reason (1 sentence) explaining the score
4. Return EXACTLY {n} pages with the highest scores
5. If there are fewer than {n} pages total, return all of them

**Input Pages:**
{pages_json}

**Output Format (JSON):**
Return a JSON array with exactly {n} objects (or fewer if input has fewer pages), each with:
- url: string
- title: string
- priority_score: integer (1-10)
- reason: string (brief explanation)

Sort by priority_score descending. Return ONLY the JSON array, no other text.
"""


def build_ranking_prompt(pages: list[dict], n: int) -> str:
    """Build the ranking prompt with pages and N parameter.

    Args:
        pages: List of dicts with 'url' and 'title' keys
        n: Number of top pages to return

    Returns:
        Formatted prompt string
    """
    import json
    pages_json = json.dumps(pages, indent=2)
    return RANKING_PROMPT.format(pages_json=pages_json, n=n)
