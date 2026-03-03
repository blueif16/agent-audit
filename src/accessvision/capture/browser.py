"""Playwright-based browser automation for screenshots and accessibility data."""

import asyncio
from typing import Dict, Any, List
from playwright.async_api import async_playwright, Page


# Viewport dimensions matching Computer Use model
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 936


async def capture_page(url: str) -> Dict[str, Any]:
    """Capture screenshot, axe-core results, element map, and a11y tree.

    Args:
        url: Page URL to capture

    Returns:
        Dict with 'screenshot', 'axe_results', 'element_map', 'accessibility_tree'
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': VIEWPORT_WIDTH, 'height': VIEWPORT_HEIGHT})

        try:
            # Navigate and wait for network idle
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Capture screenshot
            screenshot = await page.screenshot(full_page=True, type='png')

            # Inject and run axe-core
            axe_results = await _run_axe_scan(page)

            # Extract element map
            element_map = await _extract_element_map(page)

            # Get accessibility tree
            a11y_tree = await page.accessibility.snapshot(interesting_only=True)

            return {
                'screenshot': screenshot,
                'axe_results': axe_results,
                'element_map': element_map,
                'accessibility_tree': a11y_tree or {}
            }
        finally:
            await browser.close()


async def _run_axe_scan(page: Page) -> Dict[str, Any]:
    """Inject axe-core and run WCAG 2.2 AA scan."""
    # Inject axe-core from CDN
    await page.add_script_tag(url='https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js')

    # Run scan targeting WCAG 2.2 AA
    results = await page.evaluate("""
        () => {
            return axe.run(document, {
                runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag22aa'] }
            });
        }
    """)

    return results


async def _extract_element_map(page: Page) -> List[Dict[str, Any]]:
    """Extract interactive/semantic elements with bounding boxes."""
    element_map = await page.evaluate("""
        () => {
            const selectors = 'img, a, button, input, select, textarea, [role], h1, h2, h3, h4, h5, h6, label, nav, form, [tabindex]';
            const elements = document.querySelectorAll(selectors);
            return [...elements].map((el, i) => {
                const rect = el.getBoundingClientRect();
                return {
                    index: i,
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role'),
                    text: (el.textContent || '').trim().slice(0, 120),
                    alt: el.getAttribute('alt'),
                    aria_label: el.getAttribute('aria-label'),
                    aria_describedby: el.getAttribute('aria-describedby'),
                    href: el.getAttribute('href'),
                    type: el.getAttribute('type'),
                    name: el.getAttribute('name'),
                    placeholder: el.getAttribute('placeholder'),
                    bbox: {
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height)
                    },
                    visible: rect.width > 0 && rect.height > 0,
                    focusable: el.tabIndex >= 0
                };
            }).filter(e => e.visible);
        }
    """)

    return element_map
