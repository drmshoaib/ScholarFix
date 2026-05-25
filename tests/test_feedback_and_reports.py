"""Tests for feedback checks, diff rendering, and report helpers."""

from __future__ import annotations

from feedback.citation_checker import check_citations
from feedback.math_checker import check_math_definitions
from reports.report_generator import (
    generate_markdown_report,
    generate_report,
    inject_inline_issues,
)
from utils.diff_utils import diff_highlight


def test_citation_checker_detects_common_patterns(manuscript_text: str) -> None:
    issues = check_citations(manuscript_text + " See \\cite{doe2025}.")

    assert any("Numeric citation" in issue for issue in issues)
    assert any("LaTeX citation" in issue for issue in issues)


def test_citation_checker_reports_absence() -> None:
    assert check_citations("No references in this paragraph.") == ["No citations found."]


def test_math_checker_detects_defined_notation(manuscript_text: str) -> None:
    issues = check_math_definitions(manuscript_text)

    assert issues == ["Math expressions detected; no obvious definition issue found."]


def test_math_checker_warns_when_definition_marker_missing() -> None:
    issues = check_math_definitions("The model uses $x_i$ throughout the paper.")

    assert issues == [
        "Mathematical notation detected; verify variables are defined near first use."
    ]


def test_diff_highlight_escapes_html() -> None:
    html = diff_highlight("<script> old", "<script> new")

    assert "&lt;script&gt;" in html
    assert "<script>" not in html
    assert "+ new" in html


def test_plain_text_report_contains_sections() -> None:
    report = generate_report(["Math issue"], ["Citation issue"])

    assert "ScholarFix AI Feedback Report" in report
    assert "Math Symbol Check" in report
    assert "- Citation issue" in report


def test_markdown_report_can_include_rewrite() -> None:
    report = generate_markdown_report(["Math issue"], ["Citation issue"], "Improved text.")

    assert report.startswith("# ScholarFix Feedback Report")
    assert "```markdown" in report
    assert "Improved text." in report


def test_inject_inline_issues_is_safe_for_generic_messages() -> None:
    marked = inject_inline_issues(
        "Prior work [1] defines x.",
        math_issues=["Generic warning without quoted symbol."],
        citation_issues=["Numeric citation found: [1]"],
    )

    assert "[[CHECK: Citation 1]]" in marked
