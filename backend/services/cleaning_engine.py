"""
cleaning_engine.py — Pandas-Based Data Cleaning Engine

Executes individual cleaning operations on a DataFrame.
Each operation is isolated and returns a result tuple for logging.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any


def fill_missing(
    df: pd.DataFrame,
    column: str,
    strategy: str = "mean",
) -> tuple[pd.DataFrame, bool, str]:
    """
    Fill missing values in a column using the specified strategy.

    Parameters
    ----------
    df : pd.DataFrame
    column : str
    strategy : str
        One of 'mean', 'median', 'mode'.

    Returns
    -------
    tuple[pd.DataFrame, bool, str]
        (result_df, success, message)
    """
    df = df.copy()
    if column not in df.columns:
        return df, False, f"Column '{column}' not found."

    missing_before = int(df[column].isna().sum())
    if missing_before == 0:
        return df, True, f"No missing values in '{column}'."

    try:
        if strategy == "mean":
            if pd.api.types.is_numeric_dtype(df[column]):
                df[column] = df[column].fillna(df[column].mean())
            else:
                return df, False, f"Cannot apply mean to non-numeric column '{column}'."

        elif strategy == "median":
            if pd.api.types.is_numeric_dtype(df[column]):
                df[column] = df[column].fillna(df[column].median())
            else:
                return df, False, f"Cannot apply median to non-numeric column '{column}'."

        elif strategy == "mode":
            mode_vals = df[column].mode()
            if len(mode_vals) > 0:
                df[column] = df[column].fillna(mode_vals.iloc[0])
            else:
                return df, False, f"No mode found for '{column}'."

        else:
            return df, False, f"Unknown fill strategy '{strategy}'."

        missing_after = int(df[column].isna().sum())
        return df, True, (
            f"Filled {missing_before - missing_after} missing values in "
            f"'{column}' using {strategy}."
        )

    except Exception as exc:
        return df, False, f"Fill failed on '{column}': {exc}"


def drop_missing(
    df: pd.DataFrame,
    column: str,
    drop: str = "rows",
) -> tuple[pd.DataFrame, bool, str]:
    """
    Drop missing values — either the entire column or rows with NaN.

    Parameters
    ----------
    df : pd.DataFrame
    column : str
    drop : str
        'column' to drop the entire column, 'rows' to drop rows with NaN.
    """
    df = df.copy()
    if column not in df.columns:
        return df, False, f"Column '{column}' not found."

    try:
        if drop == "column":
            df = df.drop(columns=[column])
            return df, True, f"Dropped column '{column}'."
        else:
            rows_before = len(df)
            df = df.dropna(subset=[column])
            rows_dropped = rows_before - len(df)
            return df, True, f"Dropped {rows_dropped} rows with missing '{column}'."

    except Exception as exc:
        return df, False, f"Drop failed on '{column}': {exc}"


def convert_type(
    df: pd.DataFrame,
    column: str,
    dtype: str,
) -> tuple[pd.DataFrame, bool, str]:
    """
    Safely convert a column to a new data type.
    """
    df = df.copy()
    if column not in df.columns:
        return df, False, f"Column '{column}' not found."

    try:
        if dtype in ("datetime", "datetime64"):
            df[column] = pd.to_datetime(df[column], errors="coerce")
        elif dtype in ("int", "int64"):
            df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")
        elif dtype in ("float", "float64"):
            df[column] = pd.to_numeric(df[column], errors="coerce")
        elif dtype in ("str", "string", "object"):
            df[column] = df[column].astype(str)
        elif dtype == "category":
            df[column] = df[column].astype("category")
        else:
            df[column] = df[column].astype(dtype)

        return df, True, f"Converted '{column}' to {dtype}."

    except Exception as exc:
        return df, False, f"Type conversion failed on '{column}': {exc}"


def remove_duplicates(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, bool, str]:
    """Drop duplicate rows from the DataFrame."""
    df = df.copy()
    try:
        rows_before = len(df)
        df = df.drop_duplicates()
        rows_dropped = rows_before - len(df)
        return df, True, f"Removed {rows_dropped} duplicate rows."
    except Exception as exc:
        return df, False, f"Duplicate removal failed: {exc}"


def normalize_column(
    df: pd.DataFrame,
    column: str,
    method: str = "minmax",
) -> tuple[pd.DataFrame, bool, str]:
    """
    Normalize a numeric column using min-max or z-score normalization.
    """
    df = df.copy()
    if column not in df.columns:
        return df, False, f"Column '{column}' not found."

    if not pd.api.types.is_numeric_dtype(df[column]):
        return df, False, f"Cannot normalize non-numeric column '{column}'."

    try:
        if method == "minmax":
            col_min = df[column].min()
            col_max = df[column].max()
            if col_max - col_min == 0:
                return df, False, f"Cannot min-max normalize '{column}': zero range."
            df[column] = (df[column] - col_min) / (col_max - col_min)

        elif method == "zscore":
            col_mean = df[column].mean()
            col_std = df[column].std()
            if col_std == 0:
                return df, False, f"Cannot z-score normalize '{column}': zero std dev."
            df[column] = (df[column] - col_mean) / col_std

        else:
            return df, False, f"Unknown normalization method '{method}'."

        return df, True, f"Normalized '{column}' using {method}."

    except Exception as exc:
        return df, False, f"Normalization failed on '{column}': {exc}"


def execute_cleaning_step(
    df: pd.DataFrame,
    action: str,
    column: str = "",
    params: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, bool, str]:
    """
    Dispatch a single cleaning step to the appropriate function.

    Parameters
    ----------
    df : pd.DataFrame
    action : str
        One of: fill_missing, drop_missing, convert_type,
        remove_duplicates, normalize
    column : str
    params : dict

    Returns
    -------
    tuple[pd.DataFrame, bool, str]
        (result_df, success, message)
    """
    params = params or {}

    if action == "fill_missing":
        strategy = params.get("strategy", "mean")
        return fill_missing(df, column, strategy)

    elif action == "drop_missing":
        drop_type = params.get("drop", "rows")
        return drop_missing(df, column, drop_type)

    elif action == "convert_type":
        dtype = params.get("dtype", "")
        if not dtype:
            return df, False, "No target dtype specified for convert_type."
        return convert_type(df, column, dtype)

    elif action == "remove_duplicates":
        return remove_duplicates(df)

    elif action == "normalize":
        method = params.get("method", "minmax")
        return normalize_column(df, column, method)

    # Legacy action mappings (from V1 planner format)
    elif action == "fillna_mean":
        return fill_missing(df, column, "mean")
    elif action == "fillna_median":
        return fill_missing(df, column, "median")
    elif action == "fillna_mode":
        return fill_missing(df, column, "mode")
    elif action == "drop_column":
        return drop_missing(df, column, "column")
    elif action == "drop_na_rows":
        return drop_missing(df, column, "rows")
    elif action == "drop_duplicates":
        return remove_duplicates(df)

    else:
        return df, False, f"Unknown action '{action}'."
