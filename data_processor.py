import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_messy_api_data():
    """Simulates raw, uncleaned API response."""
    # Generate random dates, some nulls, some outliers
    dates = [datetime.now() - timedelta(days=i) for i in range(30)]
    values = np.random.normal(loc=100, scale=15, size=30)
    
    # Inject "messiness"
    values[5] = np.nan       # Missing value
    values[12] = 500         # Outlier spike
    dates[20] = None         # Bad date format
    
    df = pd.DataFrame({
        'date': dates,
        'metric_value': values,
        'category': np.random.choice(['A', 'B', 'C'], 30)
    })
    return df

def validate_and_clean(df):
    """Runs stats-heavy checks and returns clean DF + Audit Log."""
    audit_log = []
    
    # 1. Check Nulls
    null_count = df['metric_value'].isnull().sum()
    if null_count > 0:
        audit_log.append(f"⚠️ Found {null_count} missing values in 'metric_value'. Imputed with median.")
        df['metric_value'] = df['metric_value'].fillna(df['metric_value'].median())
        
    # 2. Check Outliers (Z-Score)
    z_scores = np.abs((df['metric_value'] - df['metric_value'].mean()) / df['metric_value'].std())
    outliers = df[z_scores > 3]
    if not outliers.empty:
        audit_log.append(f"🔍 Detected {len(outliers)} statistical outliers (>3 std dev). Flagged for review.")
        # Optional: Cap them or keep them? Let's cap for stability in report
        df['metric_value'] = df['metric_value'].clip(lower=df['metric_value'].quantile(0.01), 
                                                      upper=df['metric_value'].quantile(0.99))

    # 3. Date Continuity
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)
    
    # Calculate summary stats for the LLM context
    summary_stats = {
        'total_records': len(df),
        'avg_value': round(df['metric_value'].mean(), 2),
        'max_value': round(df['metric_value'].max(), 2),
        'min_value': round(df['metric_value'].min(), 2),
        'trend_direction': 'upward' if df['metric_value'].iloc[-1] > df['metric_value'].iloc[0] else 'downward'
    }
    
    return df, audit_log, summary_stats