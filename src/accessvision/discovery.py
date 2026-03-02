"""Site discovery via Firecrawl /map endpoint."""


async def discover_pages(root_url: str) -> list[dict]:
    """
    Discover all pages on a site via Firecrawl /map.

    Returns list of {"url": str, "title": str} dicts.
    Implementation in Slice 2.
    """
    raise NotImplementedError("Slice 2")
