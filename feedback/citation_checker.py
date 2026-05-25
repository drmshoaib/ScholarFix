"""Lightweight citation-format checks."""

from __future__ import annotations

import re


def check_citations(text: str) -> list[str]:
    """Return citation-format observations for uploaded text."""
    bracketed = re.findall(r"\[[0-9]+\]", text)
    latex_cites = re.findall(r"\\cite\{.*?\}", text)
    apa_cites = re.findall(r"\([A-Z][a-z]+(?: et al\.)?, \d{4}\)", text)

    if not (bracketed or latex_cites or apa_cites):
        return ["No citations found."]

    issues = []
    for cite in bracketed:
        issues.append(f"Numeric citation found: {cite} (verify reference list alignment)")
    for cite in latex_cites:
        issues.append(f"LaTeX citation found: {cite} (verify BibTeX key exists)")
    for cite in apa_cites:
        issues.append(f"Possible APA-style citation: {cite} (check BibTeX alignment)")

    return issues
