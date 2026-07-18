"""
Documentation page.

Reads and renders the ACTUAL markdown files produced across every
phase of this project -- not summaries or re-typed content, the real
files, bundled into streamlit_app/docs/ and read live from disk. A
visitor can browse any of them in the app or download the raw file.
"""

import os

import streamlit as st

from utils.logger import get_logger

logger = get_logger(__name__)

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(APP_ROOT, "docs")

DOCUMENT_REGISTRY = {
    "📘 Project README": "project_readme.md",
    "📄 Project Report (Full Narrative Summary)": "project_report.md",
    "🏗️ Technical Design Document": "technical_design_document.md",
    "📊 Data Quality Report (Phase 2)": "data_quality_report.md",
    "📈 EDA Insights Report — 105 Findings (Phase 3)": "eda_insights_report.md",
    "🗄️ SQL Verification Log (Phase 4)": "sql_verification_log.md",
    "🧮 Statistics Report (Phase 6)": "statistics_report.md",
    "🤖 Machine Learning Report (Phase 7)": "ml_report.md",
    "💼 BI Synthesis Report (Phase 8)": "bi_synthesis_report.md",
    "📖 Data Dictionary": "data_dictionary.md",
    "📚 Business Glossary": "business_glossary.md",
}


def render():
    st.title("📚 Documentation")
    st.caption("Every document below is the real, unedited file produced during this project's build — read live from disk, not a summary.")

    col_nav, col_content = st.columns([1, 3])

    with col_nav:
        st.markdown("##### Select a Document")
        choice = st.radio("Documents", list(DOCUMENT_REGISTRY.keys()), label_visibility="collapsed")

    filename = DOCUMENT_REGISTRY[choice]
    filepath = os.path.join(DOCS_DIR, filename)

    with col_content:
        if not os.path.exists(filepath):
            st.error(f"Document not found: {filename}")
            logger.error(f"Documentation file missing: {filepath}")
            return

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        word_count = len(content.split())
        st.caption(f"`{filename}` — {word_count:,} words")

        st.download_button(
            f"⬇️ Download {filename}", data=content.encode("utf-8"),
            file_name=filename, mime="text/markdown",
        )

        with st.container(border=True):
            st.markdown(content)

    logger.info(f"Documentation page rendered: {filename}")
