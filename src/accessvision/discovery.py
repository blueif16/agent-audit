"""Site discovery via Firecrawl /map endpoint."""

import aiohttp
from accessvision.config import FIRECRAWL_API_KEY


async def discover_pages(root_url: str) -> list[dict]:
    """Discover all pages on a site using Firecrawl /map.

    Args:
        root_url: Root URL to start discovery from

    Returns:
        List of dicts with 'url' and 'title' keys

    Raises:
        ValueError: If FIRECRAWL_API_KEY is not set
        aiohttp.ClientError: If the API request fails
    """
    if not FIRECRAWL_API_KEY:
        raise ValueError("FIRECRAWL_API_KEY not set in environment")

    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "url": root_url
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.firecrawl.dev/v1/map",
            headers=headers,
            json=payload
        ) as response:
            data = await response.json()

            # Firecrawl /map returns {success: true, links: [{url, title}, ...]}
            if not data.get("success"):
                raise ValueError(f"Firecrawl /map failed: {data}")

            links = data.get("links", [])

            # Normalize to our expected format
            return [
                {
                    "url": link.get("url", ""),
                    "title": link.get("title", "")
                }
                for link in links
                if link.get("url")
            ]
