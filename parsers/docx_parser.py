"""DOCX text extraction."""

from __future__ import annotations

from docx import Document


def extract_docx_text(file) -> str:
    """Extract paragraph text from a DOCX-like uploaded file object."""
    doc = Document(file)
    return "\n".join(para.text for para in doc.paragraphs)
