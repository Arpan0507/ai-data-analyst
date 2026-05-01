"""
planner_agent.py — LLM-Powered Planner Agent

Takes a dataset profile and generates a structured JSON execution plan
covering cleaning steps, visualization plan, insight focus areas,
and explanations for each decision.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from utils.llm_client import json_completion
from services.profiling import profile_summary_text, profile_to_dict
from schemas.models import DatasetProfile, PlannerOutput


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
PLANNER_SYSTEM_PROMPT = """\
You are a senior data engineering and analytics assistant. The user will provide
a dataset profile (column names, types, missing-value stats, skewness, outliers,
correlations). You must return ONLY a valid JSON object — no markdown fences,
no explanation text outside the JSON.

The JSON MUST have exactly these four keys:

1. "cleaning_steps" — a list of objects, each with keys:
   {"action", "column", "params", "explanation"}
   Valid actions: fill_missing, drop_missing, convert_type, remove_duplicates, normalize
   For fill_missing, params must include {"strategy": "mean"|"median"|"mode"}
   Choose median for skewed columns (|skewness| > 1).
   For convert_type, params must include {"dtype": "target_type"}

2. "visualization_plan" — a list of objects, each with keys:
   {"chart_type", "x", "y", "title", "aggregation"}
   Valid chart_types: line, bar, histogram, heatmap
   For histogram, only "x" is needed (y can be empty).
   For heatmap, both x and y can be empty (uses all numeric columns).
   aggregation can be: mean, sum, count, or empty string.

3. "insight_focus" — a string describing what business areas the analysis
   should focus on (e.g., "revenue trends and customer segmentation").

4. "explanations" — an object mapping step descriptions to reasoning
   (e.g., {"fill_missing_age": "Age has 12% missing values, using median due to right skew"})

Rules:
- Do NOT hardcode specific values; reference column names from the profile.
- Do NOT suggest dropping columns with less than 5% missing data.
- Suggest 3-6 cleaning steps and 3-5 visualizations.
- Return ONLY the JSON object.
"""


def generate_plan(
    profile: DatasetProfile,
    memory_context: str = "",
) -> PlannerOutput:
    """
    Ask the LLM to produce an execution plan based on the dataset profile.

    Parameters
    ----------
    profile : DatasetProfile
        The dataset profile from profiling engine.
    memory_context : str
        Optional context from past analyses (FAISS memory).

    Returns
    -------
    PlannerOutput
        Structured plan with cleaning steps, visualization plan,
        insight focus, and explanations.

    Raises
    ------
    ValueError
        If the LLM fails to return valid JSON after retries.
    """
    profile_dict = profile_to_dict(profile)
    profile_text = profile_summary_text(profile)

    user_prompt = (
        "Here is the dataset profile:\n\n"
        f"{json.dumps(profile_dict, indent=2)}\n\n"
        "Summary:\n"
        f"{profile_text}\n\n"
    )

    if memory_context:
        user_prompt += (
            "Context from previous analyses:\n"
            f"{memory_context}\n\n"
        )

    user_prompt += "Generate the execution plan as described."

    result = json_completion(
        prompt=user_prompt,
        system_prompt=PLANNER_SYSTEM_PROMPT,
        max_tokens=2048,
        required_keys=["cleaning_steps", "visualization_plan", "insight_focus", "explanations"],
    )

    # Parse into PlannerOutput
    return _parse_planner_output(result)


def _parse_planner_output(raw: dict[str, Any]) -> PlannerOutput:
    """Convert raw JSON dict to a PlannerOutput model."""
    cleaning_steps = []
    for step in raw.get("cleaning_steps", []):
        cleaning_steps.append({
            "action": step.get("action") or "",
            "column": step.get("column") or "",
            "params": step.get("params") or {},
            "explanation": step.get("explanation") or "",
        })

    viz_plan = []
    for viz in raw.get("visualization_plan", []):
        viz_plan.append({
            "chart_type": viz.get("chart_type") or "",
            "x": viz.get("x") or "",
            "y": viz.get("y") or "",
            "title": viz.get("title") or "",
            "aggregation": viz.get("aggregation") or "",
        })

    return PlannerOutput(
        cleaning_steps=[
            __import__("schemas.models", fromlist=["CleaningStep"]).CleaningStep(**s)
            for s in cleaning_steps
        ],
        visualization_plan=[
            __import__("schemas.models", fromlist=["VisualizationSpec"]).VisualizationSpec(**v)
            for v in viz_plan
        ],
        insight_focus=raw.get("insight_focus", ""),
        explanations=raw.get("explanations", {}),
    )
