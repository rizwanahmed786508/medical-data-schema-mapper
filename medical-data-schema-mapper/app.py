"""
app.py
==========================================================
Medical Data Schema Mapper — Streamlit Frontend
==========================================================
This file ONLY wires up the UI. All backend / AI pipeline logic
lives in utils.py and is an exact port of the original notebook.
==========================================================
"""

import io
import json

import pandas as pd
import streamlit as st

import utils

# ----------------------------------------------------------
# Page config (must be first Streamlit call)
# ----------------------------------------------------------
st.set_page_config(
    page_title="Medical Data Schema Mapper",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------------------------------------
# Load CSS
# ----------------------------------------------------------
def load_css(path: str):
    with open(path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style.css")


# ----------------------------------------------------------
# Session state defaults
# ----------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "pipeline_results" not in st.session_state:
    st.session_state.pipeline_results = None
if "source_df_raw" not in st.session_state:
    st.session_state.source_df_raw = None
if "target_df_raw" not in st.session_state:
    st.session_state.target_df_raw = None


# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 8px 4px 20px 4px;">
            <div style="font-size:1.4rem; font-weight:800; color:#f4f6f8;">🧬 Schema Mapper</div>
            <div style="font-size:0.78rem; color:#6b7684; letter-spacing:0.03em;">AI-Powered Data Mapping</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_items = {
        "Home": "🏠  Home",
        "New Output Generation": "📂  New Output Generation",
        "About Project": "📜  About Project",
        "AI Mapping Pipeline": "🧠  AI Mapping Pipeline",
        "Mapping Report": "📊  Mapping Report",
        "Feedback": "⭐  Feedback",
        "Developer": "ℹ️  Developer",
    }

    for key, label in nav_items.items():
        btn_type = "primary" if st.session_state.page == key else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
            st.session_state.page = key
            st.rerun()

    st.markdown("<div style='margin-top:30px;'></div>", unsafe_allow_html=True)

    if st.session_state.pipeline_results is not None:
        st.success("✅ Mapping results ready", icon="✅")
    else:
        st.info("No mapping generated yet", icon="ℹ️")


# ==========================================================
# SHARED FOOTER
# ==========================================================
def render_footer():
    st.markdown(
        """
        <div class="app-footer">
            Medical Data Schema Mapper &nbsp;·&nbsp; v1.0.0 &nbsp;·&nbsp;
            Built by <b>Rizwan Ahmed </b> &nbsp;·&nbsp;
            <a href="https://github.com/" target="_blank">GitHub</a> &nbsp;·&nbsp;
            © 2026 All rights reserved.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# PAGE: HOME
# ==========================================================
def page_home():
    st.markdown(
        """
        <div class="hero fade-in">
            <div class="hero-badge">AI Powered Automatic Schema Matching System</div>
            <div class="hero-title">Medical Data Schema Mapper</div>
            <div class="hero-subtitle">
                Reconcile two different medical CSV schemas into one standardized
                schema — automatically, accurately, and explainably.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-label'>Core Techniques</div>", unsafe_allow_html=True)

    features = [
        ("🔤", "RapidFuzz", "Fast spelling-similarity scoring used as a supporting signal for column names."),
        ("🧠", "Sentence Transformers", "Semantic embeddings (all-MiniLM-L6-v2) that understand meaning, not just spelling."),
        ("📐", "Cosine Similarity", "Compares embedding vectors to score how closely two columns mean the same thing."),
        ("🗺️", "Schema Mapping", "Greedy one-to-one matching with Matched / Review / Low Confidence statuses."),
        ("🧹", "Data Cleaning", "Duplicate removal, missing-value imputation, and IQR-based outlier clipping."),
        ("📄", "JSON Report", "A structured, shareable summary of every mapping decision and its score."),
    ]

    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="glass-card fade-in">
                    <span class="icon">{icon}</span>
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>At a Glance</div>", unsafe_allow_html=True)

    results = st.session_state.pipeline_results
    if results:
        report = results["json_report"]
        stat_vals = [
            (report["Total Mappings"], "Total Mappings"),
            (report["Matched"], "Matched"),
            (report["Review Required"], "Review Required"),
            (report["Average Similarity Score"], "Avg. Similarity"),
        ]
    else:
        stat_vals = [
            ("12", "Pipeline Steps"),
            ("2", "AI Techniques"),
            ("100%", "Schema Coverage Goal"),
            ("1-Click", "CSV Export"),
        ]

    stat_cols = st.columns(4)
    for col, (num, label) in zip(stat_cols, stat_vals):
        with col:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-number">{num}</div>
                    <div class="stat-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
    left, mid, right = st.columns([1, 1, 1])
    with mid:
        if st.button("🚀  Start New Mapping", use_container_width=True, type="primary"):
            st.session_state.page = "New Output Generation"
            st.rerun()

    render_footer()


# ==========================================================
# PAGE: NEW OUTPUT GENERATION
# ==========================================================
def page_generate():
    st.markdown("## 📂 New Output Generation")
    st.caption("Upload your source and target CSV files, then run the AI mapping pipeline.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='section-label'>Source CSV</div>", unsafe_allow_html=True)
        source_file = st.file_uploader("Upload Source CSV", type=["csv"], key="source_upload")
        if source_file is not None:
            st.session_state.source_df_raw = pd.read_csv(source_file)
            st.success(f"✅ Loaded `{source_file.name}` — {st.session_state.source_df_raw.shape[0]} rows, "
                       f"{st.session_state.source_df_raw.shape[1]} columns")
            st.dataframe(st.session_state.source_df_raw.head(), use_container_width=True)

    with col2:
        st.markdown("<div class='section-label'>Target CSV</div>", unsafe_allow_html=True)
        target_file = st.file_uploader("Upload Target CSV", type=["csv"], key="target_upload")
        if target_file is not None:
            st.session_state.target_df_raw = pd.read_csv(target_file)
            st.success(f"✅ Loaded `{target_file.name}` — {st.session_state.target_df_raw.shape[0]} rows, "
                       f"{st.session_state.target_df_raw.shape[1]} columns")
            st.dataframe(st.session_state.target_df_raw.head(), use_container_width=True)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    ready = st.session_state.source_df_raw is not None and st.session_state.target_df_raw is not None

    if not ready:
        st.info("Upload both a source and a target CSV to enable mapping generation.")

    if st.button("⚡ Generate Mapping", disabled=not ready, type="primary"):
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        with st.spinner("Running AI mapping pipeline..."):
            final_results = None
            for fraction, label, payload in utils.run_full_pipeline(
                st.session_state.source_df_raw, st.session_state.target_df_raw
            ):
                progress_bar.progress(fraction)
                status_text.markdown(f"**{label}**")
                if payload is not None:
                    final_results = payload

        st.session_state.pipeline_results = final_results
        status_text.markdown("**✅ Pipeline complete!**")
        st.success("Mapping generated successfully. Head to the **Mapping Report** page to review results.")
        st.balloons()

    render_footer()


# ==========================================================
# PAGE: MAPPING REPORT (results)
# ==========================================================
def status_badge(status: str) -> str:
    css_class = {
        "Matched": "badge-matched",
        "Review Required": "badge-review",
        "Low Confidence": "badge-low",
    }.get(status, "badge-review")
    return f'<span class="badge {css_class}">{status}</span>'


def page_report():
    st.markdown("## 📊 Mapping Report")

    results = st.session_state.pipeline_results
    if results is None:
        st.warning("No mapping has been generated yet. Go to **New Output Generation** first.")
        render_footer()
        return

    report = results["json_report"]
    mapping_df = results["mapping_df"]
    transformed_df = results["transformed_df"]

    # --- Summary stats ---
    stat_cols = st.columns(5)
    stats = [
        (report["Total Mappings"], "Total Mappings"),
        (report["Matched"], "Matched"),
        (report["Review Required"], "Review Required"),
        (report["Low Confidence"], "Low Confidence"),
        (report["Average Similarity Score"], "Avg. Similarity"),
    ]
    for col, (num, label) in zip(stat_cols, stats):
        with col:
            st.markdown(
                f"""<div class="stat-card"><div class="stat-number">{num}</div>
                <div class="stat-label">{label}</div></div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # --- Schema Mapping Table ---
    st.markdown("<div class='section-label'>Schema Mapping Table</div>", unsafe_allow_html=True)

    display_df = mapping_df.copy()
    display_df["Status"] = display_df["Status"].apply(status_badge)
    st.markdown(
        display_df.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # --- Verification ---
    if results["transformation_ok"]:
        st.success("✅ Transformation verified — transformed columns match the target schema exactly.")
    else:
        st.warning("⚠️ Transformed columns do not fully match the target schema (some low-confidence columns were skipped).")

    # --- Transformation Preview (searchable) ---
    st.markdown("<div class='section-label'>Transformation Preview</div>", unsafe_allow_html=True)
    search = st.text_input("🔍 Search transformed data", placeholder="Type to filter rows...")

    preview_df = transformed_df.copy()
    if search:
        mask = preview_df.astype(str).apply(
            lambda row: row.str.contains(search, case=False, na=False)
        ).any(axis=1)
        preview_df = preview_df[mask]

    st.dataframe(preview_df, use_container_width=True, height=380)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # --- Downloads ---
    st.markdown("<div class='section-label'>Download Results</div>", unsafe_allow_html=True)
    dl_col1, dl_col2 = st.columns(2)

    with dl_col1:
        csv_bytes = transformed_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️  Download Transformed CSV",
            data=csv_bytes,
            file_name="transformed_dataset.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with dl_col2:
        json_bytes = json.dumps(report, indent=4, ensure_ascii=False).encode("utf-8")
        st.download_button(
            "⬇️  Download JSON Mapping Report",
            data=json_bytes,
            file_name="schema_mapping_report.json",
            mime="application/json",
            use_container_width=True,
        )

    render_footer()


# ==========================================================
# PAGE: ABOUT PROJECT
# ==========================================================
def page_about():
    st.markdown("## 📜 About This Project")
    st.write(
        "The Medical Data Schema Mapper automatically reconciles two differently "
        "structured medical CSV schemas into a single, standardized schema — "
        "combining spelling-similarity heuristics with semantic AI understanding."
    )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    cards = [
        ("🔤", "RapidFuzz", "A high-performance string-matching library used to gauge spelling similarity between column names, as a supporting diagnostic signal."),
        ("🧠", "Sentence Transformers", "Pretrained AI model (all-MiniLM-L6-v2) that converts column names into vector embeddings capturing their meaning."),
        ("📐", "Cosine Similarity", "Measures the angle between two embedding vectors — the closer to 1, the more semantically similar the columns are."),
        ("🧬", "Embeddings", "Numerical vector representations of text that let a machine compare meaning rather than just characters."),
        ("🗺️", "Schema Mapping", "A greedy one-to-one algorithm that assigns each source column to its best available, not-yet-used target column."),
        ("🧹", "Data Cleaning", "Removes duplicate rows, imputes missing values with median/mode, normalizes text, and clips outliers using the IQR method."),
        ("🔄", "Transformation", "Renames and reorganizes the cleaned source data into the target schema's column names."),
        ("📄", "JSON Report", "A structured report summarizing every mapping decision, its similarity score, and its confidence status."),
    ]

    cols = st.columns(4)
    for i, (icon, title, desc) in enumerate(cards):
        with cols[i % 4]:
            st.markdown(
                f"""
                <div class="glass-card fade-in">
                    <span class="icon">{icon}</span>
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    render_footer()


# ==========================================================
# PAGE: AI MAPPING PIPELINE
# ==========================================================
def page_pipeline():
    st.markdown("## 🧠 AI Mapping Pipeline")
    st.write("Every uploaded dataset moves through the following stages, in order:")

    steps = [
        ("1", "CSV Reading", "Both source and target CSV files are loaded into pandas DataFrames."),
        ("2", "Data Standardization", "Column names are lowercased, cleaned of punctuation, and normalized via an alias dictionary."),
        ("3", "RapidFuzz Matching", "A spelling-similarity score is computed between every source/target column pair (diagnostic signal)."),
        ("4", "Sentence Transformer Embeddings", "Column names are converted into semantic vector embeddings using all-MiniLM-L6-v2."),
        ("5", "Cosine Similarity", "Embeddings are compared pairwise to produce a source-by-target similarity matrix."),
        ("6", "One-to-One Schema Mapping", "Each source column is greedily assigned to its best available target column."),
        ("7", "Mapping Validation", "Similarity scores are thresholded into Matched / Review Required / Low Confidence."),
        ("8", "Data Quality Check", "Shape, dtypes, missing values, and duplicate rows are inspected for both datasets."),
        ("9", "Data Cleaning", "Duplicates dropped, missing values imputed, text normalized, outliers clipped via IQR."),
        ("10", "Data Transformation", "Cleaned source data is renamed into the target schema (low-confidence columns are skipped)."),
        ("11", "CSV Output", "The transformed dataset is made available for download."),
        ("12", "JSON Report", "A structured summary of the whole mapping run is generated for download."),
    ]

    for num, title, desc in steps:
        st.markdown(
            f"""
            <div class="glass-card fade-in" style="display:flex; gap:18px; align-items:flex-start; margin-bottom:14px;">
                <div style="font-size:1.6rem; font-weight:800; color:#2dd4bf; min-width:38px;">{num}</div>
                <div>
                    <h4 style="margin:0 0 4px 0;">{title}</h4>
                    <p style="margin:0;">{desc}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_footer()


# ==========================================================
# PAGE: FEEDBACK
# ==========================================================
def page_feedback():
    st.markdown("## ⭐ Feedback")
    st.write("We'd love to hear your thoughts on the Schema Mapper.")

    with st.form("feedback_form", clear_on_submit=True):
        name = st.text_input("Name")
        email = st.text_input("Email")
        rating = st.slider("Rating", 1, 5, 5)
        suggestions = st.text_area("Suggestions", placeholder="What could we improve?")
        submitted = st.form_submit_button("Submit Feedback", type="primary")

        if submitted:
            if not name or not email:
                st.error("Please fill in both your name and email.")
            else:
                st.success(f"Thank you, {name}! Your feedback has been recorded. ⭐ x {rating}")

    render_footer()


# ==========================================================
# PAGE: DEVELOPER
# ==========================================================
def page_developer():
    st.markdown("## ℹ️ Developer")

    st.markdown(
        """
        <div class="glass-card fade-in">
            <h4>Project</h4>
            <p>Medical Data Schema Mapper — AI-powered automatic schema matching system.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="glass-card fade-in">
            <h4>Tech Stack</h4>
            <p>Python · Streamlit · pandas · RapidFuzz · Sentence-Transformers · scikit-learn</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="glass-card fade-in">
            <h4>Version</h4>
            <p>v1.0.0</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_footer()


# ==========================================================
# ROUTER
# ==========================================================
PAGES = {
    "Home": page_home,
    "New Output Generation": page_generate,
    "About Project": page_about,
    "AI Mapping Pipeline": page_pipeline,
    "Mapping Report": page_report,
    "Feedback": page_feedback,
    "Developer": page_developer,
}

PAGES[st.session_state.page]()
