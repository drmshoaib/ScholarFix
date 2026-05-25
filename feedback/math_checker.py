"""Lightweight mathematical-notation checks."""

from __future__ import annotations

import re

MATH_PATTERN = re.compile(
    r"(\$[^$]+\$|\\\(.+?\\\)|\\\[.+?\\\]|\\begin\{equation\}.+?\\end\{equation\}|"
    r"\b[A-Za-z]\([^)]+\)|\b[A-Za-z]_[A-Za-z0-9]+\b)",
    flags=re.DOTALL,
)


def check_math_definitions(text: str) -> list[str]:
    """Return lightweight observations about mathematical notation."""
    equations = MATH_PATTERN.findall(text)
    if not equations:
        return ["No math expressions detected."]

    definition_markers = ("where", "defined as", "denote", "denotes", "let ")
    if not any(marker in text.lower() for marker in definition_markers):
        return [
            "Mathematical notation detected; verify variables are defined near first use."
        ]

    return ["Math expressions detected; no obvious definition issue found."]
