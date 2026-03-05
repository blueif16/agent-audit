"""Screenshot annotation with violation bounding boxes."""

from io import BytesIO
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from accessvision.analysis.coordinates import BoundingBox, box_2d_to_pixel
from accessvision.models import SeverityLevel, Violation

# Severity colors (RGB)
SEVERITY_COLORS = {
    SeverityLevel.CRITICAL: (255, 0, 0),      # Red
    SeverityLevel.SERIOUS: (255, 140, 0),     # Orange
    SeverityLevel.MODERATE: (255, 215, 0),    # Yellow
    SeverityLevel.MINOR: (65, 105, 225),      # Blue (RoyalBlue)
}

# Annotation settings
BORDER_WIDTH = 3
BADGE_SIZE = 24
BADGE_MARGIN = 5


def annotate_screenshot(
    screenshot: bytes,
    violations: list[Violation],
    screenshot_width: int = 1280,
    screenshot_height: int = 936,
) -> bytes:
    """Draw colored bounding boxes and numbered badges on a screenshot.

    Args:
        screenshot: PNG bytes of the original screenshot
        violations: List of Violation objects to annotate
        screenshot_width: Width of screenshot in pixels
        screenshot_height: Height of screenshot in pixels

    Returns:
        PNG bytes with annotations drawn
    """
    # Load image from bytes
    img = Image.open(BytesIO(screenshot)).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        badge_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
    except Exception:
        font = ImageFont.load_default()
        badge_font = font

    # Sort violations by severity (Critical first) for consistent numbering
    sorted_violations = sorted(violations, key=lambda v: -v.severity.value)

    for idx, violation in enumerate(sorted_violations, start=1):
        # Get bounding box
        bbox = _get_violation_bbox(violation, screenshot_width, screenshot_height)
        if bbox is None:
            continue

        # Get color for severity
        color = SEVERITY_COLORS.get(violation.severity, (255, 255, 255))

        # Draw border rectangle
        draw.rectangle(
            [bbox.x_min, bbox.y_min, bbox.x_max, bbox.y_max],
            outline=color,
            width=BORDER_WIDTH,
        )

        # Draw numbered badge in top-left corner
        _draw_badge(draw, idx, bbox.x_min, bbox.y_min, color, badge_font)

    # Convert back to PNG bytes
    output = BytesIO()
    img.convert("RGB").save(output, format="PNG")
    return output.getvalue()


def _get_violation_bbox(
    violation: Violation,
    width: int,
    height: int,
) -> Optional[BoundingBox]:
    """Get pixel bounding box for a violation.

    Args:
        violation: The violation to get bbox for
        width: Screenshot width
        height: Screenshot height

    Returns:
        BoundingBox in pixels, or None if no bbox available
    """
    if violation.box_2d:
        return box_2d_to_pixel(violation.box_2d, width, height)

    # Fall back to element map if element_index is available
    # This would require access to element_map - return None for now
    return None


def _draw_badge(
    draw: ImageDraw.ImageDraw,
    number: int,
    x: int,
    y: int,
    color: tuple[int, int, int],
    font: ImageFont.ImageFont,
) -> None:
    """Draw a numbered badge at the specified position.

    Args:
        draw: PIL ImageDraw object
        number: Number to display in badge
        x: X position (left edge of badge)
        y: Y position (top edge of badge)
        color: RGB color tuple for the badge
        font: Font to use for the number
    """
    # Badge background (white with colored border)
    badge_x = x + BADGE_MARGIN
    badge_y = y + BADGE_MARGIN
    badge_right = badge_x + BADGE_SIZE
    badge_bottom = badge_y + BADGE_SIZE

    # Draw badge background (white)
    draw.ellipse(
        [badge_x, badge_y, badge_right, badge_bottom],
        fill=(255, 255, 255),
        outline=color,
        width=2,
    )

    # Draw number centered in badge
    text = str(number)
    # Estimate text width (approximate for default font)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except Exception:
        text_width = 8 * len(text)
        text_height = 12

    text_x = badge_x + (BADGE_SIZE - text_width) // 2
    text_y = badge_y + (BADGE_SIZE - text_height) // 2

    draw.text((text_x, text_y), text, fill=color, font=font)
