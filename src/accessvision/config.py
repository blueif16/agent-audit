"""Configuration management with worktree-aware .env loading."""

import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv


def _find_main_worktree() -> Path:
    """Find the main worktree root by parsing git worktree list."""
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )

        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                worktree_path = line.split("worktree ", 1)[1]
                # Check if this is the main worktree (has .git directory, not file)
                git_path = Path(worktree_path) / ".git"
                if git_path.is_dir():
                    return Path(worktree_path)

        # Fallback: if no main worktree found, use current directory
        return Path.cwd()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not in a git repo or git not available
        return Path.cwd()


# Load environment from main worktree
_main_worktree = _find_main_worktree()
_env_path = _main_worktree / ".env"

if _env_path.exists():
    load_dotenv(_env_path)
else:
    # Try loading from current directory as fallback
    load_dotenv()


# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Model names
GEMINI_FLASH_MODEL = "gemini-3-flash-preview"
GEMINI_PRO_MODEL = "gemini-3.1-pro-preview"
NANO_BANANA_MODEL = "gemini-3-pro-image"

# Default settings
DEFAULT_N_PAGES = 5
SCREENSHOT_WIDTH = 1280
SCREENSHOT_HEIGHT = 936


def validate_config():
    """Raise an error if required API keys are missing."""
    missing = []
    if not GOOGLE_API_KEY:
        missing.append("GOOGLE_API_KEY")
    if not FIRECRAWL_API_KEY:
        missing.append("FIRECRAWL_API_KEY")

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please set them in {_env_path} or your environment."
        )
