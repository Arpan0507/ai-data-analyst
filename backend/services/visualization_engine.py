"""
visualization_engine.py — Chart Generation Engine

Generates charts using matplotlib and seaborn based on the
visualization plan. Validates chart types against column data,
auto-aggregates for categorical plots, and limits categories.
Saves charts as PNG files and returns metadata.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import pandas as pd
import numpy as np

from schemas.models import VisualizationSpec, ChartMetadata


# ---------------------------------------------------------------------------
# Style configuration
# ---------------------------------------------------------------------------
_PALETTE = [
    "#6366f1", "#f43f5e", "#0ea5e9", "#10b981",
    "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6",
]

# Apply a dark, modern style
plt.rcParams.update({
    "figure.facecolor": "#0f172a",
    "axes.facecolor": "#1e293b",
    "axes.edgecolor": "#334155",
    "axes.labelcolor": "#e2e8f0",
    "text.color": "#e2e8f0",
    "xtick.color": "#94a3b8",
    "ytick.color": "#94a3b8",
    "grid.color": "#334155",
    "grid.alpha": 0.3,
    "font.family": "sans-serif",
    "font.size": 10,
})


def generate_charts(
    df: pd.DataFrame,
    viz_plan: list[VisualizationSpec],
    output_dir: str = "data/charts",
    session_id: str = "",
) -> list[ChartMetadata]:
    """
    Generate charts based on the visualization plan.

    Parameters
    ----------
    df : pd.DataFrame
        The cleaned DataFrame.
    viz_plan : list[VisualizationSpec]
        Chart specifications from the validated plan.
    output_dir : str
        Directory to save chart PNGs.
    session_id : str
        Session identifier for file naming.

    Returns
    -------
    list[ChartMetadata]
        Metadata for each generated chart.
    """
    os.makedirs(output_dir, exist_ok=True)
    charts: list[ChartMetadata] = []
    color_idx = 0

    for spec in viz_plan:
        try:
            chart_type = spec.chart_type.lower()

            if chart_type == "histogram":
                meta = _generate_histogram(df, spec, output_dir, session_id, color_idx)
            elif chart_type == "bar":
                meta = _generate_bar_chart(df, spec, output_dir, session_id, color_idx)
            elif chart_type == "line":
                meta = _generate_line_chart(df, spec, output_dir, session_id, color_idx)
            elif chart_type == "heatmap":
                meta = _generate_heatmap(df, spec, output_dir, session_id, color_idx)
            else:
                continue

            if meta:
                charts.append(meta)
                color_idx += 1

        except Exception:
            continue

    # If no charts from plan, auto-generate based on data types
    if not charts:
        charts = _auto_generate_charts(df, output_dir, session_id)

    return charts


# ---------------------------------------------------------------------------
# Chart generators
# ---------------------------------------------------------------------------

def _generate_histogram(
    df: pd.DataFrame,
    spec: VisualizationSpec,
    output_dir: str,
    session_id: str,
    color_idx: int,
) -> ChartMetadata | None:
    """Generate a histogram for numeric column distribution."""
    col = spec.x
    if col not in df.columns:
        return None
    if not pd.api.types.is_numeric_dtype(df[col]):
        return None

    data = df[col].dropna()
    if len(data) == 0:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    bins = max(5, min(int(np.ceil(np.log2(len(data)) + 1)), 50))
    color = _PALETTE[color_idx % len(_PALETTE)]

    ax.hist(data, bins=bins, color=color, edgecolor="#0f172a", linewidth=0.8, alpha=0.85)
    ax.set_title(spec.title or f"Distribution of {col}", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(col, fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.2)

    return _save_chart(fig, output_dir, session_id, "histogram", col, spec)


def _generate_bar_chart(
    df: pd.DataFrame,
    spec: VisualizationSpec,
    output_dir: str,
    session_id: str,
    color_idx: int,
) -> ChartMetadata | None:
    """Generate a bar chart for category vs numeric data."""
    x_col = spec.x
    y_col = spec.y
    color = _PALETTE[color_idx % len(_PALETTE)]

    if x_col not in df.columns:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))

    if y_col and y_col in df.columns:
        # Category vs numeric with aggregation
        top_cats = df[x_col].value_counts().head(10).index.tolist()
        subset = df[df[x_col].isin(top_cats)]
        agg = spec.aggregation or "mean"

        try:
            grouped = subset.groupby(x_col)[y_col].agg(agg).sort_values(ascending=False)
        except Exception:
            grouped = subset.groupby(x_col)[y_col].mean().sort_values(ascending=False)

        ax.bar(
            grouped.index.astype(str), grouped.values,
            color=color, edgecolor="#0f172a", linewidth=0.8, alpha=0.85,
        )
        ax.set_ylabel(f"{agg.title()} {y_col}", fontsize=11)
        title = spec.title or f"{agg.title()} {y_col} by {x_col}"
    else:
        # Value counts
        counts = df[x_col].value_counts().head(10)
        ax.bar(
            counts.index.astype(str), counts.values,
            color=color, edgecolor="#0f172a", linewidth=0.8, alpha=0.85,
        )
        ax.set_ylabel("Count", fontsize=11)
        title = spec.title or f"Top Categories in {x_col}"

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(x_col, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    ax.grid(axis="y", alpha=0.2)

    return _save_chart(fig, output_dir, session_id, "bar", x_col, spec)


def _generate_line_chart(
    df: pd.DataFrame,
    spec: VisualizationSpec,
    output_dir: str,
    session_id: str,
    color_idx: int,
) -> ChartMetadata | None:
    """Generate a line chart for time series data."""
    x_col = spec.x
    y_col = spec.y
    color = _PALETTE[color_idx % len(_PALETTE)]

    if x_col not in df.columns or y_col not in df.columns:
        return None

    temp = df[[x_col, y_col]].copy()
    temp[x_col] = pd.to_datetime(temp[x_col], errors="coerce")
    temp = temp.dropna(subset=[x_col, y_col])
    temp = temp.sort_values(x_col)

    if len(temp) == 0:
        return None

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(temp[x_col], temp[y_col], color=color, linewidth=2, alpha=0.9)
    ax.fill_between(temp[x_col], temp[y_col], alpha=0.1, color=color)

    ax.set_title(spec.title or f"{y_col} over Time", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(x_col, fontsize=11)
    ax.set_ylabel(y_col, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="both", alpha=0.2)
    fig.autofmt_xdate()

    return _save_chart(fig, output_dir, session_id, "line", x_col, spec)


def _generate_heatmap(
    df: pd.DataFrame,
    spec: VisualizationSpec,
    output_dir: str,
    session_id: str,
    color_idx: int,
) -> ChartMetadata | None:
    """Generate a correlation heatmap."""
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) < 2:
        return None

    corr = df[numeric_cols].corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        center=0,
        vmin=-1,
        vmax=1,
        ax=ax,
        square=True,
        linewidths=0.5,
        linecolor="#0f172a",
        cbar_kws={"shrink": 0.8},
        annot_kws={"size": 8, "color": "#0f172a"},
    )
    ax.set_title(
        spec.title or "Correlation Matrix",
        fontsize=14, fontweight="bold", pad=12, color="#e2e8f0",
    )
    ax.tick_params(axis="both", labelsize=9)

    return _save_chart(fig, output_dir, session_id, "heatmap", "correlation", spec)


# ---------------------------------------------------------------------------
# Auto-generation fallback
# ---------------------------------------------------------------------------

def _auto_generate_charts(
    df: pd.DataFrame,
    output_dir: str,
    session_id: str,
) -> list[ChartMetadata]:
    """Auto-generate charts when no plan is available."""
    charts: list[ChartMetadata] = []
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Histograms for first 3 numeric columns
    for i, col in enumerate(numeric_cols[:3]):
        spec = VisualizationSpec(chart_type="histogram", x=col, title=f"Distribution of {col}")
        meta = _generate_histogram(df, spec, output_dir, session_id, i)
        if meta:
            charts.append(meta)

    # Bar charts for first 2 categorical vs first numeric
    if numeric_cols and categorical_cols:
        for i, cat_col in enumerate(categorical_cols[:2]):
            spec = VisualizationSpec(
                chart_type="bar", x=cat_col, y=numeric_cols[0],
                title=f"Mean {numeric_cols[0]} by {cat_col}",
                aggregation="mean",
            )
            meta = _generate_bar_chart(df, spec, output_dir, session_id, len(numeric_cols) + i)
            if meta:
                charts.append(meta)

    # Heatmap if enough numeric columns
    if len(numeric_cols) >= 2:
        spec = VisualizationSpec(chart_type="heatmap", title="Correlation Matrix")
        meta = _generate_heatmap(df, spec, output_dir, session_id, 0)
        if meta:
            charts.append(meta)

    return charts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import base64
import io

def _save_chart(
    fig: plt.Figure,
    output_dir: str,
    session_id: str,
    chart_type: str,
    col_name: str,
    spec: VisualizationSpec,
) -> ChartMetadata:
    """
    Save a matplotlib figure (optional) and return metadata with Base64 encoding.
    
    This ensures charts work on platforms without persistent storage (like Render free).
    """
    filename = f"{session_id}_{chart_type}_{col_name}_{uuid.uuid4().hex[:6]}.png"
    filepath = os.path.join(output_dir, filename)
    fig.tight_layout()

    # 1. Generate Base64 version (Memory-safe)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    # 2. Try to save to disk (Optional/Best effort)
    try:
        os.makedirs(output_dir, exist_ok=True)
        fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    except Exception:
        # Ignore disk errors on ephemeral platforms
        filepath = None
        filename = None

    plt.close(fig)

    return ChartMetadata(
        chart_type=chart_type,
        filepath=filepath,
        filename=filename,
        image_base64=image_base64,
        title=spec.title or f"{chart_type} of {col_name}",
        x_col=spec.x,
        y_col=spec.y,
    )
