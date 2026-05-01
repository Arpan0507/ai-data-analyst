"""
validation.py — Rule-Based Safety Validation Layer

Intercepts the LLM-generated execution plan and applies deterministic
guardrail rules before execution. Prevents unsafe operations and
corrects the plan based on dataset characteristics.
"""

from __future__ import annotations

import copy
from typing import Any

from schemas.models import PlannerOutput, DatasetProfile, CleaningStep, VisualizationSpec


# ---------------------------------------------------------------------------
# Fill action identifiers
# ---------------------------------------------------------------------------
_FILL_ACTIONS = {"fill_missing", "fillna_mean", "fillna_median", "fillna_mode", "fillna_value"}
_NUMERIC_CHART_TYPES = {"histogram", "heatmap"}
_CATEGORICAL_CHART_TYPES = {"bar"}
_TIME_CHART_TYPES = {"line"}


def validate_plan(
    plan: PlannerOutput,
    profile: DatasetProfile,
) -> tuple[PlannerOutput, list[str]]:
    """
    Apply deterministic guardrail rules to the LLM plan.

    Rules
    -----
    1. If a column has > 40% missing, replace fill with drop_missing.
    2. If a column is 100% missing, force drop the column entirely.
    3. If a numeric column is skewed (|skewness| > 1), prefer median
       over mean for fill operations.
    4. Do NOT drop columns with < 5% missing data.
    5. Remove steps referencing non-existent columns.
    6. Validate chart types against column data types.

    Parameters
    ----------
    plan : PlannerOutput
        The raw plan from the Planner Agent.
    profile : DatasetProfile
        The dataset profile.

    Returns
    -------
    tuple[PlannerOutput, list[str]]
        The corrected plan and a list of applied corrections.
    """
    corrections: list[str] = []
    valid_columns = set(profile.columns.keys())
    dropped_columns: set[str] = set()

    # --- Validate cleaning steps ---
    corrected_steps: list[CleaningStep] = []

    for step in plan.cleaning_steps:
        try:
            action = step.action
            column = step.column

            # Rule 5: skip steps targeting non-existent columns
            if column and column not in valid_columns:
                corrections.append(
                    f"Removed step '{action}' on '{column}': column does not exist."
                )
                continue

            col_info = profile.columns.get(column)

            if col_info:
                missing_pct = col_info.missing_pct

                # Rule 2: 100% missing — drop the column
                if missing_pct >= 100 and action in _FILL_ACTIONS:
                    if column not in dropped_columns:
                        corrected_steps.append(CleaningStep(
                            action="drop_missing",
                            column=column,
                            params={"drop": "column"},
                            explanation=f"Column is 100% missing — dropping entirely.",
                        ))
                        dropped_columns.add(column)
                        corrections.append(
                            f"Changed fill on '{column}' to drop: column is 100% missing."
                        )
                    continue

                # Rule 1: > 40% missing — don't fill, drop rows or column
                if missing_pct > 40 and action in _FILL_ACTIONS:
                    if column not in dropped_columns:
                        corrected_steps.append(CleaningStep(
                            action="drop_missing",
                            column=column,
                            params={"drop": "column"},
                            explanation=f"Column has {missing_pct}% missing (>40%) — dropping instead of filling.",
                        ))
                        dropped_columns.add(column)
                        corrections.append(
                            f"Changed fill on '{column}' to drop: {missing_pct}% missing exceeds 40% threshold."
                        )
                    continue

                # Rule 4: Don't drop columns with < 5% missing
                if (action == "drop_missing" and
                    step.params.get("drop") == "column" and
                    missing_pct < 5 and missing_pct > 0):
                    # Convert to fill instead
                    strategy = "median" if (col_info.skewness and abs(col_info.skewness) > 1) else "mean"
                    if not _is_numeric_dtype(col_info.dtype):
                        strategy = "mode"
                    corrected_steps.append(CleaningStep(
                        action="fill_missing",
                        column=column,
                        params={"strategy": strategy},
                        explanation=f"Column has only {missing_pct}% missing — filling with {strategy} instead of dropping.",
                    ))
                    corrections.append(
                        f"Changed drop on '{column}' to fill ({strategy}): only {missing_pct}% missing."
                    )
                    continue

                # Rule 3: Skewed columns should use median
                if (action == "fill_missing" and
                    col_info.skewness is not None and
                    abs(col_info.skewness) > 1 and
                    step.params.get("strategy") == "mean"):
                    corrected_step = step.model_copy()
                    corrected_step.params = {**step.params, "strategy": "median"}
                    corrected_step.explanation = (
                        f"Column is skewed (skewness={col_info.skewness}) — "
                        f"using median instead of mean."
                    )
                    corrected_steps.append(corrected_step)
                    corrections.append(
                        f"Changed fill strategy on '{column}' from mean to median: "
                        f"skewness={col_info.skewness}."
                    )
                    continue

            # Default: keep the step as-is
            corrected_steps.append(step)

        except Exception:
            continue

    # --- Validate visualizations ---
    corrected_viz: list[VisualizationSpec] = []

    for viz in plan.visualization_plan:
        try:
            x_col = viz.x
            y_col = viz.y

            # Skip if referenced columns were dropped
            if x_col and (x_col not in valid_columns or x_col in dropped_columns):
                corrections.append(
                    f"Removed chart '{viz.title or viz.chart_type}': "
                    f"x-column '{x_col}' is not available."
                )
                continue
            if y_col and (y_col not in valid_columns or y_col in dropped_columns):
                corrections.append(
                    f"Removed chart '{viz.title or viz.chart_type}': "
                    f"y-column '{y_col}' is not available."
                )
                continue

            # Rule 6: Validate chart type vs column type
            if viz.chart_type == "histogram" and x_col:
                col_info = profile.columns.get(x_col)
                if col_info and not _is_numeric_dtype(col_info.dtype):
                    # Convert histogram to bar chart for categorical
                    corrected_viz.append(VisualizationSpec(
                        chart_type="bar",
                        x=x_col,
                        y="",
                        title=viz.title or f"Distribution of {x_col}",
                        aggregation="count",
                    ))
                    corrections.append(
                        f"Changed histogram to bar chart for '{x_col}': column is categorical."
                    )
                    continue

            corrected_viz.append(viz)

        except Exception:
            continue

    corrected_plan = PlannerOutput(
        cleaning_steps=corrected_steps,
        visualization_plan=corrected_viz,
        insight_focus=plan.insight_focus,
        explanations=plan.explanations,
    )

    return corrected_plan, corrections


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_numeric_dtype(dtype_str: str) -> bool:
    """Check if a dtype string represents a numeric type."""
    numeric_indicators = ["int", "float", "number", "numeric", "Int64", "Float64"]
    return any(ind.lower() in dtype_str.lower() for ind in numeric_indicators)
