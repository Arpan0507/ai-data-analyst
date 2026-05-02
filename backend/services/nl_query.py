"""
nl_query.py — Natural Language Query Handler

Interprets user questions about the data, generates pandas code,
executes it safely, and returns an LLM-generated answer.
"""

from __future__ import annotations

import json
import pandas as pd
from typing import Any

from utils.llm_client import json_completion, chat_completion
from utils.helpers import truncate_for_llm, dataframe_summary_for_llm

CODE_GEN_PROMPT = """\
You are a data query assistant. The user has a pandas DataFrame called `df`.
Given the user's question and the DataFrame info, generate Python code that
answers the question. Return ONLY a JSON object:

{"code": "pandas code using df variable", "explanation": "what this code does"}

Rules:
- The code must use the variable `df` (already available)
- Only use pandas operations
- The code should produce a result assigned to variable `result`
- Do NOT import anything or read files
- Do NOT modify df, only query it
- Return ONLY JSON
"""

ANSWER_PROMPT = """\
You are a data analyst. Given the user's question and the query result,
provide a clear, concise answer. Include specific numbers and context.
Be direct and helpful. Do not use markdown formatting.
"""


def handle_query(
    df: pd.DataFrame,
    question: str,
) -> dict[str, Any]:
    """
    Process a natural language query about the dataset.

    Parameters
    ----------
    df : pd.DataFrame
        The cleaned dataset.
    question : str
        The user's natural language question.

    Returns
    -------
    dict
        {answer, supporting_data, query_code}
    """
    df_info = truncate_for_llm(dataframe_summary_for_llm(df, max_rows=3), max_chars=3000)

    # Step 1: Generate pandas code
    code_prompt = (
        f"DataFrame info:\n{df_info}\n\n"
        f"Columns: {list(df.columns)}\n"
        f"Dtypes: {dict(df.dtypes.astype(str))}\n\n"
        f"User question: {question}"
    )

    code_result = json_completion(
        prompt=code_prompt,
        system_prompt=CODE_GEN_PROMPT,
        max_tokens=500,
        required_keys=["code"],
    )

    query_code = code_result.get("code", "")
    explanation = code_result.get("explanation", "")

    # Step 2: Execute the code safely
    exec_result = _safe_execute(df, query_code)

    # Step 3: Generate natural language answer
    answer_prompt = (
        f"Question: {question}\n\n"
        f"Code executed: {query_code}\n"
        f"Explanation: {explanation}\n\n"
        f"Result:\n{truncate_for_llm(str(exec_result.get('output', '')), 2000)}\n\n"
        "Provide a clear answer to the user's question."
    )

    answer = chat_completion(
        prompt=answer_prompt,
        system_prompt=ANSWER_PROMPT,
        max_tokens=500,
    )

    return {
        "answer": answer,
        "supporting_data": exec_result.get("output_data"),
        "query_code": query_code,
    }


def _safe_execute(df: pd.DataFrame, code: str) -> dict[str, Any]:
    """Safely execute pandas code in a restricted namespace."""
    try:
        namespace = {"df": df.copy(), "pd": pd, "result": None}
        exec(code, {"__builtins__": {}}, namespace)

        result = namespace.get("result")

        if isinstance(result, pd.DataFrame):
            output = result.head(20).to_string()
            output_data = result.head(20).to_dict(orient="records")
        elif isinstance(result, pd.Series):
            output = result.head(20).to_string()
            output_data = result.head(20).to_dict()
        else:
            output = str(result)
            output_data = result

        return {"output": output, "output_data": output_data, "success": True}

    except Exception as exc:
        return {
            "output": f"Query execution failed: {exc}",
            "output_data": None,
            "success": False,
        }
