# Legacy Streamlit prototype retained for reference.
# The maintained application entry point is app.py.
#
# === Firebase Auth + Streamlit Setup ===
from signin_component import google_login_component
from auth import verify_firebase_token

import streamlit as st
from parsers.pdf_parser import extract_pdf_text
from parsers.tex_parser import extract_tex_text
from parsers.docx_parser import extract_docx_text
from feedback.math_checker import check_math_definitions
from feedback.citation_checker import check_citations
from feedback.ai_suggestions import suggest_rewording
from reports.report_generator import generate_report, inject_inline_issues, generate_markdown_report
from reports.pdf_generator import generate_custom_pdf
from utils.diff_utils import diff_highlight

import openai
from openai import OpenAI
import re
import os

# === MUST BE FIRST ===
st.set_page_config(page_title="ScholarFix", layout="wide")

# === Load custom style ===
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === Secure Auth Flow ===
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.markdown("## ✍️ Fix your writing. Impress your reviewers.")
    st.markdown("ScholarFix gives you instant feedback  to improve grammar, math clarity, and citations.")

    google_login_component()

    # Hidden input where token is passed from JS to Streamlit
    token = st.text_input("Firebase token", type="password", key="firebase-token", label_visibility="collapsed")
    if token:
        user_info = verify_firebase_token(token)
        if user_info:
            st.session_state.user = user_info
            st.success(f"✅ Logged in as {user_info['email']}")
        else:
            st.error("❌ Invalid or expired login. Try again.")
    st.stop()

# === Branding Header ===
col1, col2 = st.columns([1, 8])
with col1:
    st.image("assets/logo.png", width=90)
with col2:
    st.markdown("<h1 style='margin-top: 18px;'>🧠 ScholarFix – Smart Academic Writing Assistant</h1>", unsafe_allow_html=True)

st.markdown("---")

# === Main App ===
client = OpenAI()

st.markdown("🎯 *Precision feedback for academic excellence – powered by SSS*")

uploaded_file = st.file_uploader("Upload a .pdf, .tex, or .docx file", type=["pdf", "tex", "docx"])

if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1]
    raw_text = ""

    if file_type == "pdf":
        raw_text = extract_pdf_text(uploaded_file)
    elif file_type == "tex":
        raw_text = extract_tex_text(uploaded_file)
    elif file_type == "docx":
        raw_text = extract_docx_text(uploaded_file)

    st.subheader("📄 Extracted Text")
    st.text_area("Raw Content", raw_text[:2000], height=250)

    math_issues = check_math_definitions(raw_text)
    citation_issues = check_citations(raw_text)

    st.subheader("📌 Inline Feedback")
    with st.expander("📐 Math Symbol Issues"):
        if math_issues:
            for i, issue in enumerate(math_issues):
                st.markdown(f"**{i+1}.** {issue}")
        else:
            st.success("✅ No math symbol issues found.")

    with st.expander("🔗 Citation Issues"):
        if citation_issues:
            for i, issue in enumerate(citation_issues):
                st.markdown(f"**{i+1}.** {issue}")
        else:
            st.success("✅ No citation issues found.")

    st.subheader("🧠 AI Grammar & Style Suggestions")

    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        scope = st.selectbox("Section", ["abstract", "introduction", "full"], key="scope_selector")
    with col2:
        tone = st.selectbox("Tone", ["Neutral", "Formal", "Assertive"], key="tone_selector")
    with col3:
        level = st.selectbox("Academic Level", ["Undergraduate", "MSc", "PhD"], key="level_selector")

    suggestion = ""
    if st.button("💬 Generate Academic Rewording", key="generate_button"):
        st.info("Generating AI-enhanced academic writing suggestions...")
        suggestion = suggest_rewording(raw_text, scope=scope, tone=tone, level=level)

        if suggestion and len(suggestion) > 10:
            st.subheader("🆚 Highlighted Diff: Original vs Rewritten")
            highlighted = diff_highlight(raw_text[:3000], suggestion)
            st.markdown(highlighted, unsafe_allow_html=True)

            with st.expander("📑 View Full Side-by-Side"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**📝 Original Text**")
                    st.text_area("Original", raw_text[:3000], height=400)
                with col2:
                    st.markdown("**✍️ Rewritten Version**")
                    st.text_area("Rewritten", suggestion, height=400)

            st.download_button("📥 Export Rewritten Text (.md)", suggestion, file_name="rewritten_section.md")

    st.subheader("📄 Downloadable Reports")

    full_report = generate_report(math_issues, citation_issues)
    st.download_button("📥 Download Feedback (.txt)", full_report, file_name="scholarfix_feedback.txt")

    markdown_report = generate_markdown_report(
        math_issues,
        citation_issues,
        suggestion if suggestion else None
    )
    st.download_button("📥 Download Markdown (.md)", markdown_report, file_name="scholarfix_feedback.md")

    with st.expander("⚙️ Customize PDF Report"):
        include_math = st.checkbox("Include Math Issues", value=True)
        include_citations = st.checkbox("Include Citation Issues", value=True)
        include_rewrite = st.checkbox("Include Rewritten Text", value=bool(suggestion))

        if st.button("📄 Generate Custom PDF", key="pdf_button"):
            pdf_path = generate_custom_pdf(
                math_issues if include_math else [],
                citation_issues if include_citations else [],
                suggestion if include_rewrite else None,
                tone=tone if include_rewrite else None,
                level=level if include_rewrite else None
            )
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name="scholarfix_feedback.pdf")

    st.subheader("📊 Quick Summary of Feedback")

    if st.button("🧠 Generate Summary"):
        summary_prompt = (
            "Summarize the key math issues, citation problems, and rewritten suggestions "
            "found in the academic text below. Use bullet points for clarity.\n\n"
            f"Math Issues:\n{math_issues}\n\n"
            f"Citation Issues:\n{citation_issues}\n\n"
            f"Rewritten:\n{suggestion if suggestion else 'N/A'}"
        )

        with st.spinner("Summarizing..."):
            summary_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a concise academic reviewer."},
                    {"role": "user", "content": summary_prompt}
                ]
            )
            feedback_summary = summary_response.choices[0].message.content.strip()
            st.markdown(feedback_summary)

    st.subheader("💬 Ask ScholarFix")

    chat_scope = st.selectbox("💬 Limit chat to section", ["Entire Document", "Abstract", "Introduction", "Conclusion"], key="chat_scope_selector")
    user_query = st.chat_input("Ask about citations, clarity, grammar...")

    def extract_section(text, heading):
        pattern = rf'{heading}\s*(.*?)\s*(?:\n[A-Z][a-z]+|\\section|\\subsection|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else text[:2000]

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        if chat_scope == "Abstract":
            context = extract_section(raw_text, "Abstract")
        elif chat_scope == "Introduction":
            context = extract_section(raw_text, "Introduction")
        elif chat_scope == "Conclusion":
            context = extract_section(raw_text, "Conclusion")
        else:
            context = raw_text[:4000]

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a writing assistant helping users refine academic writing. Use the context to answer precisely."},
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{user_query}"}
                    ]
                )
                reply = response.choices[0].message.content
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

# === Footer ===
st.markdown("<footer>© 2025 ScholarFix – Created by Dr. Muhammad Shoaib</footer>", unsafe_allow_html=True)
