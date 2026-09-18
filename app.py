from html import escape as esc
from pathlib import Path

import streamlit as st

import llm
from charts import plotly_fig
from data_processor import apply_plan, get_messy_api_data, load_file, plan_cleaning, profile_dataset
from report_generator import build_document, to_docx, to_html

st.set_page_config(page_title="AutoReport AI", layout="wide", page_icon="📊", initial_sidebar_state="collapsed")
st.markdown(f"<style>{(Path(__file__).parent / 'style.css').read_text()}</style>", unsafe_allow_html=True)

FORMATS = {"Monthly Report": "monthly", "Weekly Insights": "weekly", "Data Visualizations": "visuals"}
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def title(text: str, cls: str = "section-title"):
    st.markdown(f'<div class="{cls}">{esc(text)}</div>', unsafe_allow_html=True)


def show_fig(fig, key: str):
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except TypeError:  # older Streamlit
        st.plotly_chart(fig, use_container_width=True, key=key)


def render_doc(doc):
    st.markdown(f"<h2>{esc(doc.title)}</h2><p class='doc-sub'>{esc(doc.subtitle)}</p>", unsafe_allow_html=True)
    if doc.headline:
        st.markdown(f"<p class='headline'>{esc(doc.headline)}</p>", unsafe_allow_html=True)
    if doc.kpis:
        tiles = "".join(f"<div class='kpi'><div class='kpi-label'>{esc(l)}</div><div class='kpi-value'>{esc(v)}</div>"
                        f"<div class='kpi-delta'>{esc(d)}</div></div>" for l, v, d in doc.kpis)
        st.markdown(f"<div class='kpis'>{tiles}</div>", unsafe_allow_html=True)
    words = {"up": "Up", "down": "Down", "flat": "Steady", "watch": "Watch"}
    for i, b in enumerate(doc.blocks):
        if b[0] == "h2":
            st.markdown(f"<h3>{esc(b[1])}</h3>", unsafe_allow_html=True)
        elif b[0] == "p":
            st.markdown(f"<p>{esc(b[1])}</p>", unsafe_allow_html=True)
        elif b[0] == "bullets":
            st.markdown("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in b[1]) + "</ul>", unsafe_allow_html=True)
        elif b[0] == "insight":
            st.markdown(f"<div class='insight'><span class='tag {b[3]}'>{words[b[3]]}</span><strong>{esc(b[1])}</strong><p>{esc(b[2])}</p></div>",
                        unsafe_allow_html=True)
        elif b[0] == "chart":
            st.markdown(f"<h3>{esc(b[1].title)}</h3>", unsafe_allow_html=True)
            show_fig(plotly_fig(b[2], b[1]), key=f"{doc.kind}-{i}")
            st.markdown(f"<p class='doc-sub'>{esc(b[3])}</p>", unsafe_allow_html=True)


def start_over(raw_df):
    st.session_state["raw_df"] = raw_df
    st.session_state.pop("analysis", None)
    st.session_state["docs"] = {}
    st.rerun()


# --- Hero ---
st.markdown("""
<div class="hero">
    <div class="disc disc-pink"></div><div class="disc disc-blue"></div><div class="disc disc-yellow"></div>
    <div class="hero-title">Intelligent<br>Report<br>Orchestrator</div>
    <div class="hero-sub">Drop in messy data. The AI works out what it is, cleans it, and writes the report as a Word document.</div>
</div>
""", unsafe_allow_html=True)

# --- Data ingestion ---
title("Start with your data")
left, right = st.columns([3, 2], gap="large", vertical_alignment="center")
with left:
    uploaded = st.file_uploader("Drop a data file here", type=["csv", "tsv", "txt", "xlsx", "json"], label_visibility="collapsed")
with right:
    if uploaded is None:
        if st.button("Use demo data"):
            start_over(get_messy_api_data())
    elif st.button("Analyse file"):
        try:
            start_over(load_file(uploaded))
        except Exception as e:
            st.error(f"Couldn't read this file: {e}")

# --- Understand + clean (runs once per dataset) ---
if "raw_df" in st.session_state and "analysis" not in st.session_state:
    raw = st.session_state["raw_df"]
    with st.status("Reading your data", expanded=True) as status:
        if not llm.check():
            st.write("Ollama isn't running, so built-in rules stand in for the AI. Start Ollama for smarter results.")
        st.write("Working out what each column means...")
        profile, ai_profile = profile_dataset(raw)
        st.write("Deciding how to clean it...")
        plan, ai_plan = plan_cleaning(raw, profile)
        st.write("Cleaning...")
        clean, log = apply_plan(raw, profile, plan)
        status.update(label="Data ready", state="complete", expanded=False)
    st.session_state["analysis"] = dict(clean=clean, profile=profile, log=log, ai=ai_profile and ai_plan)

if "analysis" in st.session_state:
    a = st.session_state["analysis"]
    clean, profile, log = a["clean"], a["profile"], a["log"]

    title("What we found")
    st.markdown(f"<p class='doc-sub' style='font-size:1.3rem;max-width:60ch'>{esc(profile.summary)}</p>", unsafe_allow_html=True)
    chips = "".join(f"<span class='chip {c.role}'>{esc(c.name)}<small>{c.role}</small></span>" for c in profile.columns)
    st.markdown(f"<div class='chips'>{chips}</div>", unsafe_allow_html=True)
    title("What we fixed", "small-title")
    items = "".join(f"<li>{esc(x)}</li>" for x in log) or "<li>Nothing needed fixing.</li>"
    st.markdown(f"<ul class='fixes'>{items}</ul>", unsafe_allow_html=True)
    with st.expander("Preview the cleaned data"):
        st.dataframe(clean.head(100))

    title("Pick a format")
    report_type = st.radio("Output format", list(FORMATS), horizontal=True, label_visibility="collapsed")
    kind = FORMATS[report_type]
    docs = st.session_state.setdefault("docs", {})

    if kind not in docs:  # each artifact is generated once, not on every rerun
        try:
            with st.spinner("Writing it up..."):
                doc = build_document(kind, clean, profile, log)
                docs[kind] = {"doc": doc, "docx": to_docx(doc), "html": to_html(doc)}
        except Exception as e:
            st.error(f"Couldn't build the {report_type.lower()}: {e}")

    if kind in docs:
        out = docs[kind]
        if not out["doc"].ai:
            st.info("The AI model wasn't available for the writing, so this uses built-in summaries. The numbers are unaffected.")
        with st.container(key="report-sheet"):
            render_doc(out["doc"])

        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            st.download_button("Download Word", out["docx"], file_name=f"autoreport_{kind}.docx", mime=DOCX_MIME)
        with c2:
            st.download_button("Download HTML", out["html"], file_name=f"autoreport_{kind}.html", mime="text/html")
        with c3:
            st.download_button("Download clean CSV", clean.to_csv(index=False), file_name="autoreport_clean_data.csv", mime="text/csv")
        st.write("")
        if st.button("Write it again"):
            docs.pop(kind, None)
            st.rerun()
else:
    st.info("Upload a file or use the demo data to get started.")