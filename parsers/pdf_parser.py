"""PDF text extraction."""

from __future__ import annotations

import fitz  # PyMuPDF


def extract_pdf_text(file) -> str:
    """Extract text from a PDF-like uploaded file object."""
    with fitz.open(stream=file.read(), filetype="pdf") as document:
        return "\n".join(page.get_text() for page in document)
