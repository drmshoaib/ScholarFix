"""Shared pytest fixtures."""

from __future__ import annotations

from io import BytesIO

import pytest


@pytest.fixture
def manuscript_text() -> str:
    """Small synthetic manuscript excerpt for deterministic tests."""
    return (
        "Let R(t) denote reviewer pressure. Prior work [1] shows that clarity matters. "
        "We define x_i as the notation quality score."
    )


@pytest.fixture
def tex_upload() -> BytesIO:
    """LaTeX-like upload fixture."""
    return BytesIO(
        br"""
        \section{Abstract}
        We study clarity in academic writing \cite{smith2024}.
        Let $x_i$ denote a notation score.
        """
    )
