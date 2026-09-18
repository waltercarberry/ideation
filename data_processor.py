import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ollama
import json

def get_messy_api_data():
    """Simulates raw, uncleaned API response."""
    dates = [datetime.now() - timedelta(days=i) for i in range(30)]
    values = np.random.normal(loc=100, scale=15, size=30)
    values[5] = np.nan       
    values[12] = 500         
    dates[20] = None         
    df = pd.DataFrame({
        'date': dates,
        'metric_value': values,
        'category': np.random.choice(['A', 'B', 'C'], 30)
    })
    return df

def get_llm_data_profile(df):
    """Uses LLM to understand the structure of ANY raw data."""
    # Send only headers and first 3 rows to save tokens
    sample = df.head(3).to_dict(orient='records')
    prompt = f"""
    Analyze this data sample: {sample}
    Return a JSON object with:
    1. 'date_columns': List of column names that look like dates.
    2. 'numeric_columns': List of column names that contain numbers/currencies.
    3. 'categorical_columns': List of column names for grouping (e.g., company, sector).
    """
    try:
        response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        # In production, use a JSON parser; here we assume the LLM returns clean JSON
        return json.loads(response['message']['content'])
    except:
        return {}

def validate_and_clean(df):
    """Runs stats-heavy checks on ANY dataset."""
    audit_log = []
    
    # 1. Dynamic Column Detection
    profile = get_llm_data_profile(df)
    date_cols = profile.get('date_columns', [])
    numeric_cols = profile.get('numeric_columns', [])
    
    # 2. Date Processing
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        nulls = df[col].isnull().sum()
        if nulls > 0:
            audit_log.append(f"⚠️ {nulls} invalid dates found in '{col}'.")
        df.dropna(subset=[col], inplace=True)

    # 3. Numeric Cleaning & Stats
    summary_stats = {'total_records': len(df)}
    
    for col in numeric_cols:
        # Convert to numeric if needed (handles '£1.2m' etc if we add a helper)
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Null Imputation
        null_count = df[col].isnull().sum()
        if null_count > 0:
            audit_log.append(f"⚠️ Imputed {null_count} missing values in '{col}' with median.")
            df[col] = df[col].fillna(df[col].median())
            
        # Outlier Detection (Z-Score)
        if df[col].std() > 0:
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            outliers = df[z_scores > 3]
            if not outliers.empty:
                audit_log.append(f"🔍 Capped {len(outliers)} outliers in '{col}'.")
                df[col] = df[col].clip(lower=df[col].quantile(0.01), upper=df[col].quantile(0.99))
        
        # Add to stats for the report
        summary_stats[f'avg_{col}'] = round(df[col].mean(), 2)
        summary_stats[f'trend_{col}'] = 'up' if df[col].iloc[-1] > df[col].iloc[0] else 'down'

    return df, audit_log, summary_stats