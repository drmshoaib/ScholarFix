"""LaTeX text extraction."""

from __future__ import annotations

from pylatexenc.latex2text import LatexNodes2Text


def extract_tex_text(file) -> str:
    """Extract plain text from a LaTeX upload."""
    tex = file.read().decode("utf-8")
    return LatexNodes2Text().latex_to_text(tex)
