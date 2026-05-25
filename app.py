"""ScholarFix / RedPen Streamlit application."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import streamlit as st
from openai import OpenAI

from config import APP_NAME, ASSETS_DIR, DEV_MODE, OPENAI_MODEL
from feedback.ai_suggestions import suggest_rewording
from feedback.citation_checker import check_citations
from feedback.math_checker import check_math_definitions
from parsers.docx_parser import extract_docx_text
from parsers.pdf_parser import extract_pdf_text
from parsers.tex_parser import extract_tex_text
from reports.pdf_generator import generate_clean_rewrite_pdf, generate_custom_pdf
from reports.report_generator import generate_markdown_report, generate_report
from utils.diff_utils import diff_highlight
from utils.text_metrics import flesch_label, readability_metrics

LOGGER = logging.getLogger(__name__)


st.set_page_config(page_title=APP_NAME, layout="wide")


@st.cache_resource
def get_openai_client() -> OpenAI:
    """Create an OpenAI client for summary generation."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY is not set. Add it to .env or your shell environment.")
        st.stop()
    return OpenAI(api_key=api_key)


def apply_css() -> None:
    """Load local CSS when available."""
    css_path = ASSETS_DIR / "style.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def metric_card(label: str, value: str, help_text: str | None = None) -> None:
    """Render a compact metric card."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text or ""}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def init_session_state() -> None:
    """Initialise Streamlit session state keys."""
    defaults = {
        "user": None,
        "raw_text": "",
        "file_name": None,
        "math_issues": [],
        "citation_issues": [],
        "suggestion": "",
        "rewrite_tone": "Neutral",
        "rewrite_level": "Undergraduate",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def process_upload(file_obj) -> str:
    """Extract text from a supported upload."""
    file_type = Path(file_obj.name).suffix.lower()
    if file_type == ".pdf":
        return extract_pdf_text(file_obj)
    if file_type == ".tex":
        return extract_tex_text(file_obj)
    if file_type == ".docx":
        return extract_docx_text(file_obj)
    raise ValueError("Unsupported file type.")


def render_sidebar() -> None:
    """Render the persistent sidebar."""
    with st.sidebar:
        st.markdown(f"### {APP_NAME}")
        st.caption("AI-assisted academic editing")
        st.markdown("---")

        user_email = (st.session_state.user or {}).get("email", "Not signed in")
        st.markdown("**User**")
        st.write(user_email)

        st.markdown("---")
        st.markdown("**Exports**")
        st.caption("Generate feedback reports and clean academic PDFs.")

        st.markdown("---")
        mode = "development" if DEV_MODE else "Firebase authentication"
        st.caption(f"Mode: {mode}")


def ensure_authenticated() -> None:
    """Gate the app behind Firebase unless local development mode is enabled."""
    if DEV_MODE:
        st.session_state.user = {"email": "dev@localhost"}
        return

    from auth import verify_firebase_token
    from signin_component import google_login_component

    if st.session_state.user:
        return

    st.markdown("## ScholarFix")
    st.markdown("### Academic feedback, rewrite support, and reviewer-style exports.")
    st.caption("Sign in to continue.")
    st.markdown("---")

    google_login_component()
    token = st.text_input(
        "Firebase token",
        type="password",
        key="firebase-token",
        label_visibility="collapsed",
    )

    if token:
        user_info = verify_firebase_token(token)
        if user_info:
            st.session_state.user = user_info
            st.success(f"Logged in as {user_info['email']}")
            st.rerun()
        else:
            st.error("Invalid or expired login.")

    st.stop()


def render_empty_state() -> None:
    """Render the initial upload prompt."""
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-title">Upload a manuscript to begin</div>
            <ul>
              <li>Extract text from PDF, DOCX, or LaTeX files</li>
              <li>Run lightweight math and citation sanity checks</li>
              <li>Generate an academic rewrite with tone and level controls</li>
              <li>Export feedback as TXT, Markdown, or PDF</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_footer()
    st.stop()


def render_header() -> None:
    """Render the main page header."""
    header_left, header_right = st.columns([0.74, 0.26])
    with header_left:
        st.markdown(
            """
            <div class="app-header">
              <div class="app-title">ScholarFix</div>
              <div class="app-subtitle">
                Academic manuscript feedback, AI rewrite support, and clean reviewer-style exports.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_right:
        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=92)

    st.markdown("---")


def render_upload_bar() -> None:
    """Render upload controls and process newly uploaded files."""
    upload_col, info_col = st.columns([0.65, 0.35])

    with upload_col:
        uploaded_file = st.file_uploader(
            "Upload a .pdf, .tex, or .docx file",
            type=["pdf", "tex", "docx"],
        )

    with info_col:
        if st.session_state.file_name:
            st.markdown("**Current file**")
            st.write(st.session_state.file_name)
        else:
            st.markdown("**Ready**")
            st.caption("Upload a document to begin.")

    if not uploaded_file:
        return

    try:
        st.session_state.file_name = uploaded_file.name
        st.session_state.raw_text = process_upload(uploaded_file)

        if not st.session_state.raw_text.strip():
            st.warning("No readable text detected.")
            return

        st.session_state.math_issues = check_math_definitions(st.session_state.raw_text)
        st.session_state.citation_issues = check_citations(st.session_state.raw_text)
        st.session_state.suggestion = ""
        st.success("Document processed. Navigate tabs below.")
    except Exception as exc:
        LOGGER.exception("File extraction failed")
        st.error(f"Error extracting file: {exc}")


def render_metrics(raw_text: str) -> None:
    """Render readability and length metrics."""
    metrics = readability_metrics(raw_text)

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        metric_card("Word count", f"{metrics['words']:,}", "Total words detected")
    with mcol2:
        metric_card("Sentences", f"{metrics['sentences']:,}", "Approximate count")
    with mcol3:
        metric_card(
            "Avg sentence length",
            f"{metrics['avg_sentence_len']}",
            "Words per sentence",
        )
    with mcol4:
        label = flesch_label(metrics["flesch"])
        metric_card("Readability", f"{metrics['flesch']}", f"Flesch: {label}")


def render_analysis_tab(raw_text: str, math_issues: list[str], citation_issues: list[str]) -> None:
    """Render extracted text and deterministic checks."""
    left, right = st.columns([0.55, 0.45])

    with left:
        st.subheader("Extracted Text Preview")
        st.text_area("Raw Content (preview)", raw_text[:4000], height=320)

    with right:
        st.subheader("Findings")
        a1, a2 = st.columns(2)
        with a1:
            st.metric("Math findings", len(math_issues))
        with a2:
            st.metric("Citation findings", len(citation_issues))

        with st.expander("Math Symbol Issues", expanded=True):
            for index, issue in enumerate(math_issues, start=1):
                st.markdown(f"**{index}.** {issue}")

        with st.expander("Citation Issues", expanded=True):
            for index, issue in enumerate(citation_issues, start=1):
                st.markdown(f"**{index}.** {issue}")


def render_rewrite_tab(raw_text: str) -> None:
    """Render OpenAI rewrite controls and exports."""
    st.subheader("AI Grammar and Style Rewrite")

    rcol1, rcol2, rcol3, rcol4 = st.columns([2.2, 1.4, 1.4, 1.0])
    with rcol1:
        scope = st.selectbox("Target section", ["abstract", "introduction", "full"])
    with rcol2:
        tone = st.selectbox("Tone", ["Neutral", "Formal", "Assertive"])
    with rcol3:
        level = st.selectbox("Academic level", ["Undergraduate", "MSc", "PhD"])
    with rcol4:
        depth = st.slider(
            "AI depth",
            1,
            5,
            3,
            help="Higher values request more assertive rewriting and restructuring.",
        )

    temperature = round(0.15 + 0.08 * (depth - 1), 2)
    st.caption(f"Model: **{OPENAI_MODEL}** | Temperature guide: **{temperature}**")

    action_col, _ = st.columns([0.25, 0.75])
    with action_col:
        run = st.button("Generate Rewrite", use_container_width=True)

    if run:
        st.info("Generating rewrite...")
        st.session_state.rewrite_tone = tone
        st.session_state.rewrite_level = level
        st.session_state.suggestion = suggest_rewording(
            raw_text,
            scope=scope,
            tone=tone,
            level=level,
            model=OPENAI_MODEL,
        )

    suggestion = st.session_state.suggestion
    if not suggestion or len(suggestion) <= 10:
        st.markdown(
            """
            <div class="hint-box">
                Generate a rewrite first to unlock clean PDF export.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown("---")
    st.subheader("Highlighted Diff")
    highlighted = diff_highlight(raw_text[:3000], suggestion)
    st.markdown(highlighted, unsafe_allow_html=True)

    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**Original (excerpt)**")
        st.text_area("Original", raw_text[:3000], height=300)
    with d2:
        st.markdown("**Rewrite**")
        st.text_area("Rewrite", suggestion, height=300)

    st.markdown("---")
    st.subheader("Export Rewrite")
    e1, e2 = st.columns([0.5, 0.5])
    with e1:
        st.download_button(
            "Download Rewrite (.md)",
            suggestion,
            file_name="scholarfix_rewrite.md",
            use_container_width=True,
        )
    with e2:
        clean_pdf_path = Path(
            generate_clean_rewrite_pdf(
                rewritten_text=suggestion,
                title="ScholarFix Clean Academic Rewrite",
            )
        )
        with clean_pdf_path.open("rb") as file_handle:
            st.download_button(
                "Download Clean Academic PDF",
                file_handle,
                file_name="scholarfix_rewritten_draft.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


def render_reports_tab(
    math_issues: list[str],
    citation_issues: list[str],
    suggestion: str,
) -> None:
    """Render report exports and optional OpenAI summary."""
    st.subheader("Reports and Exports")
    r1, r2 = st.columns([0.55, 0.45])

    with r1:
        st.markdown("### Feedback Reports")
        full_report = generate_report(math_issues, citation_issues)
        st.download_button(
            "Download Feedback (.txt)",
            full_report,
            file_name="scholarfix_feedback.txt",
            use_container_width=True,
        )

        markdown_report = generate_markdown_report(
            math_issues,
            citation_issues,
            suggestion if suggestion else None,
        )
        st.download_button(
            "Download Feedback (.md)",
            markdown_report,
            file_name="scholarfix_feedback.md",
            use_container_width=True,
        )

        st.markdown("### PDF Feedback Report")
        include_rewrite = st.checkbox("Include rewrite in PDF", value=bool(suggestion))
        pdf_path = Path(
            generate_custom_pdf(
                math_issues=math_issues,
                citation_issues=citation_issues,
                rewritten_text=suggestion if include_rewrite and suggestion else None,
                tone=st.session_state.rewrite_tone,
                level=st.session_state.rewrite_level,
            )
        )
        with pdf_path.open("rb") as file_handle:
            st.download_button(
                "Download Feedback Report PDF",
                file_handle,
                file_name="scholarfix_feedback_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    with r2:
        st.markdown("### Quick AI Summary")
        st.caption("A short reviewer-style summary of the findings.")

        if st.button("Generate Summary", use_container_width=True):
            client = get_openai_client()
            summary_prompt = (
                "Summarize the key math issues and citation problems found in the text. "
                "If a rewrite exists, summarize what improved. Use concise bullet points.\n\n"
                f"Math Issues:\n{math_issues}\n\n"
                f"Citation Issues:\n{citation_issues}\n\n"
                f"Rewrite Exists:\n{bool(suggestion)}\n"
            )

            with st.spinner("Summarizing..."):
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a concise academic reviewer."},
                        {"role": "user", "content": summary_prompt},
                    ],
                )
                st.success("Done.")
                st.markdown(response.choices[0].message.content)


def render_footer() -> None:
    """Render the footer."""
    st.markdown(
        "<footer>Copyright 2025 ScholarFix - Created by Dr. Muhammad Shoaib</footer>",
        unsafe_allow_html=True,
    )


def main() -> None:
    """Run the Streamlit application."""
    apply_css()
    init_session_state()
    render_sidebar()
    ensure_authenticated()
    render_header()
    render_upload_bar()

    raw_text = st.session_state.raw_text
    if not raw_text.strip():
        render_empty_state()

    math_issues = st.session_state.math_issues
    citation_issues = st.session_state.citation_issues
    suggestion = st.session_state.suggestion

    render_metrics(raw_text)

    tab_analysis, tab_rewrite, tab_reports = st.tabs(["Analysis", "Rewrite", "Reports"])
    with tab_analysis:
        render_analysis_tab(raw_text, math_issues, citation_issues)
    with tab_rewrite:
        render_rewrite_tab(raw_text)
    with tab_reports:
        render_reports_tab(math_issues, citation_issues, suggestion)

    render_footer()


if __name__ == "__main__":
    main()
