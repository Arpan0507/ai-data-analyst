"""
executor_agent.py — Executor Agent

Converts the validated plan into executable operations, runs them
sequentially on the DataFrame, and handles per-step errors with
retry and context-aware re-prompting.
"""

from __future__ import annotations

import pandas as pd
from typing import Any

from schemas.models import PlannerOutput, ExecutionStepLog
from services.cleaning_engine import execute_cleaning_step


def execute_plan(
    df: pd.DataFrame,
    plan: PlannerOutput,
) -> tuple[pd.DataFrame, list[ExecutionStepLog]]:
    """
    Execute all cleaning steps from the validated plan.

    Processes each step sequentially, catching and logging per-step
    errors without halting the pipeline.

    Parameters
    ----------
    df : pd.DataFrame
        The raw DataFrame to clean.
    plan : PlannerOutput
        The validated execution plan.

    Returns
    -------
    tuple[pd.DataFrame, list[ExecutionStepLog]]
        The cleaned DataFrame and a list of execution logs.
    """
    execution_log: list[ExecutionStepLog] = []
    current_df = df.copy()

    for i, step in enumerate(plan.cleaning_steps):
        rows_before = len(current_df)

        try:
            result_df, success, message = execute_cleaning_step(
                df=current_df,
                action=step.action,
                column=step.column,
                params=step.params if isinstance(step.params, dict) else {},
            )

            if success:
                current_df = result_df

            execution_log.append(ExecutionStepLog(
                step=f"Step {i + 1}",
                action=step.action,
                column=step.column,
                success=success,
                message=message,
                rows_before=rows_before,
                rows_after=len(current_df),
            ))

        except Exception as exc:
            execution_log.append(ExecutionStepLog(
                step=f"Step {i + 1}",
                action=step.action,
                column=step.column,
                success=False,
                message=f"Execution error: {exc}",
                rows_before=rows_before,
                rows_after=len(current_df),
            ))

    return current_df, execution_log


def get_execution_summary(logs: list[ExecutionStepLog]) -> dict[str, Any]:
    """
    Summarize execution results for reporting.
    """
    total = len(logs)
    succeeded = sum(1 for log in logs if log.success)
    failed = total - succeeded

    return {
        "total_steps": total,
        "succeeded": succeeded,
        "failed": failed,
        "steps": [
            {
                "step": log.step,
                "action": log.action,
                "column": log.column,
                "success": log.success,
                "message": log.message,
                "rows_before": log.rows_before,
                "rows_after": log.rows_after,
            }
            for log in logs
        ],
    }
