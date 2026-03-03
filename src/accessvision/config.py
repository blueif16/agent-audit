"""Configuration and environment management with worktree-aware .env loading."""

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
                # First worktree entry is always the main worktree
                return Path(line.split("worktree ", 1)[1])

        # Fallback: if not in a worktree, use current directory
        return Path.cwd()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repo or git not available
        return Path.cwd()


def _load_env():
    """Load environment variables from main worktree .env file."""
    main_worktree = _find_main_worktree()
    env_path = main_worktree / ".env"

    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try .env.example as fallback for documentation
        example_path = main_worktree / ".env.example"
        if example_path.exists():
            load_dotenv(example_path)


# Load environment on module import
_load_env()


# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Model names
GEMINI_FLASH = "gemini-3-flash-preview"
GEMINI_PRO = "gemini-3.1-pro-preview"
NANO_BANANA_PRO = "gemini-3-pro-image"
NANO_BANANA_2 = "gemini-3.1-flash-image"

# Default settings
DEFAULT_N_PAGES = 5

# Validate required keys
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
            f"Please create a .env file in the main worktree with these keys."
        )
