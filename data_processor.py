"""Understand -> plan -> clean -> measure.

The LLM makes the judgement calls (what is each column, how should gaps and outliers be
handled). Plain pandas then executes those decisions and computes every number, so the
figures in a report are always exact and every change is written to an audit log.
"""
import io
import json
import math
import re
from datetime import datetime, timedelta
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel

import llm

DAYFIRST = True  # dd/mm/yyyy (Ireland/UK). Set False for US-style data.
SUM_HINTS = ("revenue", "sales", "amount", "cost", "spend", "units", "count", "total",
             "orders", "quantity", "profit", "income", "visits", "clicks")


# ------------------------------------------------------------------ schemas
class ColumnProfile(BaseModel):
    name: str
    role: Literal["date", "metric", "category", "identifier", "text"]
    unit: str = ""      # "£", "$", "€", "%", a short unit like "kg", or ""
    agg: Literal["sum", "mean"] = "mean"
    meaning: str = ""


class DatasetProfile(BaseModel):
    summary: str
    columns: list[ColumnProfile]
    primary_date: str = ""


class ColumnFix(BaseModel):
    column: str
    missing: Literal["median", "mean", "zero", "forward_fill", "leave"] = "median"
    outliers: Literal["cap", "leave"] = "cap"
    reason: str = ""


class CleaningPlan(BaseModel):
    drop_duplicates: bool = True
    drop_rows_missing_date: bool = True
    fixes: list[ColumnFix] = []


# ------------------------------------------------------------------ loading
def load_file(uploaded) -> pd.DataFrame:
    """Read csv / tsv / txt / xlsx / json from a Streamlit upload."""
    name = uploaded.name.lower()
    raw = uploaded.getvalue()
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(raw))
    elif name.endswith(".json"):
        df = pd.read_json(io.BytesIO(raw))
    else:
        df = None
        for enc in ("utf-8-sig", "latin-1"):
            try:
                df = pd.read_csv(io.BytesIO(raw), sep=None, engine="python", encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        if df is None:
            raise ValueError("Couldn't decode this file. Try saving it as UTF-8 CSV.")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def get_messy_api_data() -> pd.DataFrame:
    """Demo data with realistic mess: text dates, £ strings, blanks, a spike, casing, a duplicate."""
    rng = np.random.default_rng(7)
    n = 90
    dates = [(datetime.now() - timedelta(days=n - i)).strftime("%d/%m/%Y") for i in range(n)]
    orders = (rng.normal(120, 15, n) + np.linspace(0, 25, n)).round()
    revenue = orders * rng.normal(48, 4, n)
    df = pd.DataFrame({
        "date": dates,
        "orders": orders,
        "revenue": [f"£{v:,.2f}" for v in revenue],
        "region": rng.choice(["North", "South", "East", "West"], n),
    })
    df.loc[5, "orders"] = np.nan
    df.loc[12, "orders"] = 900
    df.loc[20, "date"] = "not recorded"
    df.loc[30, "region"] = "north "
    df.loc[31, "region"] = "SOUTH"
    df.loc[40, "revenue"] = "n/a"
    return pd.concat([df, df.iloc[[50]]], ignore_index=True)


# ------------------------------------------------------------------ parsing helpers
_MULT = {"k": 1e3, "m": 1e6, "bn": 1e9, "b": 1e9}


def to_number(s: pd.Series) -> pd.Series:
    """Parse '£1,234.50', '12%', '(300)', '1.2m' etc. Anything unreadable becomes NaN."""
    if pd.api.types.is_numeric_dtype(s):
        return s

    def parse(v):
        if pd.isna(v):
            return np.nan
        t = str(v).strip().lower().replace(",", "")
        neg = t.startswith("(") and t.endswith(")")
        t = re.sub(r"[£$€%()\s]", "", t)
        m = re.fullmatch(r"(-?\d*\.?\d+)(bn|k|m|b)?", t)
        if not m:
            return np.nan
        x = float(m.group(1)) * _MULT.get(m.group(2), 1)
        return -x if neg else x

    return s.map(parse).astype(float)


def to_date(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        out = s
    else:
        try:
            out = pd.to_datetime(s, errors="coerce", dayfirst=DAYFIRST, format="mixed")
        except (TypeError, ValueError):
            out = pd.to_datetime(s, errors="coerce", dayfirst=DAYFIRST)
    if getattr(out.dt, "tz", None) is not None:
        out = out.dt.tz_localize(None)
    return out


def _num_ratio(s: pd.Series) -> float:
    nn = s.dropna().head(200)
    return float(to_number(nn).notna().mean()) if len(nn) else 0.0


def _date_ratio(s: pd.Series) -> float:
    nn = s.dropna().head(200)
    if not len(nn) or pd.api.types.is_numeric_dtype(nn):
        return 0.0
    return float(to_date(nn.astype(str) if not pd.api.types.is_datetime64_any_dtype(nn) else nn).notna().mean())


def _n(n: int, word: str, plural: str = "") -> str:
    return f"{n} {word if n == 1 else (plural or word + 's')}"


def label(name: str) -> str:
    return str(name).replace("_", " ").strip().capitalize()


def fmt(v, unit: str = "") -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    s = f"{v:,.0f}" if abs(v) >= 100 else f"{v:,.2f}"
    if s.endswith(".00"):
        s = s[:-3]
    if unit in ("£", "$", "€"):
        return f"{unit}{s}"
    if unit == "%":
        return f"{s}%"
    return f"{s} {unit}".strip()


# ------------------------------------------------------------------ 1. profile
def heuristic_profile(df: pd.DataFrame) -> DatasetProfile:
    cols = []
    for c in df.columns:
        s = df[c]
        nn = s.dropna()
        uniq = nn.nunique()
        unit = ""
        if pd.api.types.is_datetime64_any_dtype(s):
            role = "date"
        elif pd.api.types.is_numeric_dtype(s) or _num_ratio(s) > 0.8:
            role = "identifier" if re.search(r"(^id$|_id$|^id_|uuid)", c.lower()) else "metric"
            if not pd.api.types.is_numeric_dtype(s):
                sample = "".join(nn.astype(str).head(50))
                unit = next((u for u in "£$€%" if u in sample), "")
        elif _date_ratio(s) > 0.8:
            role = "date"
        elif uniq <= max(25, 0.05 * len(nn)):
            role = "category"
        else:
            role = "text"
        agg = "sum" if any(h in c.lower() for h in SUM_HINTS) else "mean"
        cols.append(ColumnProfile(name=c, role=role, unit=unit, agg=agg))
    first_date = next((c.name for c in cols if c.role == "date"), "")
    return DatasetProfile(summary=f"{len(df):,} rows and {len(df.columns)} columns.", columns=cols, primary_date=first_date)


def _col_stats(df: pd.DataFrame, cap: int = 40) -> list[dict]:
    return [{
        "name": c, "dtype": str(df[c].dtype), "missing": int(df[c].isna().sum()),
        "unique": int(df[c].nunique(dropna=True)),
        "examples": [str(v) for v in df[c].dropna().unique()[:5]],
    } for c in list(df.columns)[:cap]]


def _reconcile(df: pd.DataFrame, prof: DatasetProfile, fallback: DatasetProfile) -> DatasetProfile:
    """Trust the LLM, but check it against the data and fill any gaps."""
    known = {c.name: c for c in fallback.columns}
    out, seen = [], set()
    for cp in prof.columns:
        if cp.name not in known or cp.name in seen:
            continue
        seen.add(cp.name)
        s = df[cp.name]
        bad = (cp.role == "date" and _date_ratio(s) <= 0.5 and not pd.api.types.is_datetime64_any_dtype(s)) \
            or (cp.role == "metric" and _num_ratio(s) <= 0.5)
        out.append(known[cp.name] if bad else cp)
    out += [known[c] for c in known if c not in seen]
    order = {c: i for i, c in enumerate(df.columns)}
    out.sort(key=lambda c: order[c.name])
    dates = [c.name for c in out if c.role == "date"]
    primary = prof.primary_date if prof.primary_date in dates else (dates[0] if dates else "")
    return DatasetProfile(summary=prof.summary or fallback.summary, columns=out, primary_date=primary)


def profile_dataset(df: pd.DataFrame) -> tuple[DatasetProfile, bool]:
    """Returns (profile, used_ai)."""
    fallback = heuristic_profile(df)
    prompt = f"""A dataset has {len(df)} rows. Column summaries (JSON):
{json.dumps(_col_stats(df), indent=1)}

For EVERY column decide its role: date, metric (a numeric measure), category (groups rows, e.g. region),
identifier (unique id) or text (free text).
Also give: unit ("£", "$", "€", "%", a short unit like "kg", or ""), agg ("sum" for additive quantities such as
revenue or units sold; "mean" for rates, prices, scores), and meaning (max 8 words).
summary: one plain sentence saying what this dataset is about.
primary_date: the main date column name, or "" if none."""
    try:
        prof = llm.ask_json(prompt, DatasetProfile, system="You are a careful data analyst. Only use the column names given.")
        return _reconcile(df, prof, fallback), True
    except llm.LLMUnavailable:
        return fallback, False


# ------------------------------------------------------------------ 2. cleaning plan
def _fences(s: pd.Series):
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    return (q1 - 3 * iqr, q3 + 3 * iqr) if iqr > 0 else (None, None)


def _default_plan(profile: DatasetProfile) -> CleaningPlan:
    return CleaningPlan(fixes=[ColumnFix(column=c.name) for c in profile.columns if c.role == "metric"])


def plan_cleaning(df: pd.DataFrame, profile: DatasetProfile) -> tuple[CleaningPlan, bool]:
    """Returns (plan, used_ai). The plan is only a set of choices; apply_plan() does the work."""
    metrics = [c for c in profile.columns if c.role == "metric"]
    default = _default_plan(profile)
    if not metrics:
        return default, False
    stats = []
    for c in metrics:
        s = to_number(df[c.name])
        lo, hi = _fences(s.dropna()) if s.notna().sum() > 3 else (None, None)
        stats.append({
            "column": c.name, "meaning": c.meaning, "unit": c.unit,
            "missing": int(s.isna().sum()), "rows": len(s),
            "extreme_values": int(((s < lo) | (s > hi)).sum()) if lo is not None else 0,
            "min": None if s.dropna().empty else float(s.min()),
            "median": None if s.dropna().empty else float(s.median()),
            "max": None if s.dropna().empty else float(s.max()),
        })
    prompt = f"""Dataset: {profile.summary}
Numeric columns with quality stats (JSON):
{json.dumps(stats, indent=1)}

For each numeric column choose:
- missing: "median" (default), "mean", "zero" (blank really means none, e.g. counts), "forward_fill" (a level that
  carries over time, e.g. a price or balance) or "leave" (never invent data).
- outliers: "cap" (extreme values are likely errors or would distort averages) or "leave" (they are genuine).
Give a short reason for each. Set drop_duplicates and drop_rows_missing_date to true unless there is a good reason."""
    try:
        plan = llm.ask_json(prompt, CleaningPlan, system="You are a careful data analyst. Only use the column names given.")
        names = {c.name for c in metrics}
        chosen = {f.column: f for f in plan.fixes if f.column in names}
        plan.fixes = [chosen.get(n) or ColumnFix(column=n) for n in names]
        return plan, True
    except llm.LLMUnavailable:
        return default, False


# ------------------------------------------------------------------ 3. apply
def apply_plan(df: pd.DataFrame, profile: DatasetProfile, plan: CleaningPlan) -> tuple[pd.DataFrame, list[str]]:
    df, log = df.copy(), []

    n = len(df)
    df = df.dropna(how="all")
    if len(df) < n:
        log.append(f"Removed {_n(n - len(df), 'completely empty row')}.")
    empty = [c for c in df.columns if df[c].isna().all()]
    if empty:
        df = df.drop(columns=empty)
        log.append(f"Removed empty columns: {', '.join(empty)}.")
    if plan.drop_duplicates:
        n = len(df)
        df = df.drop_duplicates()
        if len(df) < n:
            log.append(f"Removed {_n(n - len(df), 'duplicate row')}.")
    df = df.reset_index(drop=True)

    roles = {c.name: c for c in profile.columns if c.name in df.columns}
    primary = profile.primary_date if profile.primary_date in df.columns else ""

    for name, cp in roles.items():
        if cp.role != "date":
            continue
        before = df[name].notna().sum()
        df[name] = to_date(df[name])
        bad = int(before - df[name].notna().sum())
        if bad and name != primary:
            log.append(f"{_n(bad, 'entry', 'entries')} in '{name}' weren't valid dates and {'was' if bad == 1 else 'were'} left blank.")

    if primary:
        n = len(df)
        if plan.drop_rows_missing_date:
            df = df[df[primary].notna()].copy()
            if len(df) < n:
                log.append(f"Dropped {_n(n - len(df), 'row')} with a missing or unreadable date in '{primary}'.")
        df = df.sort_values(primary).reset_index(drop=True)

    fixes = {f.column: f for f in plan.fixes}
    for name, cp in roles.items():
        if cp.role == "metric":
            before = int(df[name].isna().sum())
            df[name] = to_number(df[name]).astype(float)
            coerced = int(df[name].isna().sum()) - before
            if coerced:
                log.append(f"{_n(coerced, 'non-numeric entry', 'non-numeric entries')} in '{name}' {'was' if coerced == 1 else 'were'} treated as missing.")
            fx = fixes.get(name) or ColumnFix(column=name)

            miss = int(df[name].isna().sum())
            if miss and fx.missing != "leave":
                med = df[name].median()
                how = {"median": "median", "mean": "mean", "zero": "zero", "forward_fill": "previous value"}[fx.missing]
                if fx.missing == "median":
                    df[name] = df[name].fillna(med)
                elif fx.missing == "mean":
                    df[name] = df[name].fillna(df[name].mean())
                elif fx.missing == "zero":
                    df[name] = df[name].fillna(0)
                else:
                    df[name] = df[name].ffill().fillna(med)
                log.append(f"Filled {_n(miss, 'missing value')} in '{name}' using the {how}.")

            if fx.outliers == "cap" and df[name].notna().sum() > 3:
                lo, hi = _fences(df[name].dropna())
                if lo is not None:
                    n_out = int(((df[name] < lo) | (df[name] > hi)).sum())
                    if n_out:
                        df[name] = df[name].clip(lo, hi)
                        log.append(f"Capped {_n(n_out, 'extreme value')} in '{name}' to the range {fmt(lo, cp.unit)} to {fmt(hi, cp.unit)}.")

        elif cp.role == "category":
            orig = df[name].astype("string")
            s = orig.str.strip()
            s = s.mask(s == "", pd.NA)
            lower = s.str.lower()
            canon = s.groupby(lower).agg(lambda x: x.value_counts().idxmax())
            mapped = lower.map(canon)
            changed = int((mapped.fillna("") != orig.fillna("").str.strip()).sum())
            blank = int(mapped.isna().sum())
            df[name] = mapped.fillna("Unknown").astype(object)
            if changed:
                log.append(f"Standardised spelling and capitalisation in '{name}' ({_n(changed, 'entry', 'entries')}).")
            if blank:
                log.append(f"Labelled {_n(blank, 'blank entry', 'blank entries')} in '{name}' as 'Unknown'.")
    return df, log


# ------------------------------------------------------------------ 4. facts (every number the report may use)
def _r(v, d=2):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), d)


def compute_facts(df: pd.DataFrame, profile: DatasetProfile, kind: str, notes: list[str] | None = None) -> dict:
    roles = {c.name: c for c in profile.columns if c.name in df.columns}
    metrics = [c for c in roles.values() if c.role == "metric"][:4]
    cats = [c.name for c in roles.values() if c.role == "category" and 2 <= df[c.name].nunique() <= 25]
    cat = cats[0] if cats else ""
    dcol = profile.primary_date if profile.primary_date in df.columns and df[profile.primary_date].notna().any() else ""

    facts = {"dataset": profile.summary, "rows": int(len(df)), "data_quality_notes": notes or []}
    cur, prev = df, df.iloc[0:0]
    windowed = bool(dcol) and kind in ("monthly", "weekly")
    if dcol:
        start, end = df[dcol].min(), df[dcol].max()
        facts["date_range"] = f"{start:%d %b %Y} to {end:%d %b %Y}"
    if windowed:
        days = 30 if kind == "monthly" else 7
        uniq = df[dcol].dt.normalize().drop_duplicates().sort_values()
        gap = uniq.diff().dt.days.median() if len(uniq) > 1 else 1
        days = int(max(days, gap if pd.notna(gap) else 1))
        cur = df[(df[dcol] > end - pd.Timedelta(days=days)) & (df[dcol] <= end)]
        prev = df[(df[dcol] > end - pd.Timedelta(days=2 * days)) & (df[dcol] <= end - pd.Timedelta(days=days))]
        facts["window"] = {
            "length_days": days,
            "current_period": f"{cur[dcol].min():%d %b} to {cur[dcol].max():%d %b %Y}" if len(cur) else "",
            "compared_with_previous_period": bool(len(prev)),
        }

    def agg(s, how):
        return None if not len(s) else float(s.sum() if how == "sum" else s.mean())

    out = []
    for m in metrics:
        s = df[m.name]
        item = {"name": m.name, "label": label(m.name), "unit": m.unit, "aggregation": m.agg, "meaning": m.meaning,
                "overall": {"mean": _r(s.mean()), "median": _r(s.median()), "min": _r(s.min()), "max": _r(s.max()),
                            "total": _r(s.sum()) if m.agg == "sum" else None}}
        if windowed:
            c, p = agg(cur[m.name], m.agg), agg(prev[m.name], m.agg)
            item["current_period_value"] = _r(c)
            item["previous_period_value"] = _r(p)
            item["change_pct"] = _r((c - p) / abs(p) * 100, 1) if c is not None and p else None
            if len(cur):
                i = cur[m.name].idxmax()
                item["peak_in_period"] = {"date": f"{cur.loc[i, dcol]:%d %b}", "value": _r(cur.loc[i, m.name])}
        if cat:
            g = (cur if len(cur) else df).groupby(cat)[m.name].agg("sum" if m.agg == "sum" else "mean").sort_values(ascending=False)
            item["by_category"] = {"column": cat,
                                   "highest": [[str(k), _r(v)] for k, v in g.head(3).items()],
                                   "lowest": [[str(k), _r(v)] for k, v in g.tail(1).items()]}
        out.append(item)
    facts["metrics"] = out
    return facts