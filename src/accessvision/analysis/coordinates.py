"""Coordinate conversion from Gemini box_2d to pixel coordinates."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BoundingBox:
    """Bounding box in pixel coordinates."""
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    @property
    def width(self) -> int:
        """Return width of the bounding box."""
        return self.x_max - self.x_min

    @property
    def height(self) -> int:
        """Return height of the bounding box."""
        return self.y_max - self.y_min


def box_2d_to_pixel(
    box_2d: list[int],
    screenshot_width: int,
    screenshot_height: int,
) -> BoundingBox:
    """Convert Gemini box_2d normalized coordinates to pixel coordinates.

    Gemini returns box_2d as [y_min, x_min, y_max, x_max] in a 1000x1000 normalized grid.

    Args:
        box_2d: Gemini format [y_min, x_min, y_max, x_max] normalized to 1000x1000
        screenshot_width: Width of the screenshot in pixels
        screenshot_height: Height of the screenshot in pixels

    Returns:
        BoundingBox in pixel coordinates

    Example:
        >>> box_2d_to_pixel([200, 300, 400, 500], 1280, 936)
        BoundingBox(x_min=384, y_min=187, x_max=640, y_max=374)
    """
    y_min, x_min, y_max, x_max = box_2d

    pixel_x_min = int((x_min / 1000) * screenshot_width)
    pixel_y_min = int((y_min / 1000) * screenshot_height)
    pixel_x_max = int((x_max / 1000) * screenshot_width)
    pixel_y_max = int((y_max / 1000) * screenshot_height)

    return BoundingBox(
        x_min=pixel_x_min,
        y_min=pixel_y_min,
        x_max=pixel_x_max,
        y_max=pixel_y_max,
    )


def element_bbox_to_pixel(element: dict, screenshot_width: int, screenshot_height: int) -> Optional[BoundingBox]:
    """Convert element map bbox to pixel coordinates.

    Args:
        element: Element from element_map with 'bbox' field
        screenshot_width: Width of the screenshot in pixels
        screenshot_height: Height of the screenshot in pixels

    Returns:
        BoundingBox in pixel coordinates, or None if no bbox
    """
    bbox = element.get("bbox")
    if not bbox:
        return None

    # Element map bboxes are already in pixels (not normalized)
    return BoundingBox(
        x_min=int(bbox.get("x", 0)),
        y_min=int(bbox.get("y", 0)),
        x_max=int(bbox.get("x", 0) + bbox.get("w", 0)),
        y_max=int(bbox.get("y", 0) + bbox.get("h", 0)),
    )
