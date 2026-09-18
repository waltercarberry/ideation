import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data_processor import get_messy_api_data, validate_and_clean, get_llm_data_profile
from report_generator import generate_report_artifacts

# Riso palette: paper + four inks
PAPER = "#F3F3EE"
INK = "#1B1F3B"
BLUE = "#0078BF"
PINK = "#FF48B0"
YELLOW = "#FFE800"
FONT = "Helvetica Neue, Helvetica, Nimbus Sans, Arial, sans-serif"

st.set_page_config(
    page_title="AutoReport AI",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    :root {
        --paper: #F3F3EE;
        --ink: #1B1F3B;
        --blue: #0078BF;
        --pink: #FF48B0;
        --yellow: #FFE800;
        --font: "Helvetica Neue", Helvetica, "Nimbus Sans", Arial, sans-serif;
    }

    /* ---------- Base ---------- */
    .stApp, .stApp *:not([data-testid="stIconMaterial"]) {
        font-family: var(--font) !important;
    }
    .stApp { background: var(--paper); color: var(--ink); }
    .block-container { max-width: 1280px; padding: 2.5rem 4rem 7rem; }
    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer, [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none; }
    *:focus-visible { outline: 3px solid var(--blue); outline-offset: 3px; }

    /* ---------- Hero ---------- */
    .hero { position: relative; min-height: 26rem; padding-top: 2rem; }
    .hero-title {
        position: relative; z-index: 1;
        font-size: clamp(3.2rem, 9vw, 8.5rem);
        font-weight: 700; line-height: 0.9; letter-spacing: -0.05em;
        color: var(--ink);
    }
    .hero-sub {
        position: relative; z-index: 1;
        margin-top: 2rem; max-width: 30rem;
        font-size: 1.35rem; line-height: 1.3; letter-spacing: -0.01em;
    }
    .disc { position: absolute; border-radius: 50%; mix-blend-mode: multiply; pointer-events: none; }
    .disc-pink   { width: 24rem; height: 24rem; top: 0; right: 6%; background: var(--pink); }
    .disc-blue   {
        width: 24rem; height: 24rem; top: 6rem; right: 0;
        background: radial-gradient(circle, var(--blue) 38%, transparent 41%) 0 0 / 11px 11px;
    }
    .disc-yellow { width: 9rem; height: 9rem; top: 17rem; right: 20%; background: var(--yellow); }

    /* ---------- Section titles ---------- */
    .section-title {
        font-size: 2.6rem; font-weight: 700; letter-spacing: -0.04em;
        margin: 4rem 0 1.25rem;
    }

    /* ---------- Big buttons ---------- */
    .stButton > button, .stDownloadButton > button {
        width: 100%; min-height: 5.5rem; padding: 0 2.5rem;
        background: var(--pink); color: var(--ink) !important;
        border: 3px solid var(--ink); border-radius: 999px;
        box-shadow: 6px 6px 0 var(--ink);
        transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
    }
    .stButton > button p, .stDownloadButton > button p {
        font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em; color: var(--ink) !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: var(--yellow); border-color: var(--ink);
        transform: translate(-2px, -2px); box-shadow: 9px 9px 0 var(--ink);
    }
    .stButton > button:active, .stDownloadButton > button:active {
        transform: translate(6px, 6px); box-shadow: 0 0 0 var(--ink);
    }
    .stDownloadButton > button { background: var(--yellow); }
    .stDownloadButton > button:hover { background: var(--pink); }

    /* ---------- File dropzone ---------- */
    [data-testid="stFileUploaderDropzone"] {
        background: var(--yellow); border: 3px dashed var(--ink); border-radius: 28px;
        padding: 2rem 2.5rem; min-height: 8rem;
    }
    [data-testid="stFileUploaderDropzone"] * { color: var(--ink) !important; }
    [data-testid="stFileUploaderDropzone"] button {
        background: var(--paper); border: 2.5px solid var(--ink); border-radius: 999px;
        padding: .7rem 1.6rem; font-weight: 700;
    }

    /* ---------- Format picker (radio as big tiles) ---------- */
    div[role="radiogroup"] { gap: 1.25rem; flex-wrap: wrap; }
    label[data-baseweb="radio"] {
        margin: 0; padding: 1.3rem 2.4rem;
        background: var(--paper); color: var(--ink);
        border: 3px solid var(--ink); border-radius: 999px;
        box-shadow: 5px 5px 0 var(--ink);
        cursor: pointer; transition: transform .12s ease, box-shadow .12s ease;
    }
    label[data-baseweb="radio"] > div:first-child { display: none; }
    label[data-baseweb="radio"] p { margin: 0; color: inherit; font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }
    label[data-baseweb="radio"]:hover { transform: translate(-2px, -2px); box-shadow: 7px 7px 0 var(--ink); }
    label[data-baseweb="radio"]:has(input:checked) { background: var(--blue); color: var(--paper); }
    label[data-baseweb="radio"]:has(input:checked) p { color: var(--paper); }
    label[data-baseweb="radio"]:has(input:focus-visible) { outline: 3px solid var(--blue); outline-offset: 4px; }

    /* ---------- Report sheet ---------- */
    .st-key-report-sheet {
        background: #FFFFFF; border: 3px solid var(--ink);
        box-shadow: 14px 14px 0 var(--pink);
        padding: 3rem 3.5rem; margin: 3rem 0 3.5rem;
    }
    .st-key-report-sheet h1, .st-key-report-sheet h2, .st-key-report-sheet h3 {
        color: var(--ink); font-weight: 700; letter-spacing: -0.04em; line-height: 1;
    }
    .st-key-report-sheet h1 { font-size: 3.4rem; }
    .st-key-report-sheet h2 { font-size: 2.6rem; margin: 0 0 1.25rem; }
    .st-key-report-sheet h3 { font-size: 1.6rem; }
    .st-key-report-sheet p, .st-key-report-sheet li { font-size: 1.1rem; line-height: 1.5; max-width: 70ch; }
    .st-key-report-sheet table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; }
    .st-key-report-sheet th {
        background: var(--yellow); text-align: left; padding: .8rem 1rem;
        border-bottom: 3px solid var(--ink);
    }
    .st-key-report-sheet td { padding: .8rem 1rem; border-bottom: 1px solid rgba(27,31,59,.2); }

    /* ---------- Alerts ---------- */
    [data-testid="stAlert"] {
        background: var(--yellow); color: var(--ink);
        border: 2.5px solid var(--ink); border-radius: 18px;
    }
    [data-testid="stAlert"] * { color: var(--ink) !important; }

    @media (max-width: 800px) {
        .block-container { padding: 1.5rem 1.25rem 5rem; }
        .disc-pink, .disc-blue { width: 13rem; height: 13rem; }
        .disc-blue { top: 4rem; }
        .disc-yellow { display: none; }
        .st-key-report-sheet { padding: 1.5rem; box-shadow: 8px 8px 0 var(--pink); }
    }
</style>
""", unsafe_allow_html=True)

# --- Hero ---
st.markdown("""
<div class="hero">
    <div class="disc disc-pink"></div>
    <div class="disc disc-blue"></div>
    <div class="disc disc-yellow"></div>
    <div class="hero-title">Intelligent<br>Report<br>Orchestrator</div>
    <div class="hero-sub">Drop in messy data. It gets cleaned, explained by an LLM, and packaged as a report.</div>
</div>
""", unsafe_allow_html=True)

# --- Data ingestion ---
st.markdown('<div class="section-title">Start with your data</div>', unsafe_allow_html=True)

src_left, src_right = st.columns([3, 2], gap="large", vertical_alignment="center")

with src_left:
    uploaded_file = st.file_uploader(
        "Drop CSV or Excel here", type=["csv", "xlsx"], label_visibility="collapsed"
    )

with src_right:
    if uploaded_file is None:
        if st.button("Use demo data"):
            st.session_state['raw_df'] = get_messy_api_data()
            st.session_state['processed'] = False
            st.rerun()
    else:
        if st.button("Process file"):
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.session_state['raw_df'] = df
                st.session_state['processed'] = False
                st.rerun()
            except Exception as e:
                st.error(f"Couldn't read this file: {e}")

# --- Main area ---
if 'raw_df' in st.session_state:
    raw_df = st.session_state['raw_df']

    # Processing step
    if not st.session_state.get('processed', False):
        with st.spinner("Analysing your data schema..."):
            clean_df, audit_log, summary_stats = validate_and_clean(raw_df)
            st.session_state['clean_df'] = clean_df
            st.session_state['audit_log'] = audit_log
            st.session_state['summary_stats'] = summary_stats
            st.session_state['processed'] = True

    if st.session_state.get('processed', False):
        clean_df = st.session_state['clean_df']
        audit_log = st.session_state['audit_log']
        summary_stats = st.session_state['summary_stats']

        st.markdown('<div class="section-title">Pick a format</div>', unsafe_allow_html=True)
        report_type = st.radio(
            "Choose your output format:",
            ["Monthly Report", "Weekly Insights", "Data Visualizations"],
            horizontal=True,
            label_visibility="collapsed",
        )

        html_content, csv_data, readme_content = generate_report_artifacts(
            clean_df, audit_log, summary_stats
        )

        with st.container(key="report-sheet"):
            if report_type == "Monthly Report":
                st.markdown(html_content, unsafe_allow_html=True)

            elif report_type == "Weekly Insights":
                st.markdown("<h2>Weekly executive brief</h2>", unsafe_allow_html=True)
                st.info("Focus: short-term trends and immediate anomalies.")
                st.markdown(html_content.split("<h2")[0], unsafe_allow_html=True)  # Simplified for demo

            elif report_type == "Data Visualizations":
                st.markdown("<h2>Interactive analytics</h2>", unsafe_allow_html=True)

                numeric_cols = clean_df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    col_to_plot = numeric_cols[0]
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=clean_df.index,
                        y=clean_df[col_to_plot],
                        mode='lines+markers',
                        name=col_to_plot,
                        line=dict(color=BLUE, width=4),
                        marker=dict(color=PINK, size=11, line=dict(color=INK, width=2)),
                    ))
                    fig.update_layout(
                        height=520,
                        paper_bgcolor="#FFFFFF",
                        plot_bgcolor="#FFFFFF",
                        font=dict(family=FONT, size=14, color=INK),
                        margin=dict(l=10, r=10, t=10, b=10),
                        showlegend=False,
                        xaxis=dict(showgrid=False, zeroline=False, linecolor=INK,
                                   linewidth=3, ticks="outside", tickcolor=INK),
                        yaxis=dict(gridcolor="rgba(27,31,59,0.14)", zeroline=False,
                                   linecolor=INK, linewidth=3,
                                   title=dict(text=str(col_to_plot))),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No numeric columns found, so there's nothing to chart.")

        st.download_button(
            label=f"Download {report_type} as HTML",
            data=html_content,
            file_name=f"{report_type.replace(' ', '_').lower()}.html",
            mime="text/html",
        )

else:
    st.info("Upload a file or use the demo data to get started.")