"""Configuration and repository hygiene tests."""

from __future__ import annotations

from pathlib import Path

import config


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_config_paths_are_pathlib_paths() -> None:
    assert isinstance(config.ROOT_DIR, Path)
    assert isinstance(config.ASSETS_DIR, Path)
    assert config.ROOT_DIR == PROJECT_ROOT


def test_requirements_are_reproducible() -> None:
    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
    clean_requirements = (PROJECT_ROOT / "requirements_clean.txt").read_text(encoding="utf-8")

    assert "file" + ":///" not in clean_requirements
    assert "scispacy" not in requirements.lower()
    assert "fpdf" not in requirements.lower()
    assert "python-dotenv" in requirements


def test_readme_documents_canonical_run_command() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "streamlit run app.py" in readme
    assert "firebase_key.json" not in readme.lower()


def test_gitignore_protects_local_secrets() -> None:
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".env" in gitignore
    assert "firebase_key.json" in gitignore
    assert "venv/" in gitignore
