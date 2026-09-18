import streamlit as st
import pandas as pd
from data_processor import get_messy_api_data, validate_and_clean
from report_generator import generate_report_artifacts

st.set_page_config(page_title="AutoReport AI", layout="wide")

# --- Sidebar: Controls ---
st.sidebar.header("⚙️ Configuration")
run_demo = st.sidebar.button("Run Full Pipeline Demo")
uploaded_file = st.sidebar.file_uploader("Or Upload Raw CSV", type=["csv"])

# --- Main Area ---
st.title("📊 Intelligent Report Orchestrator")
st.caption("Automated Data Cleaning → LLM Insight → Multi-Artifact Generation")

if run_demo or uploaded_file:
    with st.spinner("Processing..."):
        # 1. Ingest
        if uploaded_file:
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = get_messy_api_data()
            
        st.subheader("1. Raw Data Preview")
        st.dataframe(raw_df.head())

        # 2. Validate & Clean
        clean_df, audit_log, summary_stats = validate_and_clean(raw_df)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("2. Cleaned Data")
            st.dataframe(clean_df.tail())
        with col2:
            st.subheader("3. Audit Flags")
            if audit_log:
                for item in audit_log:
                    st.warning(item)
            else:
                st.success("No issues found!")

        # 3. Generate Artifacts
        st.subheader("4. Generated Artifacts")
        html_out, csv_out, md_out = generate_report_artifacts(clean_df, audit_log, summary_stats)
        
        tab1, tab2, tab3 = st.tabs(["📄 Final Report", "💾 Clean Data (CSV)", "📝 Audit Log (MD)"])
        
        with tab1:
            st.markdown(html_out, unsafe_allow_html=True)
            # Note: For true PDF download, you'd convert html_out to bytes here
            
        with tab2:
            st.download_button(
                label="Download Clean CSV",
                data=csv_out,
                file_name='cleaned_data.csv',
                mime='text/csv'
            )
            
        with tab3:
            st.code(md_out, language='markdown')
            st.download_button(
                label="Download Audit Log",
                data=md_out,
                file_name='audit_readme.md',
                mime='text/markdown'
            )
else:
    st.info("Click **'Run Full Pipeline Demo'** in the sidebar to simulate messy API data processing.")