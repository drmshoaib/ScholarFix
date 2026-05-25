"""Central configuration for the RedPen / ScholarFix MVP."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - exercised only in minimal test envs
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False


ROOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ROOT_DIR / "assets"
COMPONENTS_DIR = ROOT_DIR / "components"

load_dotenv(ROOT_DIR / ".env")

APP_NAME = "ScholarFix"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def _env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DEV_MODE = _env_flag("REDPEN_DEV_MODE", default=True)

_firebase_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_key.json")
FIREBASE_CREDENTIALS_PATH = Path(_firebase_path)
if not FIREBASE_CREDENTIALS_PATH.is_absolute():
    FIREBASE_CREDENTIALS_PATH = ROOT_DIR / FIREBASE_CREDENTIALS_PATH
