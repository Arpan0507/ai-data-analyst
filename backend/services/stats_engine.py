"""
stats_engine.py — Statistical Summary Generator

Computes structured statistical summaries of cleaned data including
trends, growth rates, top categories, and key metrics.
Provides structured JSON input for the Insight Agent.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any

from utils.helpers import to_native, safe_json_serialize


def generate_statistics(df: pd.DataFrame) -> dict[str, Any]:
    """
    Generate a comprehensive statistical summary of the cleaned DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The cleaned dataset.

    Returns
    -------
    dict
        Structured statistics including:
        - numeric_summary: per-column stats
        - categorical_summary: top categories
        - trends: time-based trends (if applicable)
        - growth_rates: period-over-period changes
        - key_metrics: overall dataset metrics
    """
    result: dict[str, Any] = {
        "numeric_summary": {},
        "categorical_summary": {},
        "trends": [],
        "growth_rates": [],
        "key_metrics": {},
    }

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

    # Detect datetime-like object columns
    for col in list(categorical_cols):
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().sum() > len(df) * 0.6:
                datetime_cols.append(col)
                categorical_cols.remove(col)
        except Exception:
            pass

    # --- Numeric Summary ---
    for col in numeric_cols:
        try:
            series = df[col].dropna()
            if len(series) == 0:
                continue

            result["numeric_summary"][col] = {
                "mean": to_native(series.mean()),
                "median": to_native(series.median()),
                "std": to_native(series.std()),
                "min": to_native(series.min()),
                "max": to_native(series.max()),
                "q25": to_native(series.quantile(0.25)),
                "q75": to_native(series.quantile(0.75)),
                "skewness": to_native(series.skew()),
                "range": to_native(series.max() - series.min()),
                "cv": to_native(series.std() / series.mean()) if series.mean() != 0 else None,
            }
        except Exception:
            continue

    # --- Categorical Summary ---
    for col in categorical_cols:
        try:
            counts = df[col].value_counts()
            total = len(df[col].dropna())

            result["categorical_summary"][col] = {
                "unique_count": int(df[col].nunique()),
                "top_5": {
                    str(k): {
                        "count": int(v),
                        "percentage": round(v / total * 100, 2) if total > 0 else 0,
                    }
                    for k, v in counts.head(5).items()
                },
                "most_common": str(counts.index[0]) if len(counts) > 0 else None,
                "least_common": str(counts.index[-1]) if len(counts) > 0 else None,
            }
        except Exception:
            continue

    # --- Time-based Trends ---
    for dt_col in datetime_cols[:2]:
        for num_col in numeric_cols[:3]:
            try:
                temp = df[[dt_col, num_col]].copy()
                temp[dt_col] = pd.to_datetime(temp[dt_col], errors="coerce")
                temp = temp.dropna()

                if len(temp) < 2:
                    continue

                temp = temp.sort_values(dt_col)

                # Determine appropriate frequency
                date_range = (temp[dt_col].max() - temp[dt_col].min()).days
                if date_range > 365:
                    freq = "QE"
                    freq_label = "quarterly"
                elif date_range > 60:
                    freq = "ME"
                    freq_label = "monthly"
                else:
                    freq = "W"
                    freq_label = "weekly"

                grouped = temp.set_index(dt_col).resample(freq)[num_col].mean()

                if len(grouped) >= 2:
                    first_val = to_native(grouped.iloc[0])
                    last_val = to_native(grouped.iloc[-1])
                    change = last_val - first_val if (first_val is not None and last_val is not None) else None
                    pct_change = (
                        round((change / abs(first_val)) * 100, 2)
                        if first_val and first_val != 0 and change is not None
                        else None
                    )

                    result["trends"].append({
                        "metric": num_col,
                        "time_column": dt_col,
                        "frequency": freq_label,
                        "direction": "up" if (change and change > 0) else "down" if (change and change < 0) else "flat",
                        "first_value": first_val,
                        "last_value": last_val,
                        "absolute_change": to_native(change),
                        "percentage_change": pct_change,
                        "num_periods": len(grouped),
                    })

            except Exception:
                continue

    # --- Growth Rates ---
    for dt_col in datetime_cols[:1]:
        for num_col in numeric_cols[:3]:
            try:
                temp = df[[dt_col, num_col]].copy()
                temp[dt_col] = pd.to_datetime(temp[dt_col], errors="coerce")
                temp = temp.dropna().sort_values(dt_col)

                if len(temp) < 2:
                    continue

                monthly = temp.set_index(dt_col).resample("ME")[num_col].sum()
                if len(monthly) >= 2:
                    pct_changes = monthly.pct_change().dropna()
                    if len(pct_changes) > 0:
                        result["growth_rates"].append({
                            "metric": num_col,
                            "avg_monthly_growth": to_native(round(pct_changes.mean() * 100, 2)),
                            "max_monthly_growth": to_native(round(pct_changes.max() * 100, 2)),
                            "min_monthly_growth": to_native(round(pct_changes.min() * 100, 2)),
                        })
            except Exception:
                continue

    # --- Key Metrics ---
    result["key_metrics"] = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "numeric_columns": len(numeric_cols),
        "categorical_columns": len(categorical_cols),
        "datetime_columns": len(datetime_cols),
        "total_missing": int(df.isna().sum().sum()),
        "missing_percentage": round(df.isna().sum().sum() / (len(df) * len(df.columns)) * 100, 2)
        if len(df) * len(df.columns) > 0 else 0,
    }

    return safe_json_serialize(result)


def stats_summary_text(stats: dict[str, Any]) -> str:
    """Create a text summary of statistics for LLM consumption."""
    parts = []

    # Key metrics
    km = stats.get("key_metrics", {})
    parts.append(
        f"Dataset: {km.get('total_rows', '?')} rows, "
        f"{km.get('total_columns', '?')} columns "
        f"({km.get('numeric_columns', 0)} numeric, "
        f"{km.get('categorical_columns', 0)} categorical)"
    )

    # Numeric highlights
    num_summary = stats.get("numeric_summary", {})
    if num_summary:
        parts.append("\nNumeric Column Highlights:")
        for col, s in num_summary.items():
            parts.append(
                f"  {col}: mean={s.get('mean')}, median={s.get('median')}, "
                f"range=[{s.get('min')}, {s.get('max')}]"
            )

    # Categorical highlights
    cat_summary = stats.get("categorical_summary", {})
    if cat_summary:
        parts.append("\nCategorical Column Highlights:")
        for col, s in cat_summary.items():
            parts.append(
                f"  {col}: {s.get('unique_count', '?')} unique values, "
                f"most common: {s.get('most_common', '?')}"
            )

    # Trends
    trends = stats.get("trends", [])
    if trends:
        parts.append("\nTrends:")
        for t in trends:
            parts.append(
                f"  {t['metric']}: {t['direction']} "
                f"({t.get('percentage_change', '?')}% change over {t.get('num_periods', '?')} periods)"
            )

    return "\n".join(parts)
