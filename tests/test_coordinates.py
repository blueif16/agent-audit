"""Tests for coordinate conversion."""

import pytest
from accessvision.analysis.coordinates import box_2d_to_pixel, element_bbox_to_pixel, BoundingBox


class TestBox2DToPixel:
    """Tests for box_2d_to_pixel conversion."""

    def test_center_box(self):
        """Test converting a center box on 1280x936 screenshot."""
        # box_2d = [y_min, x_min, y_max, x_max]
        # Center of image would be ~500,500 for x and y
        box_2d = [500, 500, 600, 600]

        result = box_2d_to_pixel(box_2d, 1280, 936)

        assert result.x_min == 640  # (500/1000) * 1280
        assert result.y_min == 468  # (500/1000) * 936
        assert result.x_max == 768  # (600/1000) * 1280
        assert result.y_max == 561  # int(600/1000 * 936) = int(561.6) = 561

    def test_top_left_corner(self):
        """Test converting a box at top-left corner."""
        box_2d = [0, 0, 100, 100]

        result = box_2d_to_pixel(box_2d, 1280, 936)

        assert result.x_min == 0
        assert result.y_min == 0
        assert result.x_max == 128  # int(100/1000 * 1280) = 128
        assert result.y_max == 93   # int(100/1000 * 936) = int(93.6) = 93

    def test_bottom_right_corner(self):
        """Test converting a box at bottom-right corner."""
        box_2d = [900, 900, 1000, 1000]

        result = box_2d_to_pixel(box_2d, 1280, 936)

        assert result.x_min == 1152
        assert result.y_min == 842
        assert result.x_max == 1280
        assert result.y_max == 936

    def test_full_image(self):
        """Test converting a box covering the full image."""
        box_2d = [0, 0, 1000, 1000]

        result = box_2d_to_pixel(box_2d, 1280, 936)

        assert result.x_min == 0
        assert result.y_min == 0
        assert result.x_max == 1280
        assert result.y_max == 936

    def test_known_values_from_flow(self):
        """Test known conversion values from FLOW.md example."""
        # Example from FLOW.md: [780, 350, 830, 550]
        box_2d = [780, 350, 830, 550]

        result = box_2d_to_pixel(box_2d, 1280, 936)

        # y_min = (780/1000) * 936 = 730.68 -> 730
        # x_min = (350/1000) * 1280 = 448
        # y_max = (830/1000) * 936 = 776.88 -> 776
        # x_max = (550/1000) * 1280 = 704
        assert result.y_min == 730
        assert result.x_min == 448
        assert result.y_max == 776
        assert result.x_max == 704


class TestElementBboxToPixel:
    """Tests for element_bbox_to_pixel conversion."""

    def test_element_with_bbox(self):
        """Test converting element with bbox."""
        element = {
            "bbox": {"x": 100, "y": 200, "w": 300, "h": 50}
        }

        result = element_bbox_to_pixel(element, 1280, 936)

        assert result == BoundingBox(x_min=100, y_min=200, x_max=400, y_max=250)

    def test_element_without_bbox(self):
        """Test element without bbox returns None."""
        element = {"tag": "div", "text": "Hello"}

        result = element_bbox_to_pixel(element, 1280, 936)

        assert result is None

    def test_element_with_empty_bbox(self):
        """Test element with empty bbox returns None."""
        element = {"bbox": {}}

        result = element_bbox_to_pixel(element, 1280, 936)

        assert result is None


class TestBoundingBox:
    """Tests for BoundingBox dataclass."""

    def test_width_calculation(self):
        """Test width property."""
        bbox = BoundingBox(x_min=100, y_min=100, x_max=400, y_max=200)

        assert bbox.width == 300

    def test_height_calculation(self):
        """Test height property."""
        bbox = BoundingBox(x_min=100, y_min=100, x_max=400, y_max=200)

        assert bbox.height == 100
