import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional, Any

# Store session data (in production, use Redis or database)
session_data = {}

def get_time_range(df):
    """Extract time range information from the DataFrame"""
    if 'time' not in df.columns:
        return None
    
    time_series = pd.to_datetime(df['time'])
    min_time = time_series.min()
    max_time = time_series.max()
    
    return {
        'min_date': min_time.strftime('%Y-%m-%d'),
        'max_date': max_time.strftime('%Y-%m-%d'),
        'min_datetime': min_time.strftime('%Y-%m-%dT%H:%M'),
        'max_datetime': max_time.strftime('%Y-%m-%dT%H:%M'),
        'total_days': (max_time - min_time).days + 1,
        'total_records': len(df)
    }

def calculate_statistics(df, data_info):
    """Calculate basic statistics for each available parameter"""
    stats = {}
    
    for parameter_type in ['voltage', 'current', 'power_factor']:
        if data_info[parameter_type]['available']:
            stats[parameter_type] = {}
            for column in data_info[parameter_type]['columns']:
                if column in df.columns:
                    column_data = df[column].dropna()
                    if len(column_data) > 0:
                        stats[parameter_type][column] = {
                            'min': float(column_data.min()),
                            'max': float(column_data.max()),
                            'mean': float(column_data.mean()),
                            'std': float(column_data.std())
                        }
    
    return stats

def _to_json_safe(obj):
    """Recursively convert numpy/pandas types into JSON-serializable Python types."""
    # Primitives and None
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # Numpy scalars
    if isinstance(obj, np.generic):
        return obj.item()

    # Pandas Timestamp
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    # Dict
    if isinstance(obj, dict):
        return {str(_to_json_safe(k)): _to_json_safe(v) for k, v in obj.items()}

    # List or Tuple
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(v) for v in obj]

    # Pandas Series/DataFrame
    if isinstance(obj, pd.Series):
        return [_to_json_safe(v) for v in obj.tolist()]
    if isinstance(obj, pd.DataFrame):
        return [_to_json_safe(rec) for rec in obj.to_dict(orient='records')]

    # Fallback to string
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)
