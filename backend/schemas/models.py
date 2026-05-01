"""
models.py — Pydantic Models for All Data Structures

Provides strict type validation for agent inputs/outputs,
API request/response bodies, and internal data structures.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Dataset Profiling
# ---------------------------------------------------------------------------

class ColumnProfile(BaseModel):
    """Profile for a single column in the dataset."""
    name: str
    dtype: str
    missing_count: int = 0
    missing_pct: float = 0.0
    unique_count: int = 0
    skewness: Optional[float] = None
    outlier_count: int = 0
    sample_values: list[Any] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    """Complete dataset profile."""
    row_count: int
    column_count: int
    columns: dict[str, ColumnProfile]
    duplicate_rows: int = 0
    correlations: Optional[dict[str, dict[str, float]]] = None


# ---------------------------------------------------------------------------
# Planner Agent
# ---------------------------------------------------------------------------

class CleaningStep(BaseModel):
    """A single cleaning operation."""
    action: str
    column: str = ""
    params: dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""


class VisualizationSpec(BaseModel):
    """Specification for a single chart."""
    chart_type: str  # line, bar, histogram, heatmap
    x: str = ""
    y: str = ""
    title: str = ""
    aggregation: str = ""  # mean, sum, count, etc.


class PlannerOutput(BaseModel):
    """Structured output from the Planner Agent."""
    cleaning_steps: list[CleaningStep] = Field(default_factory=list)
    visualization_plan: list[VisualizationSpec] = Field(default_factory=list)
    insight_focus: str = ""
    explanations: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Critic Agent
# ---------------------------------------------------------------------------

class CriticFeedback(BaseModel):
    """Validation feedback from the Critic Agent."""
    approved: bool = False
    quality_score: float = 0.0  # 0.0 to 1.0
    issues: list[str] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)
    summary: str = ""


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

class InsightItem(BaseModel):
    """A single business insight."""
    text: str
    metric_value: str = ""
    comparison: str = ""
    category: str = ""  # trend, anomaly, pattern, recommendation


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

class ChartMetadata(BaseModel):
    """Metadata for a generated chart."""
    chart_type: str
    filepath: str
    filename: str
    title: str
    x_col: str = ""
    y_col: str = ""


# ---------------------------------------------------------------------------
# Execution Log
# ---------------------------------------------------------------------------

class ExecutionStepLog(BaseModel):
    """Log entry for a single execution step."""
    step: str
    action: str
    column: str = ""
    success: bool = True
    message: str = ""
    rows_before: int = 0
    rows_after: int = 0


# ---------------------------------------------------------------------------
# Analysis Report
# ---------------------------------------------------------------------------

class AnalysisReport(BaseModel):
    """Complete analysis report combining all outputs."""
    session_id: str
    dataset_overview: dict[str, Any] = Field(default_factory=dict)
    profile: Optional[dict[str, Any]] = None
    cleaning_steps: list[dict[str, Any]] = Field(default_factory=list)
    cleaning_explanations: dict[str, str] = Field(default_factory=dict)
    execution_log: list[dict[str, Any]] = Field(default_factory=list)
    charts: list[dict[str, Any]] = Field(default_factory=list)
    statistics: dict[str, Any] = Field(default_factory=dict)
    insights: list[dict[str, Any]] = Field(default_factory=list)
    critic_feedback: Optional[dict[str, Any]] = None
    validation_notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API Models
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    """Response after file upload."""
    session_id: str
    filename: str
    rows: int
    columns: int
    message: str = "File uploaded successfully"


class AnalysisStatus(BaseModel):
    """Pipeline progress status."""
    session_id: str
    status: str  # pending, profiling, planning, validating, cleaning, visualizing, analyzing, critiquing, complete, error
    current_step: str = ""
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""


class QueryRequest(BaseModel):
    """Natural language query request."""
    question: str
    session_id: str


class QueryResponse(BaseModel):
    """Natural language query response."""
    question: str
    answer: str
    supporting_data: Optional[dict[str, Any]] = None
    query_code: str = ""
