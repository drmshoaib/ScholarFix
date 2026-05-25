"""PDF export helpers for ScholarFix feedback reports."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from config import ASSETS_DIR


def _add_page_number(canvas, doc) -> None:
    """Draw a simple page number in the footer."""
    page_text = f"{doc.page}"
    canvas.setFont("Times-Roman", 10)
    canvas.drawRightString(A4[0] - 72, 40, page_text)


def _temporary_pdf_path() -> str:
    """Create and return a temporary PDF path."""
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    filepath = tmp_file.name
    tmp_file.close()
    return filepath


def generate_custom_pdf(
    math_issues: list[str] | None,
    citation_issues: list[str] | None,
    rewritten_text: str | None = None,
    tone: str | None = None,
    level: str | None = None,
) -> str:
    """Generate a branded feedback PDF and return its path."""
    filepath = _temporary_pdf_path()

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=60,
        bottomMargin=60,
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = styles["Heading1"]
    title_style.fontSize = 18
    title_style.spaceAfter = 12

    section_style = styles["Heading2"]
    section_style.fontSize = 14
    section_style.textColor = colors.HexColor("#1f4e79")
    section_style.spaceBefore = 20
    section_style.spaceAfter = 8

    normal_style = styles["Normal"]
    normal_style.fontSize = 11
    normal_style.leading = 15

    meta_style = ParagraphStyle(
        name="MetaStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=10,
    )

    logo_path = ASSETS_DIR / "logo.png"
    if logo_path.exists():
        try:
            image = Image(str(logo_path), width=1.2 * inch, height=1.2 * inch)
            elements.extend([image, Spacer(1, 0.3 * inch)])
        except Exception:
            pass

    elements.append(Paragraph("ScholarFix AI Academic Feedback Report", title_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Spacer(1, 0.3 * inch))

    now = datetime.now().strftime("%d %B %Y")
    meta_text = (
        f"<b>Generated:</b> {escape(now)}<br/>"
        f"<b>Tone:</b> {escape(tone or 'N/A')}<br/>"
        f"<b>Academic Level:</b> {escape(level or 'N/A')}"
    )
    elements.extend([Paragraph(meta_text, meta_style), Spacer(1, 0.4 * inch)])

    def render_section(title: str, items: list[str] | None) -> None:
        elements.append(Paragraph(escape(title), section_style))
        if not items:
            elements.append(Paragraph("No issues detected.", normal_style))
        else:
            bullets = [ListItem(Paragraph(escape(issue), normal_style)) for issue in items]
            elements.append(ListFlowable(bullets, bulletType="bullet", leftIndent=15))
        elements.append(Spacer(1, 0.3 * inch))

    render_section("Math Symbol Issues", math_issues)
    render_section("Citation Issues", citation_issues)

    if rewritten_text:
        elements.append(Paragraph("AI-Rewritten Section", section_style))
        elements.append(Spacer(1, 0.2 * inch))
        for paragraph in rewritten_text.split("\n"):
            if paragraph.strip():
                elements.append(Paragraph(escape(paragraph.strip()), normal_style))
                elements.append(Spacer(1, 0.15 * inch))

    elements.append(Spacer(1, 0.5 * inch))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(
        Paragraph(
            "Copyright 2025 ScholarFix - Created by Dr. Muhammad Shoaib",
            meta_style,
        )
    )

    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    return filepath


def generate_clean_rewrite_pdf(
    rewritten_text: str,
    title: str = "ScholarFix Clean Academic Draft",
) -> str:
    """Generate a clean academic rewrite PDF and return its path."""
    filepath = _temporary_pdf_path()

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = styles["Heading1"]
    title_style.fontName = "Times-Bold"
    title_style.fontSize = 18
    title_style.spaceAfter = 18

    body_style = ParagraphStyle(
        name="AcademicBody",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=12,
        leading=16,
        spaceAfter=12,
    )

    meta_style = ParagraphStyle(
        name="MetaStyle",
        parent=styles["Normal"],
        fontName="Times-Italic",
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
    )

    elements.append(Paragraph(escape(title), title_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Spacer(1, 0.3 * inch))

    now = datetime.now().strftime("%d %B %Y")
    elements.append(Paragraph(f"Generated by ScholarFix on {escape(now)}", meta_style))
    elements.append(Spacer(1, 0.4 * inch))

    for paragraph in rewritten_text.split("\n"):
        if paragraph.strip():
            elements.append(Paragraph(escape(paragraph.strip()), body_style))
            elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    return filepath


def cleanup_generated_pdf(path: str | Path) -> None:
    """Best-effort cleanup for generated temporary PDFs."""
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass
