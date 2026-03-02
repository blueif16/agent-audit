"""Configuration management with worktree-aware .env loading."""

import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv


def _get_main_worktree() -> Path:
    """Resolve the main worktree directory via git."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=True
    )
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            return Path(line.split(" ", 1)[1])
    raise RuntimeError("Could not determine main worktree")


def _load_env():
    """Load .env from main worktree if it exists."""
    try:
        main_worktree = _get_main_worktree()
        env_path = main_worktree / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except Exception:
        # Not in a git repo or no worktrees - try local .env
        load_dotenv()


_load_env()


# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment")
if not FIRECRAWL_API_KEY:
    raise ValueError("FIRECRAWL_API_KEY not found in environment")


# Model names
MODEL_FLASH = "gemini-3-flash-preview"
MODEL_PRO_VISION = "gemini-3.1-pro-preview"
MODEL_NANO_BANANA = "gemini-3-pro-image"

# Default settings
DEFAULT_PAGES_COUNT = 5
SCREENSHOT_WIDTH = 1280
SCREENSHOT_HEIGHT = 936
