"""The LLM picks which charts explain the data; code builds the numbers and draws them.

One ChartSpec feeds two renderers: Plotly for the app, matplotlib (PNG) for Word/HTML exports.
"""
import io
import json
import logging
from typing import Literal

import pandas as pd
from pydantic import BaseModel

import llm
from data_processor import DatasetProfile, fmt, label

INK, BLUE, PINK, YELLOW = "#1B1F3B", "#0078BF", "#FF48B0", "#FFE800"
SERIES = [BLUE, PINK, INK, YELLOW]
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)


class ChartSpec(BaseModel):
    title: str
    kind: Literal["line", "bar", "scatter", "histogram"]
    x: str
    y: str = ""
    group: str = ""
    agg: Literal["sum", "mean", "count"] = "mean"
    freq: Literal["none", "day", "week", "month"] = "none"


class ChartPlan(BaseModel):
    charts: list[ChartSpec]


# ------------------------------------------------------------------ planning
def auto_freq(df: pd.DataFrame, dcol: str) -> str:
    span = (df[dcol].max() - df[dcol].min()).days
    return "day" if span <= 60 else "week" if span <= 400 else "month"


def _roles(profile: DatasetProfile) -> dict:
    return {c.name: c for c in profile.columns}


def default_charts(df: pd.DataFrame, profile: DatasetProfile) -> list[ChartSpec]:
    cols = [c for c in profile.columns if c.name in df.columns]
    metrics = [c for c in cols if c.role == "metric"]
    cats = [c.name for c in cols if c.role == "category" and 2 <= df[c.name].nunique() <= 12]
    dcol = profile.primary_date if profile.primary_date in df.columns else ""
    out = []
    for m in metrics[:2]:
        agg = m.agg
        if dcol:
            out.append(ChartSpec(title=f"{label(m.name)} over time", kind="line", x=dcol, y=m.name, agg=agg, freq=auto_freq(df, dcol)))
        if cats:
            out.append(ChartSpec(title=f"{label(m.name)} by {label(cats[0]).lower()}", kind="bar", x=cats[0], y=m.name, agg=agg))
    if metrics:
        out.append(ChartSpec(title=f"Distribution of {label(metrics[0].name).lower()}", kind="histogram", x=metrics[0].name))
    if len(metrics) >= 2:
        out.append(ChartSpec(title=f"{label(metrics[0].name)} vs {label(metrics[1].name).lower()}", kind="scatter", x=metrics[0].name, y=metrics[1].name))
    return out


def _validate(s: ChartSpec, df: pd.DataFrame, profile: DatasetProfile):
    roles = {n: c.role for n, c in _roles(profile).items() if n in df.columns}
    if s.x not in roles:
        return None
    if s.kind == "histogram":
        return s.model_copy(update={"y": "", "group": "", "freq": "none"}) if roles[s.x] == "metric" else None
    if roles.get(s.y) != "metric":
        return None
    if s.group and (roles.get(s.group) != "category" or df[s.group].nunique() > 8):
        s = s.model_copy(update={"group": ""})
    ok = {"line": roles[s.x] == "date", "bar": roles[s.x] in ("category", "date"), "scatter": roles[s.x] == "metric"}[s.kind]
    if not ok:
        return None
    if roles[s.x] == "date":
        return s.model_copy(update={"freq": auto_freq(df, s.x) if s.freq == "none" else s.freq})
    return s.model_copy(update={"freq": "none"})


def plan_charts(df: pd.DataFrame, profile: DatasetProfile, n: int) -> list[ChartSpec]:
    chosen = []
    cols = [{"name": c.name, "role": c.role, "meaning": c.meaning} for c in profile.columns]
    prompt = f"""Dataset: {profile.summary}
Columns (JSON): {json.dumps(cols)}

Propose {n} different charts that best explain this data to a busy reader. Chart kinds:
- line: x = the date column, y = a metric (set agg to sum or mean, freq to day/week/month)
- bar: x = a category column (or the date column), y = a metric
- histogram: x = a metric (its distribution)
- scatter: x = a metric, y = another metric
Optional group = a category column with few values. Use only the column names above. Titles should say what the chart shows."""
    try:
        plan = llm.ask_json(prompt, ChartPlan, system="You are a data visualisation expert.")
        chosen = [v for v in (_validate(s, df, profile) for s in plan.charts) if v]
    except llm.LLMUnavailable:
        pass
    seen, out = set(), []
    for s in chosen + default_charts(df, profile):
        key = (s.kind, s.x, s.y, s.group)
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out[:n]


# ------------------------------------------------------------------ data
def build_frame(df: pd.DataFrame, s: ChartSpec) -> pd.DataFrame:
    if s.kind == "histogram":
        return df[[s.x]].dropna()
    cols = [s.x, s.y] + ([s.group] if s.group else [])
    d = df[cols].dropna(subset=[s.x, s.y]).copy()
    if pd.api.types.is_datetime64_any_dtype(d[s.x]) and s.freq != "none":
        d[s.x] = d[s.x].dt.to_period({"day": "D", "week": "W", "month": "M"}[s.freq]).dt.start_time
    if s.kind in ("line", "bar"):
        if s.agg == "sum" and s.freq in ("week", "month") and d[s.x].nunique() >= 4:
            xs = sorted(d[s.x].unique())  # first/last buckets are usually partial and would distort a total
            d = d[~d[s.x].isin([xs[0], xs[-1]])]
        keys = [s.x] + ([s.group] if s.group else [])
        d = d.groupby(keys, as_index=False)[s.y].agg(s.agg).sort_values(keys)
        if s.kind == "bar" and not s.group and not pd.api.types.is_datetime64_any_dtype(d[s.x]):
            d = d.nlargest(15, s.y)
    return d.reset_index(drop=True)


def digest(frame: pd.DataFrame, s: ChartSpec, units: dict) -> str:
    """A one-sentence, exact description of what a chart shows (also the no-AI caption)."""
    u = units.get(s.y, "") if s.y else units.get(s.x, "")
    if frame.empty:
        return f"{s.title}: no data to show."
    if s.kind == "histogram":
        v = frame[s.x]
        return f"{s.title}: typical value {fmt(v.median(), u)}, ranging from {fmt(v.min(), u)} to {fmt(v.max(), u)}."
    if s.kind == "scatter":
        return f"{s.title}: correlation of {frame[s.x].corr(frame[s.y]):.2f} across {len(frame)} points."
    if s.group:
        g = frame.groupby(s.group)[s.y].mean().sort_values(ascending=False)
        return f"{s.title}: {g.index[0]} is highest ({fmt(g.iloc[0], u)}) and {g.index[-1]} lowest ({fmt(g.iloc[-1], u)}) on average."
    if s.kind == "bar":
        f = frame.sort_values(s.y, ascending=False)
        x0, x1 = f.iloc[0], f.iloc[-1]
        d = lambda v: f"{v:%d %b}" if hasattr(v, "strftime") else str(v)
        return f"{s.title}: {d(x0[s.x])} is highest ({fmt(x0[s.y], u)}) and {d(x1[s.x])} lowest ({fmt(x1[s.y], u)})."
    a, b = frame.iloc[0][s.y], frame.iloc[-1][s.y]
    pk = frame.loc[frame[s.y].idxmax()]
    chg = f", a change of {(b - a) / abs(a) * 100:+.1f}%" if a else ""
    return f"{s.title}: moved from {fmt(a, u)} to {fmt(b, u)}{chg}, peaking at {fmt(pk[s.y], u)} on {pk[s.x]:%d %b}."


# ------------------------------------------------------------------ Plotly (app)
def plotly_fig(frame: pd.DataFrame, s: ChartSpec):
    import plotly.graph_objects as go
    fig = go.Figure()
    if s.kind == "histogram":
        fig.add_trace(go.Histogram(x=frame[s.x], marker=dict(color=BLUE, line=dict(color=INK, width=1.5))))
    else:
        groups = list(frame.groupby(s.group)) if s.group else [(s.y, frame)]
        for i, (g, d) in enumerate(groups):
            c = SERIES[i % len(SERIES)]
            mk = dict(color=c, size=9, line=dict(color=INK, width=1.5))
            if s.kind == "line":
                fig.add_trace(go.Scatter(x=d[s.x], y=d[s.y], name=str(g), mode="lines+markers", line=dict(color=c, width=4), marker=mk))
            elif s.kind == "bar":
                fig.add_trace(go.Bar(x=d[s.x], y=d[s.y], name=str(g), marker=dict(color=c, line=dict(color=INK, width=1.5))))
            else:
                fig.add_trace(go.Scatter(x=d[s.x], y=d[s.y], name=str(g), mode="markers", marker=mk))
    fig.update_layout(
        height=440, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", barmode="group",
        font=dict(family=FONT, size=14, color=INK), margin=dict(l=10, r=10, t=10, b=10),
        showlegend=bool(s.group), legend=dict(orientation="h", y=1.1),
        xaxis=dict(title=label(s.x), showgrid=False, zeroline=False, linecolor=INK, linewidth=3, ticks="outside", tickcolor=INK),
        yaxis=dict(title=label(s.y) if s.y else "Count", gridcolor="rgba(27,31,59,0.14)", zeroline=False, linecolor=INK, linewidth=3),
    )
    return fig


# ------------------------------------------------------------------ matplotlib (Word / HTML exports)
def mpl_png(frame: pd.DataFrame, s: ChartSpec) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Helvetica", "Helvetica Neue", "Arial", "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"

    fig, ax = plt.subplots(figsize=(7.2, 3.5), dpi=200)
    if s.kind == "histogram":
        ax.hist(frame[s.x], bins=min(20, max(5, int(len(frame) ** 0.5))), color=BLUE, edgecolor=INK, linewidth=1.2)
    elif s.kind == "bar":
        piv = frame.pivot_table(index=s.x, columns=s.group or None, values=s.y, aggfunc="sum") if s.group \
            else frame.set_index(s.x)[[s.y]]
        piv.index = [v.strftime("%d %b") if hasattr(v, "strftime") else str(v) for v in piv.index]
        piv.plot.bar(ax=ax, color=SERIES[:piv.shape[1]], edgecolor=INK, linewidth=1.2, legend=bool(s.group), width=0.75)
        ax.tick_params(axis="x", rotation=0 if len(piv) <= 6 else 45)
    else:
        groups = list(frame.groupby(s.group)) if s.group else [(s.y, frame)]
        for i, (g, d) in enumerate(groups):
            c = SERIES[i % len(SERIES)]
            if s.kind == "line":
                ax.plot(d[s.x], d[s.y], color=c, lw=2.4, marker="o", ms=4.5, mec=INK, mew=0.8, label=str(g))
            else:
                ax.scatter(d[s.x], d[s.y], color=c, s=28, edgecolor=INK, linewidth=0.8, label=str(g))
        if s.group:
            ax.legend(frameon=False)
    ax.set_xlabel(label(s.x) if s.kind != "bar" or s.group else "")
    ax.set_ylabel(label(s.y) if s.y else "Count")
    ax.set_facecolor("white")
    ax.grid(axis="y", color=INK, alpha=0.14)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK)
        ax.spines[side].set_linewidth(1.6)
    ax.tick_params(colors=INK)
    if pd.api.types.is_datetime64_any_dtype(frame[s.x]) and s.kind in ("line", "scatter"):
        import matplotlib.dates as mdates
        loc = mdates.AutoDateLocator()
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()