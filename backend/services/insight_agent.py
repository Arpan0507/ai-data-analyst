"""
insight_agent.py — LLM-Powered Insight Agent

Generates 3-5 specific, quantitative business insights using
statistical summaries, dataset profiles, and chart metadata.
"""

from __future__ import annotations

import json
from typing import Any

from utils.llm_client import json_completion
from schemas.models import InsightItem, ChartMetadata

INSIGHT_SYSTEM_PROMPT = """\
You are a senior business analyst. You will receive a statistical summary,
dataset profile, and chart metadata. Return ONLY a valid JSON object:

{"insights": [
  {"text": "specific insight with numbers", "metric_value": "key number",
   "comparison": "vs what", "category": "trend|anomaly|pattern|recommendation"}
]}

Rules:
- 3-5 insights, each with specific numbers/percentages
- NO generic statements
- Reference actual column names and values
- Return ONLY JSON, no markdown
"""


def generate_insights(
    stats: dict[str, Any],
    profile_text: str,
    charts: list[ChartMetadata],
    memory_context: str = "",
) -> list[InsightItem]:
    charts_info = "\n".join([
        f"  - {c.chart_type}: {c.title}" for c in charts
    ]) if charts else "  No charts generated."

    user_prompt = (
        f"Dataset Profile:\n{profile_text}\n\n"
        f"Statistical Summary:\n{json.dumps(stats, indent=2, default=str)}\n\n"
        f"Charts:\n{charts_info}\n\n"
    )
    if memory_context:
        user_prompt += f"Past context:\n{memory_context}\n\n"
    user_prompt += "Generate 3-5 specific business insights."

    result = json_completion(
        prompt=user_prompt,
        system_prompt=INSIGHT_SYSTEM_PROMPT,
        max_tokens=1500,
        required_keys=["insights"],
    )

    insights = []
    for item in result.get("insights", []):
        insights.append(InsightItem(
            text=item.get("text", ""),
            metric_value=str(item.get("metric_value", "")),
            comparison=item.get("comparison", ""),
            category=item.get("category", "pattern"),
        ))
    return insights
