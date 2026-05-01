"""
profiling.py — Dataset Profiling Engine

Generates a comprehensive dataset profile using pure pandas —
NO LLM calls. Includes column stats, skewness, outlier detection,
and correlation matrix.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any, Optional

from utils.helpers import to_native, safe_json_serialize
from schemas.models import ColumnProfile, DatasetProfile


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    """
    Profile the incoming DataFrame comprehensively.

    Computes per-column statistics including missing values, unique counts,
    skewness (for numeric columns), outlier counts (IQR method),
    sample values, and a correlation matrix.

    Parameters
    ----------
    df : pd.DataFrame
        The raw uploaded dataset.

    Returns
    -------
    DatasetProfile
        Complete structured profile of the dataset.
    """
    columns: dict[str, ColumnProfile] = {}

    for col in df.columns:
        missing = int(df[col].isna().sum())
        total = len(df)
        pct = round(missing / total * 100, 2) if total > 0 else 0.0

        # Sample values (non-null)
        non_null = df[col].dropna()
        samples = non_null.head(5).tolist() if len(non_null) > 0 else []
        samples = [to_native(v) for v in samples]

        # Skewness (numeric only)
        skewness: Optional[float] = None
        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                skew_val = float(df[col].skew())
                if not (np.isnan(skew_val) or np.isinf(skew_val)):
                    skewness = round(skew_val, 4)
            except Exception:
                pass

        # Outlier detection via IQR (numeric only)
        outlier_count = 0
        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outlier_count = int(
                        ((df[col] < lower) | (df[col] > upper)).sum()
                    )
            except Exception:
                pass

        columns[col] = ColumnProfile(
            name=col,
            dtype=str(df[col].dtype),
            missing_count=missing,
            missing_pct=pct,
            unique_count=int(df[col].nunique()),
            skewness=skewness,
            outlier_count=outlier_count,
            sample_values=samples,
        )

    # Correlation matrix (numeric columns only)
    correlations: Optional[dict[str, dict[str, float]]] = None
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) >= 2:
        try:
            corr_df = df[numeric_cols].corr()
            correlations = {}
            for c in corr_df.columns:
                correlations[c] = {
                    r: round(to_native(corr_df.loc[r, c]), 4)
                    for r in corr_df.index
                    if not np.isnan(corr_df.loc[r, c])
                }
        except Exception:
            pass

    return DatasetProfile(
        row_count=len(df),
        column_count=len(df.columns),
        columns=columns,
        duplicate_rows=int(df.duplicated().sum()),
        correlations=correlations,
    )


def profile_to_dict(profile: DatasetProfile) -> dict[str, Any]:
    """Convert DatasetProfile to a plain dict for JSON serialization."""
    result = {
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "duplicate_rows": profile.duplicate_rows,
        "columns": {},
        "correlations": profile.correlations,
    }
    for name, col in profile.columns.items():
        result["columns"][name] = {
            "dtype": col.dtype,
            "missing_count": col.missing_count,
            "missing_pct": col.missing_pct,
            "unique_count": col.unique_count,
            "skewness": col.skewness,
            "outlier_count": col.outlier_count,
            "sample_values": col.sample_values,
        }
    return safe_json_serialize(result)


def profile_summary_text(profile: DatasetProfile) -> str:
    """Create a concise text summary of the profile for LLM consumption."""
    lines = [
        f"Dataset: {profile.row_count} rows × {profile.column_count} columns",
        f"Duplicate rows: {profile.duplicate_rows}",
        "",
        "Columns:",
    ]
    for name, col in profile.columns.items():
        parts = [f"  - {name} ({col.dtype})"]
        if col.missing_count > 0:
            parts.append(f"missing={col.missing_count} ({col.missing_pct}%)")
        parts.append(f"unique={col.unique_count}")
        if col.skewness is not None:
            parts.append(f"skew={col.skewness}")
        if col.outlier_count > 0:
            parts.append(f"outliers={col.outlier_count}")
        lines.append(", ".join(parts))

    return "\n".join(lines)
