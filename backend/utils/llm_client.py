"""
llm_client.py — OpenRouter LLM Client with JSON Reliability Layer

Provides chat completion and structured JSON completion with
automatic retry, JSON extraction, and schema validation.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.getenv("LLM_MODEL", "openrouter/auto")
MAX_JSON_RETRIES = 3


# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """Return a cached OpenAI client wired to OpenRouter."""
    global _client
    if _client is not None:
        return _client

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY environment variable is not set. "
            "Please set it in your .env file or export it.\n"
            "  export OPENROUTER_API_KEY='sk-or-...'"
        )

    _client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )
    return _client


# ---------------------------------------------------------------------------
# Raw chat completion
# ---------------------------------------------------------------------------

def chat_completion(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> str:
    """
    Send a chat completion request and return the raw text response.

    Parameters
    ----------
    prompt : str
        The user message.
    system_prompt : str
        Optional system-level instruction.
    max_tokens : int
        Maximum tokens in the response.
    temperature : float
        Sampling temperature.

    Returns
    -------
    str
        The assistant's reply text.
    """
    try:
        client = get_client()
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()

    except EnvironmentError:
        raise
    except Exception as exc:
        raise RuntimeError(f"LLM API call failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Structured JSON completion with retry
# ---------------------------------------------------------------------------

def json_completion(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.2,
    max_retries: int = MAX_JSON_RETRIES,
    required_keys: Optional[list[str]] = None,
) -> dict:
    """
    Request a JSON response from the LLM, with automatic retry on failure.

    Attempts to parse JSON from the response. If parsing fails or required
    keys are missing, retries with error context appended to the prompt.

    Parameters
    ----------
    prompt : str
        The user message.
    system_prompt : str
        System-level instruction (should request JSON output).
    max_tokens : int
        Maximum response tokens.
    temperature : float
        Sampling temperature (lower for JSON reliability).
    max_retries : int
        Maximum number of retry attempts (default 3).
    required_keys : list[str], optional
        Top-level keys that must be present in the parsed JSON.

    Returns
    -------
    dict
        The parsed JSON response.

    Raises
    ------
    ValueError
        If the LLM fails to return valid JSON after all retries.
    """
    current_prompt = prompt
    last_error = ""

    for attempt in range(1, max_retries + 1):
        try:
            raw = chat_completion(
                current_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            parsed = extract_json(raw)

            # Validate required keys
            if required_keys:
                missing = [k for k in required_keys if k not in parsed]
                if missing:
                    raise ValueError(
                        f"JSON is missing required keys: {missing}"
                    )

            return parsed

        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            last_error = str(exc)
            current_prompt = (
                f"{prompt}\n\n"
                f"[RETRY {attempt}/{max_retries}] Your previous output was "
                f"invalid: {last_error}. "
                f"Please return ONLY a valid JSON object with no markdown "
                f"fences, no explanation text."
            )

    raise ValueError(
        f"LLM failed to return valid JSON after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


# ---------------------------------------------------------------------------
# JSON extraction helpers
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict:
    """
    Extract and parse a JSON object from LLM response text.

    Handles common issues: markdown fences, surrounding prose,
    nested JSON blocks.
    """
    # 1. Direct parse
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE)
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass

    # 3. Find the first complete { ... } block using brace matching
    start_idx = text.find("{")
    if start_idx != -1:
        depth = 0
        for i in range(start_idx, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start_idx : i + 1])
                    except json.JSONDecodeError:
                        break

    # 4. Fallback: regex for any { ... }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No valid JSON object found in LLM response", text, 0)
