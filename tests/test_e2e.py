"""End-to-end CLI integration tests."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.mark.integration
class TestE2E:
    """End-to-end tests for the full CLI pipeline."""

    @pytest.fixture
    def output_file(self):
        """Create a temporary output file."""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            yield f.name
        # Cleanup
        if os.path.exists(f.name):
            os.remove(f.name)

    def test_cli_help(self):
        """Test CLI help output."""
        result = subprocess.run(
            ["python", "-m", "accessvision", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "AccessVision" in result.stdout
        assert "--pages" in result.stdout
        assert "--output" in result.stdout

    def test_cli_requires_url(self):
        """Test CLI requires a URL argument."""
        result = subprocess.run(
            ["python", "-m", "accessvision"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2  # argparse error
        assert "error: the following arguments are required: url" in result.stderr

    @pytest.mark.integration
    def test_cli_full_pipeline(self):
        """Test full CLI pipeline with minimal pages.

        This is an integration test that requires API keys.
        Skip with: pytest -m "not integration"
        """
        # Skip if no API keys
        if not os.environ.get("GOOGLE_API_KEY") or not os.environ.get("FIRECRAWL_API_KEY"):
            pytest.skip("API keys not configured")

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [
                    "python", "-m", "accessvision",
                    "https://example.com",
                    "--pages", "1",
                    "--output", output_path,
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
            )

            # Check it ran without errors
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Check output file was created
            assert os.path.exists(output_path), "Output file not created"

            # Check HTML content
            html = Path(output_path).read_text()
            assert "AccessVision" in html
            assert "example.com" in html

            # Check progress output to stderr
            assert "Phase" in result.stderr
            assert "complete" in result.stderr.lower()

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
