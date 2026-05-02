"""
report_generator.py — Final Report Assembly

Combines all pipeline outputs into a comprehensive analysis report.
"""

from __future__ import annotations

import base64
import os
from typing import Any

from schemas.models import (
    AnalysisReport, ChartMetadata, CriticFeedback,
    InsightItem, ExecutionStepLog,
)
from utils.helpers import safe_json_serialize


def generate_report(
    session_id: str,
    profile_dict: dict[str, Any],
    execution_log: list[ExecutionStepLog],
    explanations: dict[str, str],
    charts: list[ChartMetadata],
    statistics: dict[str, Any],
    insights: list[InsightItem],
    critic_feedback: CriticFeedback | None,
    validation_notes: list[str],
    rows_before: int,
    rows_after: int,
    cols_before: int,
    cols_after: int,
) -> dict[str, Any]:
    """
    Assemble the final analysis report.

    Returns a JSON-serializable dict containing all pipeline outputs.
    """
    # Dataset overview
    overview = {
        "rows_before_cleaning": rows_before,
        "rows_after_cleaning": rows_after,
        "columns_before_cleaning": cols_before,
        "columns_after_cleaning": cols_after,
        "rows_removed": rows_before - rows_after,
        "columns_removed": cols_before - cols_after,
    }

    # Chart data with base64 encoded images
    chart_data = []
    for chart in charts:
        chart_entry = {
            "chart_type": chart.chart_type,
            "title": chart.title,
            "filename": chart.filename,
            "x_col": chart.x_col,
            "y_col": chart.y_col,
        }
        # Encode image as base64 for frontend
        if os.path.exists(chart.filepath):
            try:
                with open(chart.filepath, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode("utf-8")
                chart_entry["image_base64"] = img_data
            except Exception:
                chart_entry["image_base64"] = None
        chart_data.append(chart_entry)

    # Execution log
    exec_log = [
        {
            "step": log.step,
            "action": log.action,
            "column": log.column,
            "success": log.success,
            "message": log.message,
            "rows_before": log.rows_before,
            "rows_after": log.rows_after,
        }
        for log in execution_log
    ]

    # Insights
    insight_data = [
        {
            "text": ins.text,
            "metric_value": ins.metric_value,
            "comparison": ins.comparison,
            "category": ins.category,
        }
        for ins in insights
    ]

    # Critic feedback
    critic_data = None
    if critic_feedback:
        critic_data = {
            "approved": critic_feedback.approved,
            "quality_score": critic_feedback.quality_score,
            "issues": critic_feedback.issues,
            "corrections": critic_feedback.corrections,
            "summary": critic_feedback.summary,
        }

    report = {
        "session_id": session_id,
        "dataset_overview": overview,
        "profile": safe_json_serialize(profile_dict),
        "cleaning_steps": exec_log,
        "cleaning_explanations": explanations,
        "charts": chart_data,
        "statistics": safe_json_serialize(statistics),
        "insights": insight_data,
        "critic_feedback": critic_data,
        "validation_notes": validation_notes,
    }

    return safe_json_serialize(report)
