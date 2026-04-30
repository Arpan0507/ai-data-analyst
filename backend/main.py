"""
main.py — FastAPI Application Entry Point

Sets up the FastAPI app with CORS, routes, static file serving,
and startup/shutdown events for FAISS memory initialization.
"""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: initialize FAISS memory
    logger.info("Initializing FAISS memory layer...")
    from services.memory import initialize_memory
    initialize_memory()

    # Ensure data directories exist
    os.makedirs("data/charts", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/memory", exist_ok=True)

    logger.info("AI Data Analyst V3 is ready!")
    yield
    # Shutdown
    logger.info("Shutting down AI Data Analyst V3...")


# Create FastAPI app
app = FastAPI(
    title="AI Data Analyst V3",
    description="Production-grade multi-agent AI data analysis system",
    version="3.0.0",
    lifespan=lifespan,
)

# CORS middleware — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
from routes.upload import router as upload_router
from routes.query import router as query_router

app.include_router(upload_router)
app.include_router(query_router)

# Mount static files for chart serving
os.makedirs("data/charts", exist_ok=True)
app.mount("/static/charts", StaticFiles(directory="data/charts"), name="charts")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "AI Data Analyst V3",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    """Health check with memory stats."""
    from services.memory import get_memory_stats
    return {
        "status": "healthy",
        "memory": get_memory_stats(),
    }
