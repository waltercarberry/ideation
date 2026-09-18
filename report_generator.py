

import os
import ollama # Replaces openai
import jinja2
import pandas as pd

# Define your Custom Template (HTML/CSS for Figma-like quality)
TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { font-family: 'Inter', sans-serif; color: #333; padding: 40px; max-width: 800px; margin: auto; }
    h1 { color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
    .stat-box { background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 10px; display: inline-block; width: 30%; text-align: center;}
    .stat-value { font-size: 24px; font-weight: bold; color: #111827; }
    .stat-label { font-size: 12px; color: #6b7280; text-transform: uppercase; }
    .warning-section { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-top: 20px; }
    .insight-text { line-height: 1.6; margin-top: 20px; }
</style>
</head>
<body>
    <h1>{{ title }}</h1>
    <div class="stats-container">
        {% for stat_name, stat_val in stats.items() %}
        <div class="stat-box">
            <div class="stat-value">{{ stat_val }}</div>
            <div class="stat-label">{{ stat_name.replace('_', ' ') }}</div>
        </div>
        {% endfor %}
    </div>
    
    <div class="insight-text">
        {{ llm_analysis }}
    </div>

    {% if warnings %}
    <div class="warning-section">
        <strong>⚠️ Data Quality Notes:</strong>
        <ul>
            {% for warning in warnings %}
            <li>{{ warning }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}
</body>
</html>
"""

def generate_report_artifacts(clean_df, audit_log, summary_stats):
    """Calls Local LLM (Ollama) and renders 3 artifacts."""
    
    # 1. Construct Context-Aware Prompt
    # We format the stats nicely so the LLM can read them easily
    stats_formatted = "\n".join([f"- {k}: {v}" for k, v in summary_stats.items()])
    warnings_formatted = "\n".join(audit_log) if audit_log else "None"

    prompt = f"""
    You are a Senior Data Analyst. Review these statistics:
    {stats_formatted}

    Data Warnings:
    {warnings_formatted}

    Write a concise executive summary (3-4 sentences) interpreting the trend. 
    If there were warnings, mention how they might impact confidence in the numbers.
    Tone: Professional, insightful, direct.
    """
    
    try:
        # 2. Call Local LLM
        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        llm_text = response['message']['content']
        
    except Exception as e:
        llm_text = f"Error calling Local LLM: {str(e)}. Please ensure Ollama is running and the model is pulled."

    # 3. Render Main Report (HTML String)
    template = jinja2.Template(TEMPLATE_HTML)
    html_report = template.render(
        title="Monthly Performance Analysis",
        stats=summary_stats,
        llm_analysis=llm_text,
        warnings=audit_log
    )
    
    # 4. Prepare Secondary Artifacts
    # Artifact 2: Clean CSV Download
    csv_data = clean_df.to_csv(index=False)
    
    # Artifact 3: Error/Audit README (Markdown)
    readme_content = "# Data Audit Log\n\n"
    if audit_log:
        for log in audit_log:
            readme_content += f"- {log}\n"
    else:
        readme_content += "- No anomalies detected.\n"
        
    return html_report, csv_data, readme_content