"""
String Mapper - A local application for fuzzy string matching across Excel files.
Supports Chinese characters and numbers with elegant UI.
"""

import pandas as pd
import streamlit as st

from src.matcher import StringMatcher
from src.report_generator import ReportGenerator

st.set_page_config(
    page_title="String Mapper",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .success-box {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #FEE2E2;
        border-left: 4px solid #EF4444;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    .file-upload-section {
        background: #F8FAFC;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px dashed #CBD5E1;
        margin: 1rem 0;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1E3A5F;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        overflow: hidden;
    }
    .dataframe {
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "source_df" not in st.session_state:
        st.session_state.source_df = None
    if "lookup_dfs" not in st.session_state:
        st.session_state.lookup_dfs = []
    if "results_df" not in st.session_state:
        st.session_state.results_df = None
    if "matching_done" not in st.session_state:
        st.session_state.matching_done = False


def load_excel_file(uploaded_file):
    """Load an Excel file and return a DataFrame."""
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None


def render_header():
    """Render the application header."""
    st.markdown('<p class="main-header">🔗 String Mapper</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Intelligent string matching with Chinese & number support</p>',
        unsafe_allow_html=True
    )


def render_sidebar():
    """Render the sidebar with settings."""
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.divider()

        fuzzy_threshold = st.slider(
            "Fuzzy Match Threshold",
            min_value=50,
            max_value=100,
            value=70,
            step=5,
            help="Minimum similarity score for fuzzy matches (0-100)"
        )

        st.divider()
        st.markdown("### 📖 Guide")
        st.markdown("""
        **Steps:**
        1. Upload your source Excel file
        2. Select target column & info columns
        3. Upload lookup files
        4. Select match columns
        5. Run matching
        6. Download report
        """)

        st.divider()
        st.markdown("### 🌏 Features")
        st.markdown("""
        - ✅ Chinese text support
        - ✅ Number matching
        - ✅ Direct & fuzzy matching
        - ✅ Multi-file lookup
        - ✅ Excel report export
        """)

        return fuzzy_threshold


def render_source_section():
    """Render the source file upload section."""
    st.markdown('<p class="section-title">📁 Source File</p>', unsafe_allow_html=True)

    with st.container():
        source_file = st.file_uploader(
            "Upload your source Excel file",
            type=["xlsx", "xls"],
            key="source_uploader",
            help="This file contains the data you want to match"
        )

        if source_file:
            df = load_excel_file(source_file)
            if df is not None:
                st.session_state.source_df = df
                st.success(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns")

                with st.expander("📊 Preview Source Data", expanded=True):
                    st.dataframe(df.head(10), use_container_width=True)

                col1, col2 = st.columns(2)

                with col1:
                    target_column = st.selectbox(
                        "🎯 Target Column (to match)",
                        options=df.columns.tolist(),
                        help="Select the column containing values to match"
                    )

                with col2:
                    info_columns = st.multiselect(
                        "📋 Info Columns (to include)",
                        options=[c for c in df.columns if c != target_column],
                        help="Select additional columns to include in results"
                    )

                return df, target_column, info_columns

    return None, None, []


def render_lookup_section():
    """Render the lookup files section."""
    st.markdown('<p class="section-title">🔍 Lookup Files</p>', unsafe_allow_html=True)

    lookup_files = st.file_uploader(
        "Upload lookup Excel files (can upload multiple)",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        key="lookup_uploader",
        help="These files contain the data to match against"
    )

    lookup_configs = []

    if lookup_files:
        for i, file in enumerate(lookup_files):
            df = load_excel_file(file)
            if df is not None:
                with st.expander(f"📄 {file.name}", expanded=True):
                    st.dataframe(df.head(5), use_container_width=True)

                    match_column = st.selectbox(
                        f"Match Column for {file.name}",
                        options=df.columns.tolist(),
                        key=f"match_col_{i}",
                        help="Select the column to match against"
                    )

                    lookup_configs.append({
                        "df": df,
                        "name": file.name.replace(".xlsx", "").replace(".xls", ""),
                        "match_column": match_column
                    })

    return lookup_configs


def render_results_section(results_df: pd.DataFrame):
    """Render the results section."""
    st.markdown('<p class="section-title">📊 Matching Results</p>', unsafe_allow_html=True)

    report_gen = ReportGenerator(results_df)
    stats = report_gen.get_summary_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Records",
            value=stats["total_records"],
        )

    with col2:
        st.metric(
            label="Match Rate",
            value=f"{stats['match_rate']:.1f}%",
            delta=f"{stats['exact_matches'] + stats['direct_matches']} exact"
        )

    with col3:
        st.metric(
            label="Fuzzy Matches",
            value=stats["fuzzy_matches"],
            delta=f"avg {stats['avg_fuzzy_score']:.1f}%"
        )

    with col4:
        st.metric(
            label="No Matches",
            value=stats["no_matches"],
            delta="need review" if stats["no_matches"] > 0 else "all matched",
            delta_color="inverse"
        )

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 All Results",
        "✅ Matched",
        "❌ Unmatched",
        "⚠️ Low Confidence"
    ])

    with tab1:
        st.dataframe(results_df, use_container_width=True, height=400)

    with tab2:
        matched = results_df[results_df["match_type"] != "no_match"]
        if len(matched) > 0:
            st.dataframe(matched, use_container_width=True, height=400)
        else:
            st.info("No matches found")

    with tab3:
        unmatched = report_gen.get_unmatched_records()
        if len(unmatched) > 0:
            st.dataframe(unmatched, use_container_width=True, height=400)
        else:
            st.success("All records matched!")

    with tab4:
        low_conf = report_gen.get_low_confidence_matches()
        if len(low_conf) > 0:
            st.dataframe(low_conf, use_container_width=True, height=400)
        else:
            st.success("No low confidence matches!")

    st.divider()

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        excel_buffer = report_gen.generate_excel_report()
        st.download_button(
            label="📥 Download Excel Report",
            data=excel_buffer,
            file_name="matching_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col2:
        text_report = report_gen.generate_text_report()
        st.download_button(
            label="📄 Download Text Report",
            data=text_report,
            file_name="matching_report.txt",
            mime="text/plain",
        )

    with col3:
        with st.expander("📊 View Text Report"):
            st.code(text_report, language=None)


def main():
    """Main application entry point."""
    init_session_state()
    render_header()
    fuzzy_threshold = render_sidebar()

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        source_result = render_source_section()
        source_df, target_column, info_columns = source_result

    with col2:
        lookup_configs = render_lookup_section()

    st.divider()

    if source_df is not None and lookup_configs:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("🚀 Run Matching", use_container_width=True):
                with st.spinner("Matching in progress..."):
                    matcher = StringMatcher(fuzzy_threshold=fuzzy_threshold)

                    lookup_dfs = [
                        (config["df"], config["match_column"], config["name"])
                        for config in lookup_configs
                    ]

                    results_df = matcher.match_dataframes(
                        source_df=source_df,
                        target_column=target_column,
                        info_columns=info_columns,
                        lookup_dfs=lookup_dfs,
                    )

                    st.session_state.results_df = results_df
                    st.session_state.matching_done = True

        st.divider()

        if st.session_state.matching_done and st.session_state.results_df is not None:
            render_results_section(st.session_state.results_df)

    elif source_df is None:
        st.info("👆 Please upload a source Excel file to get started")
    elif not lookup_configs:
        st.info("👆 Please upload at least one lookup Excel file")


if __name__ == "__main__":
    main()
