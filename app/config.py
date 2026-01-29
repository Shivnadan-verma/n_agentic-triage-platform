# AI assisted development
"""
Central configuration – all paths and file names from environment (nothing hardcoded).

Env vars (all optional):
- WORKSPACE_ROOT: absolute path to project root (default: derived from this file)
- DATA_FOLDER: path to data input folder, relative to workspace (default: app/data/input)
- BUGS_FILENAMES: comma-separated bug file names to try (default: bugs.json,bug.json)
- ENGINEERS_FILENAME: engineers JSON file name (default: engineer.json)
- DEFAULT_BUG_FILE: default bug file name when no input (default: bug.json)
"""
import os
from pathlib import Path

# Reference for default workspace: parent of app/ is project root
_APP_DIR = Path(__file__).resolve().parent


def get_workspace_root() -> Path:
    """Project root; overridable via WORKSPACE_ROOT."""
    raw = os.environ.get("WORKSPACE_ROOT", "").strip()
    if raw:
        return Path(raw).resolve()
    return _APP_DIR.parent


def get_data_folder() -> str:
    """Data input folder path (relative to workspace); overridable via DATA_FOLDER."""
    return os.environ.get("DATA_FOLDER", "app/data/input").strip() or "app/data/input"


def get_bugs_filenames() -> list[str]:
    """Bug file names to try (order matters); overridable via BUGS_FILENAMES (comma-separated)."""
    raw = os.environ.get("BUGS_FILENAMES", "bugs.json,bug.json").strip()
    return [n.strip() for n in raw.split(",") if n.strip()] or ["bugs.json", "bug.json"]


def get_engineers_filename() -> str:
    """Engineers JSON file name; overridable via ENGINEERS_FILENAME."""
    return os.environ.get("ENGINEERS_FILENAME", "engineer.json").strip() or "engineer.json"


def get_default_bug_file() -> str:
    """Default bug file when no input; overridable via DEFAULT_BUG_FILE."""
    return os.environ.get("DEFAULT_BUG_FILE", "bug.json").strip() or "bug.json"


def get_data_path(filename: str) -> Path:
    """Absolute path for a file in the data input folder."""
    root = get_workspace_root()
    folder = get_data_folder()
    return root / folder / filename


def get_engineers_path() -> Path:
    """Absolute path for engineers file."""
    return get_data_path(get_engineers_filename())
