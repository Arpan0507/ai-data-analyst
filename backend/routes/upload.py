"""
upload.py — File Upload & Analysis Orchestration Routes

Handles file upload, triggers the full multi-agent analysis pipeline,
and serves results including charts.

Critic-agent retry loop
-----------------------
After each Plan→Clean→Visualize→Stats→Insights pass the Critic Agent
reviews the outputs.  If the critic rejects them (approved=False) and
the retry budget has not been exhausted, the corrections are injected
back into the planning context and the inner pipeline is re-executed.
The loop runs at most MAX_RETRIES times before accepting the last result
unconditionally, so the pipeline can never be stuck indefinitely.
"""

from __future__ import annotations

import os
import uuid
import logging
import shutil
from typing import Any

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from schemas.models import UploadResponse, AnalysisStatus
from services.profiling import profile_dataset, profile_to_dict, profile_summary_text
from services.planner_agent import generate_plan
from services.validation import validate_plan
from services.executor_agent import execute_plan
from services.visualization_engine import generate_charts
from services.stats_engine import generate_statistics, stats_summary_text
from services.insight_agent import generate_insights
from services.critic_agent import critique_analysis
from services.memory import store_memory, get_memory_context
from services.report_generator import generate_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

# In-memory session storage
_sessions: dict[str, dict[str, Any]] = {}

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024  # bytes
MAX_RETRIES   = int(os.getenv("CRITIC_MAX_RETRIES", "2"))  # max critic-triggered re-runs


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or Excel file for analysis."""

    # Validate file type
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(400, f"Unsupported file type: .{ext}. Use CSV or Excel.")

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB")

    # Parse into DataFrame
    try:
        import io
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(content), on_bad_lines="warn")
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(400, f"Failed to parse file: {exc}")

    # Create session
    session_id = uuid.uuid4().hex[:12]
    _sessions[session_id] = {
        "df_raw": df,
        "filename": filename,
        "status": "uploaded",
        "progress": 0.0,
        "report": None,
        "df_cleaned": None,
    }

    return UploadResponse(
        session_id=session_id,
        filename=filename,
        rows=len(df),
        columns=len(df.columns),
    )


@router.post("/analyze/{session_id}")
async def analyze(session_id: str):
    """Run the full multi-agent analysis pipeline with critic-agent retry loop."""

    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found. Upload a file first.")

    df_raw = session["df_raw"]
    rows_before = len(df_raw)
    cols_before = len(df_raw.columns)

    try:
        # ── Step 1: Profile ────────────────────────────────────────
        session["status"] = "profiling"
        session["progress"] = 0.1
        logger.info(f"[{session_id}] Profiling dataset...")

        profile = profile_dataset(df_raw)
        profile_dict = profile_to_dict(profile)
        profile_text = profile_summary_text(profile)

        # ── Step 2: Memory context ─────────────────────────────────
        base_memory_context = get_memory_context(profile_text)

        # ──────────────────────────────────────────────────────────
        # Critic-agent retry loop
        # Steps 3-8 (Plan → Validate → Clean → Visualise → Stats →
        # Insights) are wrapped in a loop.  After each pass the Critic
        # Agent validates the outputs.  If it rejects them *and* we
        # still have retry budget, the corrections are appended to the
        # memory/planning context and the inner pipeline runs again.
        # ──────────────────────────────────────────────────────────
        critic_feedback = None
        extra_context   = ""          # accumulated critic corrections

        for attempt in range(1, MAX_RETRIES + 2):   # attempts: 1 … MAX_RETRIES+1
            is_last_attempt = (attempt == MAX_RETRIES + 1)

            # Build planning context: base memory + any prior corrections
            memory_context = base_memory_context
            if extra_context:
                memory_context = (
                    memory_context + "\n\n" + extra_context
                    if memory_context else extra_context
                )

            # ── Step 3: Plan ───────────────────────────────────────
            session["status"] = "planning"
            session["progress"] = 0.2
            logger.info(f"[{session_id}] (attempt {attempt}) Generating plan via Planner Agent...")

            plan = generate_plan(profile, memory_context=memory_context)

            # ── Step 4: Validate ───────────────────────────────────
            session["status"] = "validating"
            session["progress"] = 0.3
            logger.info(f"[{session_id}] (attempt {attempt}) Validating plan...")

            validated_plan, validation_notes = validate_plan(plan, profile)

            # ── Step 5: Execute (Clean) ────────────────────────────
            session["status"] = "cleaning"
            session["progress"] = 0.4
            logger.info(f"[{session_id}] (attempt {attempt}) Executing cleaning plan...")

            df_cleaned, execution_log = execute_plan(df_raw, validated_plan)
            session["df_cleaned"] = df_cleaned

            # ── Step 6: Visualize ──────────────────────────────────
            session["status"] = "visualizing"
            session["progress"] = 0.55
            logger.info(f"[{session_id}] (attempt {attempt}) Generating charts...")

            charts_dir = os.path.join("data", "charts", session_id)
            # Remove stale charts from a previous attempt before regenerating
            if os.path.isdir(charts_dir):
                shutil.rmtree(charts_dir)

            charts = generate_charts(
                df_cleaned,
                validated_plan.visualization_plan,
                output_dir=charts_dir,
                session_id=session_id,
            )

            # ── Step 7: Statistics ─────────────────────────────────
            session["status"] = "analyzing"
            session["progress"] = 0.65
            logger.info(f"[{session_id}] (attempt {attempt}) Computing statistics...")

            statistics = generate_statistics(df_cleaned)
            stats_text = stats_summary_text(statistics)

            # ── Step 8: Insights ───────────────────────────────────
            session["status"] = "generating_insights"
            session["progress"] = 0.75
            logger.info(f"[{session_id}] (attempt {attempt}) Generating insights...")

            insights = generate_insights(
                stats=statistics,
                profile_text=profile_text,
                charts=charts,
                memory_context=memory_context,
            )

            # ── Critic review ──────────────────────────────────────
            logger.info(f"[{session_id}] (attempt {attempt}) Running Critic Agent...")
            try:
                critic_feedback = critique_analysis(
                    cleaning_log=execution_log,
                    charts=charts,
                    insights=insights,
                    profile_text=profile_text,
                    stats_summary=stats_text,
                )
                approved      = critic_feedback.approved
                quality_score = critic_feedback.quality_score
                logger.info(
                    f"[{session_id}] Critic: approved={approved}, "
                    f"score={quality_score:.2f}"
                )
            except Exception as critic_exc:
                # Critic failures must not break the pipeline
                logger.warning(
                    f"[{session_id}] Critic Agent failed (non-fatal): {critic_exc}"
                )
                approved = True   # treat as approved so we don't retry on a critic error

            if approved or is_last_attempt:
                if not approved:
                    logger.warning(
                        f"[{session_id}] Critic still not satisfied after "
                        f"{MAX_RETRIES} retries — proceeding with last result."
                    )
                break

            # Build correction context for the next attempt
            issues      = critic_feedback.issues if critic_feedback else []
            corrections = critic_feedback.corrections if critic_feedback else []
            extra_context = (
                "CRITIC FEEDBACK FROM PREVIOUS ATTEMPT (apply these corrections):\n"
                + "Issues found:\n"
                + "\n".join(f"  - {i}" for i in issues)
                + "\nSuggested corrections:\n"
                + "\n".join(f"  - {c}" for c in corrections)
            )
            logger.info(
                f"[{session_id}] Critic rejected output — retrying "
                f"(attempt {attempt + 1}/{MAX_RETRIES + 1})..."
            )
            # Signal the frontend poller that a critic-triggered re-run is starting
            session["status"] = "recomputing"
            session["progress"] = 0.15

        # ── Step 9: Memory ─────────────────────────────────────────
        session["status"] = "storing_memory"
        session["progress"] = 0.88
        logger.info(f"[{session_id}] Storing to memory...")

        store_memory(
            text=f"Dataset profile: {profile_text}",
            metadata={"type": "profile", "session_id": session_id},
        )
        for insight in insights:
            store_memory(
                text=insight.text,
                metadata={"type": "insight", "session_id": session_id},
            )

        # ── Step 10: Report ────────────────────────────────────────
        session["status"] = "complete"
        session["progress"] = 1.0
        logger.info(f"[{session_id}] Generating report...")

        report = generate_report(
            session_id=session_id,
            profile_dict=profile_dict,
            execution_log=execution_log,
            explanations=validated_plan.explanations,
            charts=charts,
            statistics=statistics,
            insights=insights,
            critic_feedback=critic_feedback,
            validation_notes=validation_notes,
            rows_before=rows_before,
            rows_after=len(df_cleaned),
            cols_before=cols_before,
            cols_after=len(df_cleaned.columns),
        )

        session["report"] = report
        return report

    except Exception as exc:
        session["status"] = "error"
        session["progress"] = 0.0
        logger.error(f"[{session_id}] Pipeline error: {exc}", exc_info=True)
        raise HTTPException(500, f"Analysis failed: {exc}")


@router.get("/status/{session_id}", response_model=AnalysisStatus)
async def get_status(session_id: str):
    """Get the current pipeline status."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found.")

    return AnalysisStatus(
        session_id=session_id,
        status=session["status"],
        progress=session["progress"],
        message=f"Pipeline is {session['status']}",
    )


@router.get("/report/{session_id}")
async def get_report(session_id: str):
    """Get the completed analysis report."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found.")
    if session["status"] != "complete":
        raise HTTPException(400, f"Analysis not complete. Status: {session['status']}")
    return session["report"]


@router.get("/charts/{session_id}/{filename}")
async def get_chart(session_id: str, filename: str):
    """Serve a chart image file."""
    filepath = os.path.join("data", "charts", session_id, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "Chart not found.")
    return FileResponse(filepath, media_type="image/png")


@router.get("/download/{session_id}")
async def download_cleaned(session_id: str):
    """Download the cleaned CSV."""
    session = _sessions.get(session_id)
    if not session or session.get("df_cleaned") is None:
        raise HTTPException(404, "No cleaned data available.")

    import io
    csv_buffer = io.StringIO()
    session["df_cleaned"].to_csv(csv_buffer, index=False)

    from fastapi.responses import StreamingResponse
    csv_buffer.seek(0)
    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cleaned_{session_id}.csv"},
    )
