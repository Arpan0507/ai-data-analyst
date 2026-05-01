"""
helpers.py — Shared Utility Functions

Type conversion, JSON serialization, and text truncation helpers
used across the backend services.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd


def to_native(value: Any) -> Any:
    """Convert numpy / pandas scalar to a JSON-safe Python native type."""
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        v = float(value)
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, (np.ndarray,)):
        return value.tolist()
    if isinstance(value, (pd.Series,)):
        return value.tolist()
    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            return None
    return value


def safe_json_serialize(obj: Any) -> Any:
    """
    Recursively convert an object to JSON-serializable form.

    Handles nested dicts, lists, numpy types, pandas objects,
    and NaN/Inf values.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, bool)):
        return obj
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {str(k): safe_json_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_json_serialize(item) for item in obj]
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    if isinstance(obj, pd.Series):
        return obj.tolist()
    return to_native(obj)


def truncate_for_llm(text: str, max_chars: int = 8000) -> str:
    """
    Truncate text to fit within LLM context limits.

    If the text exceeds max_chars, it is truncated and a note
    is appended indicating the truncation.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n... [TRUNCATED — showing first {max_chars} characters]"


def dataframe_summary_for_llm(df: pd.DataFrame, max_rows: int = 5) -> str:
    """
    Create a concise text summary of a DataFrame for LLM consumption.

    Includes shape, column types, sample rows, and basic stats.
    """
    parts = [
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
        f"Columns: {', '.join(df.columns.tolist())}",
        "",
        "Column Types:",
    ]
    for col in df.columns:
        parts.append(f"  - {col}: {df[col].dtype}")

    parts.append("")
    parts.append(f"First {max_rows} rows:")
    parts.append(df.head(max_rows).to_string(index=False))

    parts.append("")
    parts.append("Descriptive Statistics:")
    try:
        desc = df.describe(include="all").to_string()
        parts.append(truncate_for_llm(desc, max_chars=4000))
    except Exception:
        parts.append("  (Could not compute descriptive statistics)")

    return "\n".join(parts)
