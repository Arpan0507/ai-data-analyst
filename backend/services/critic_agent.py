"""
critic_agent.py — LLM-Powered Critic Agent (MANDATORY)

Validates all pipeline outputs: cleaning correctness, chart relevance,
and insight quality. Rejects vague or incorrect outputs and suggests
corrections. Can trigger re-runs of offending agents.
"""

from __future__ import annotations

import json
from typing import Any

from utils.llm_client import json_completion
from schemas.models import CriticFeedback, InsightItem, ChartMetadata

CRITIC_SYSTEM_PROMPT = """\
You are a strict quality assurance analyst reviewing an automated data analysis.
You must validate:
1. Cleaning steps: Were they appropriate? Any data loss concerns?
2. Charts: Are they relevant to the data? Do they tell a meaningful story?
3. Insights: Are they specific, quantitative, and actionable? Reject vague ones.

Return ONLY a valid JSON object:
{
  "approved": true/false,
  "quality_score": 0.0 to 1.0,
  "issues": ["list of problems found"],
  "corrections": ["list of suggested corrections"],
  "summary": "overall assessment"
}

Be strict but fair. Score above 0.7 means approved.
Reject if insights are generic or charts don't match the data.
Return ONLY JSON, no markdown.
"""


def critique_analysis(
    cleaning_log: list[dict[str, Any]],
    charts: list[ChartMetadata],
    insights: list[InsightItem],
    profile_text: str,
    stats_summary: str,
) -> CriticFeedback:
    cleaning_info = json.dumps(cleaning_log, indent=2, default=str)
    charts_info = json.dumps(
        [{"type": c.chart_type, "title": c.title, "x": c.x_col, "y": c.y_col} for c in charts],
        indent=2,
    )
    insights_info = json.dumps(
        [{"text": i.text, "metric": i.metric_value, "category": i.category} for i in insights],
        indent=2,
    )

    user_prompt = (
        f"Dataset Profile:\n{profile_text}\n\n"
        f"Statistics Summary:\n{stats_summary}\n\n"
        f"Cleaning Steps Executed:\n{cleaning_info}\n\n"
        f"Charts Generated:\n{charts_info}\n\n"
        f"Insights Generated:\n{insights_info}\n\n"
        "Validate all outputs. Be strict about insight quality."
    )

    result = json_completion(
        prompt=user_prompt,
        system_prompt=CRITIC_SYSTEM_PROMPT,
        max_tokens=1200,
        required_keys=["approved", "quality_score", "issues", "corrections", "summary"],
    )

    return CriticFeedback(
        approved=result.get("approved", False),
        quality_score=float(result.get("quality_score", 0.0)),
        issues=result.get("issues", []),
        corrections=result.get("corrections", []),
        summary=result.get("summary", ""),
    )
