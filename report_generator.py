import os
import json
import llm
from pydantic import BaseModel
from typing import Literal
from data_processor import DatasetProfile, compute_facts, fmt, label
from charts import plan_charts, build_frame, digest

# --- Schemas (Keep these, they are great) ---
class Section(BaseModel):
    heading: str
    body: str

class MonthlyNarrative(BaseModel):
    headline: str
    sections: list[Section]
    recommendations: list[str]

class Insight(BaseModel):
    title: str
    detail: str
    direction: Literal["up", "down", "flat", "watch"]

class WeeklyNarrative(BaseModel):
    headline: str
    insights: list[Insight]
    watchlist: list[str]

# --- The "Master Prompt" Fix ---
def _build_context(facts, digests):
    """Combines raw facts with human-readable chart descriptions."""
    context = f"""
    DATASET CONTEXT: {facts['dataset']}
    PERIOD: {facts.get('window', {}).get('current_period', 'All time')}
    
    KEY METRICS:
    {json.dumps(facts['metrics'], indent=1)}
    
    VISUAL TRENDS (What the charts show):
    {json.dumps(digests, indent=1)}
    
    DATA QUALITY NOTES:
    {json.dumps(facts['data_quality_notes'])}
    """
    return context

def _monthly_narrative(facts, digests):
    context = _build_context(facts, digests)
    prompt = f"""
    {context}

    TASK: Write a concise Monthly Performance Report based ONLY on the information provided in the input data.

OBJECTIVE:
Turn the supplied performance data, visual trends, category breakdowns, and data-quality notes into a clear executive-level narrative. The report should explain what changed, why it changed, what requires attention, and what actions should be taken.

INPUTS:
- VISUAL TRENDS: [data provided]
- CATEGORY BREAKDOWNS: [data provided]
- DATA QUALITY NOTES: [data provided]

REPORT STRUCTURE:

1. HEADLINE
Write ONE punchy sentence identifying the single most significant movement in the data.

Requirements:
- Prioritise the largest or most strategically significant movement explicitly shown in the data.
- Include the relevant metric and direction of movement where available.
- Do not introduce interpretation that is unsupported by the data.
- Avoid vague headlines such as "Performance was mixed this month."

2. WHAT MOVED
Explain the key movement in the primary metric.

Requirements:
- Use the exact figures provided in VISUAL TRENDS.
- Clearly state the direction of change (increase, decrease, stable, etc.) where explicitly provided.
- Highlight the most important change first.
- Compare periods only where the comparison is explicitly provided.
- Do NOT calculate percentage changes, absolute changes, averages, totals, rankings, or other derived figures.
- Do NOT infer causation from the trend alone.

3. WHAT'S DRIVING IT
Analyse the CATEGORY BREAKDOWNS to explain which categories are contributing to the overall picture.

Requirements:
- Identify the categories explicitly shown as leading or trailing.
- Use exact figures provided in the input.
- Highlight meaningful differences or movements between categories where these are directly stated or visible in the supplied data.
- Distinguish between correlation/association and causation.
- Do not invent explanations for why a category is performing differently unless the input explicitly provides one.

4. WHAT TO WATCH
Identify the most important risks, anomalies, or areas requiring attention.

Prioritise:
- Unusual spikes or drops.
- Negative trends.
- Data-quality issues that could affect interpretation.
- Categories showing deterioration.
- Areas where the data is incomplete, inconsistent, or potentially unreliable.

Requirements:
- Reference the relevant DATA QUALITY NOTES where applicable.
- Clearly distinguish a genuine performance concern from a potential data-quality issue.
- Do not overstate a risk when the underlying data is uncertain.

5. RECOMMENDATIONS
Provide exactly 3 specific, actionable recommendations based directly on the data.

Each recommendation must:
- Address a specific movement, category, anomaly, or data-quality issue identified above.
- Explain what should be done and what prompted the action.
- Be concrete enough for a team to act on immediately.
- Use the relevant figures/categories from the input where appropriate.

GOOD:
"Investigate the 20% drop in Category X and identify the underlying cause before the next reporting cycle."

BAD:
"Monitor Category X closely."

BAD:
"Continue to optimise performance."

RULES:
- Use ONLY the information provided in the input.
- NEVER calculate or derive new numbers.
- NEVER invent missing data, explanations, causes, or context.
- Use exact figures as provided.
- If the data does not support a conclusion, explicitly say that the cause cannot be determined from the available data.
- If a trend is negative, describe the risk honestly and directly.
- Do not soften negative findings with unnecessary positive language.
- Do not make recommendations that are unrelated to a specific finding.
- Avoid generic corporate language, filler, and repetition.
- Be concise, analytical, and professional.
- Write for an executive/corporate audience.
- Prioritise insight over description.

OUTPUT FORMAT:

# [HEADLINE]

## What Moved
[Concise analysis]

## What's Driving It
[Concise analysis]

## What to Watch
[Concise analysis]

## Recommendations
1. [Specific action]
2. [Specific action]
3. [Specific action]
    """
    try:
        return llm.ask_json(prompt, MonthlyNarrative, system="You are a Chief Strategy Officer."), True
    except llm.LLMUnavailable:
        # Fallback logic remains the same
        return _fallback_monthly(facts), False

def _weekly_narrative(facts, digests):
    context = _build_context(facts, digests)
    prompt = f"""
    {context}

    TASK: Write a Weekly Insights Brief.
    1. HEADLINE: A short summary of the week's mood (e.g., "Strong growth in Tech sector despite overall dip").
    2. INSIGHTS: Provide 3-5 insights. For each:
       - Title: Max 6 words.
       - Detail: Quote the specific change from VISUAL TRENDS (e.g., "Orders fell by 15% to 450").
       - Direction: Choose 'up', 'down', 'flat', or 'watch' based on the data.
    3. WATCHLIST: 2-3 specific anomalies or data quality issues to check next week.
    """
    try:
        return llm.ask_json(prompt, WeeklyNarrative, system="You are a Senior Data Analyst."), True
    except llm.LLMUnavailable:
        return _fallback_weekly(facts), False

# --- Update build_document to pass digests ---
def build_document(kind: str, df, profile, audit_log):
    facts = compute_facts(df, profile, kind, audit_log)
    
    # Generate the chart digests first
    n_charts = {"monthly": 2, "weekly": 1, "visuals": 5}[kind]
    charts = [(s, build_frame(df, s)) for s in plan_charts(df, profile, n_charts)]
    units = {c.name: c.unit for c in profile.columns}
    digests = [digest(f, s, units) for s, f in charts]

    doc = Doc(kind=kind, title=KINDS[kind], notes=audit_log, subtitle=profile.summary)
    
    # Pass digests to the narrative generators
    if kind == "monthly":
        n, ai = _monthly_narrative(facts, digests)
        # ... (rest of your existing block building logic) ...
    elif kind == "weekly":
        n, ai = _weekly_narrative(facts, digests)
        # ... (rest of your existing block building logic) ...
        
    return doc