"""
query.py — Natural Language Query Endpoint

Handles user questions about their uploaded data using
the NL query system.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from schemas.models import QueryRequest, QueryResponse
from services.nl_query import handle_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query/{session_id}", response_model=QueryResponse)
async def query_data(session_id: str, request: QueryRequest):
    """
    Ask a natural language question about the uploaded dataset.
    """
    logger.info(f"[{session_id}] Incoming query: '{request.question}'")

    # Import session store from upload routes
    try:
        from routes.upload import _sessions
    except ImportError as exc:
        logger.error(f"[{session_id}] Could not import _sessions: {exc}")
        raise HTTPException(500, "Session store unavailable.")

    session = _sessions.get(session_id)
    if not session:
        logger.warning(
            f"[{session_id}] Session not found. Available sessions: "
            f"{list(_sessions.keys())}"
        )
        raise HTTPException(
            404,
            "Session not found. This can happen if the server was restarted "
            "after your upload. Please re-upload your file."
        )

    df = session.get("df_cleaned") or session.get("df_raw")
    if df is None:
        logger.error(f"[{session_id}] Session has no DataFrame.")
        raise HTTPException(400, "No data available for querying.")

    logger.info(
        f"[{session_id}] Querying DataFrame with shape {df.shape} — "
        f"question: '{request.question}'"
    )

    try:
        result = handle_query(df, request.question)
        logger.info(f"[{session_id}] Query answered successfully.")
        return QueryResponse(
            question=request.question,
            answer=result.get("answer", "Could not generate an answer."),
            supporting_data=result.get("supporting_data"),
            query_code=result.get("query_code", ""),
        )
    except Exception as exc:
        logger.error(f"[{session_id}] Query failed: {exc}", exc_info=True)
        raise HTTPException(500, f"Query failed: {exc}")
