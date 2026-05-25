"""Text and Markdown report generation."""

from __future__ import annotations

import re


def generate_report(
    math_issues: list[str] | None = None,
    citation_issues: list[str] | None = None,
) -> str:
    """Generate a plain-text feedback report."""
    math_issues = math_issues or ["No issues found."]
    citation_issues = citation_issues or ["No issues found."]

    report = ["ScholarFix AI Feedback Report", "=" * 40, ""]
    report.append("Math Symbol Check:")
    report.extend(f"- {issue}" for issue in math_issues)
    report.append("")
    report.append("Citation Check:")
    report.extend(f"- {issue}" for issue in citation_issues)

    return "\n".join(report)


def inject_inline_issues(
    text: str,
    math_issues: list[str] | None = None,
    citation_issues: list[str] | None = None,
) -> str:
    """Insert simple inline markers for citation and math findings."""
    marked = text

    for issue in math_issues or []:
        match = re.search(r"'([^']+)'", issue)
        if match:
            symbol = match.group(1)
            marked = marked.replace(symbol, f"[[CHECK: {symbol}]]", 1)

    for cite in citation_issues or []:
        match = re.search(r"\[(\d+)\]", cite)
        if match:
            citation_num = match.group(1)
            marked = marked.replace(f"[{citation_num}]", f"[[CHECK: Citation {citation_num}]]", 1)

    return marked


def generate_markdown_report(
    math_issues: list[str] | None = None,
    citation_issues: list[str] | None = None,
    rewritten_text: str | None = None,
) -> str:
    """Generate a Markdown feedback report."""
    math_issues = math_issues or []
    citation_issues = citation_issues or []

    lines = ["# ScholarFix Feedback Report", ""]
    lines.extend(["## Math Symbol Issues"])
    if math_issues:
        lines.extend(f"- {issue}" for issue in math_issues)
    else:
        lines.append("- No math symbol issues found.")

    lines.extend(["", "## Citation Issues"])
    if citation_issues:
        lines.extend(f"- {issue}" for issue in citation_issues)
    else:
        lines.append("- No citation issues found.")

    if rewritten_text:
        lines.extend(["", "## AI Rewritten Section", "```markdown"])
        lines.append(rewritten_text.strip())
        lines.append("```")

    return "\n".join(lines) + "\n"
