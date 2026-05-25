"""HTML diff rendering helpers."""

from __future__ import annotations

import difflib
from html import escape


def diff_highlight(original: str, rewritten: str) -> str:
    """Return HTML showing token-level insertions and deletions."""
    diff = difflib.ndiff(original.split(), rewritten.split())
    result = []

    for token in diff:
        safe_token = escape(token[2:])
        if token.startswith("- "):
            result.append(
                "<span style='color:#9f1239;background:#ffe4e6;padding:1px 3px;'>"
                f"- {safe_token}</span>"
            )
        elif token.startswith("+ "):
            result.append(
                "<span style='color:#166534;background:#dcfce7;padding:1px 3px;'>"
                f"+ {safe_token}</span>"
            )
        elif token.startswith("  "):
            result.append(safe_token)

    return " ".join(result)
