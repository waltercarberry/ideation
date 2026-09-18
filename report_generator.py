import os
import ollama
import jinja2
import pandas as pd

# Define your Custom Template (HTML/CSS for Figma-like quality)
# Note: We use standard quotes and no 'f' prefix so Python doesn't try to parse the { }
TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #F3F3EE; color: #1B1F3B; padding: 40px; }
    .report-container { 
        background: #FFFFFF; 
        border: 3px solid #1B1F3B; 
        box-shadow: 14px 14px 0 #FF48B0; 
        padding: 40px; 
        max-width: 900px; 
        margin: 0 auto;
    }
    h1 { font-size: 3rem; letter-spacing: -0.04em; line-height: 1; margin-bottom: 30px; color: #1B1F3B; }
    h2 { font-size: 2rem; letter-spacing: -0.03em; border-bottom: 3px solid #FFE800; padding-bottom: 10px; margin-top: 40px; }
    .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
    .stat-card { 
        background: #F3F3EE; 
        border: 2px solid #1B1F3B; 
        padding: 20px; 
        border-radius: 12px;
    }
    .stat-label { font-size: 0.9rem; text-transform: uppercase; font-weight: 700; color: #0078BF; }
    .stat-value { font-size: 1.8rem; font-weight: 700; color: #1B1F3B; margin-top: 5px; }
    .audit-box { 
        background: #FFE800; 
        border: 2px solid #1B1F3B; 
        padding: 20px; 
        border-radius: 12px; 
        margin-top: 30px;
    }
    p { line-height: 1.6; font-size: 1.1rem; }
</style>
</head>
<body>
    <div class="report-container">
        <h1>{{ title }}</h1>
        
        <div class="stat-grid">
            {% for stat_name, stat_val in stats.items() %}
            <div class="stat-card">
                <div class="stat-label">{{ stat_name.replace('_', ' ') }}</div>
                <div class="stat-value">{{ stat_val }}</div>
            </div>
            {% endfor %}
        </div>

        <h2>Executive Summary</h2>
        <p>{{ llm_analysis }}</p>

        {% if warnings %}
        <div class="audit-box">
            <strong>⚠️ Data Quality Notes:</strong>
            <ul style="margin-top: 10px; padding-left: 20px;">
                {% for warning in warnings %}
                <li>{{ warning }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def generate_report_artifacts(clean_df, audit_log, summary_stats):
    """Calls Local LLM (Ollama) and renders artifacts with Riso styling."""
    
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
        response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        llm_text = response['message']['content']
    except Exception as e:
        llm_text = f"Error calling Local LLM: {str(e)}."

    # Use Jinja2 to safely render the template
    template = jinja2.Template(TEMPLATE_HTML)
    html_report = template.render(
        title="Monthly Performance Analysis",
        stats=summary_stats,
        llm_analysis=llm_text,
        warnings=audit_log
    )
    
    csv_data = clean_df.to_csv(index=False)
    readme_content = "# Data Audit Log\n\n" + "\n".join([f"- {log}" for log in audit_log])
        
    return html_report, csv_data, readme_content