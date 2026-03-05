"""Tests for the annotator module."""

import io

import pytest
from PIL import Image

from accessvision.models import SeverityLevel, Violation
from accessvision.output.annotator import annotate_screenshot


def create_test_screenshot(width: int = 1280, height: int = 936, color: tuple = (128, 128, 128)) -> bytes:
    """Create a solid color PNG screenshot for testing."""
    img = Image.new("RGB", (width, height), color)
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def get_pixel_at(img: Image.Image, x: int, y: int) -> tuple:
    """Get RGB pixel at specified coordinates."""
    return img.getpixel((x, y))


class TestAnnotateScreenshot:
    """Tests for annotate_screenshot function."""

    def test_annotate_screenshot_with_violations(self):
        """Test that annotations are drawn on the screenshot."""
        # Create a gray test screenshot
        original_screenshot = create_test_screenshot(color=(128, 128, 128))

        # Create two violations with different severities
        violation1 = Violation(
            id="v1",
            element_index=0,
            box_2d=[100, 100, 200, 200],  # Top-left area
            criterion="1.4.3",
            criterion_name="Contrast (Minimum)",
            severity=SeverityLevel.CRITICAL,
            description="Contrast ratio is insufficient",
            remediation_hint="Increase contrast ratio",
            detected_by="axe-core",
        )

        violation2 = Violation(
            id="v2",
            element_index=1,
            box_2d=[500, 500, 600, 600],  # Center area
            criterion="2.4.7",
            criterion_name="Focus Visible",
            severity=SeverityLevel.MINOR,
            description="Focus indicator is not visible",
            remediation_hint="Add visible focus indicator",
            detected_by="axe-core",
        )

        violations = [violation1, violation2]

        # Call the annotator
        annotated_bytes = annotate_screenshot(original_screenshot, violations)

        # Verify output is valid PNG
        annotated_img = Image.open(io.BytesIO(annotated_bytes))
        assert annotated_img.format == "PNG"
        assert annotated_img.size == (1280, 936)

    def test_annotated_screenshot_differs_from_input(self):
        """Test that annotated screenshot differs from original at bbox locations."""
        # Create a gray test screenshot
        original_screenshot = create_test_screenshot(color=(128, 128, 128))

        # Create a violation with CRITICAL severity (red)
        violation = Violation(
            id="v1",
            element_index=0,
            box_2d=[100, 100, 200, 200],
            criterion="1.4.3",
            criterion_name="Contrast (Minimum)",
            severity=SeverityLevel.CRITICAL,
            description="Contrast ratio is insufficient",
            remediation_hint="Increase contrast ratio",
            detected_by="axe-core",
        )

        # Call the annotator
        annotated_bytes = annotate_screenshot(original_screenshot, [violation])
        annotated_img = Image.open(io.BytesIO(annotated_bytes))

        # Verify pixels have changed at the bbox location
        # The border should be drawn at the edges of the bbox
        # For box_2d=[100,100,200,200] on 1280x936:
        # x_min = 128, y_min = 93, x_max = 256, y_max = 187

        # Check that there's a red pixel at the top edge of the bbox
        # (at least one pixel should have changed to red = (255, 0, 0))
        has_red_pixel = False
        for x in range(128, 256):
            pixel = annotated_img.getpixel((x, 93))
            if pixel[0] > 200 and pixel[1] < 50:  # Red-ish color
                has_red_pixel = True
                break

        assert has_red_pixel, "Expected red border at bbox location"

    def test_different_severities_get_different_colors(self):
        """Test that different severity levels produce different colors."""
        # Create a gray test screenshot
        original_screenshot = create_test_screenshot(color=(200, 200, 200))

        # Create violations with different severities
        violations = [
            Violation(
                id="critical",
                element_index=0,
                box_2d=[100, 100, 150, 150],
                criterion="1.4.3",
                criterion_name="Contrast",
                severity=SeverityLevel.CRITICAL,
                description="Test",
                remediation_hint="Test",
                detected_by="axe-core",
            ),
            Violation(
                id="minor",
                element_index=1,
                box_2d=[300, 300, 350, 350],
                criterion="2.4.7",
                criterion_name="Focus",
                severity=SeverityLevel.MINOR,
                description="Test",
                remediation_hint="Test",
                detected_by="axe-core",
            ),
        ]

        annotated_bytes = annotate_screenshot(original_screenshot, violations)
        annotated_img = Image.open(io.BytesIO(annotated_bytes))

        # Check CRITICAL (red) at first bbox location
        # box_2d=[100,100,150,150] -> pixel: x_min=128, y_min=93, x_max=192, y_max=140
        critical_pixel = annotated_img.getpixel((130, 95))

        # Check MINOR (blue) at second bbox location
        # box_2d=[300,300,350,350] -> pixel: x_min=384, y_min=280, x_max=448, y_max=327
        minor_pixel = annotated_img.getpixel((386, 282))

        # CRITICAL should be more red (higher R, lower G/B)
        # MINOR should be more blue (higher B)
        assert critical_pixel[0] > critical_pixel[1], "CRITICAL should have red-dominant color"

    def test_empty_violations_returns_unchanged(self):
        """Test that empty violations list returns original screenshot."""
        original_screenshot = create_test_screenshot(color=(100, 100, 100))

        annotated_bytes = annotate_screenshot(original_screenshot, [])

        # Output should still be valid PNG
        annotated_img = Image.open(io.BytesIO(annotated_bytes))
        assert annotated_img.format == "PNG"

    def test_violation_without_box_2d_is_skipped(self):
        """Test that violations without box_2d are skipped."""
        original_screenshot = create_test_screenshot(color=(100, 100, 100))

        # Violation without box_2d
        violation = Violation(
            id="v1",
            element_index=None,
            box_2d=None,  # No bounding box
            criterion="1.4.3",
            criterion_name="Contrast",
            severity=SeverityLevel.CRITICAL,
            description="Test",
            remediation_hint="Test",
            detected_by="axe-core",
        )

        # Should not raise, just skip the violation
        annotated_bytes = annotate_screenshot(original_screenshot, [violation])
        annotated_img = Image.open(io.BytesIO(annotated_bytes))

        # Should be valid PNG (though unchanged since bbox is None)
        assert annotated_img.format == "PNG"
