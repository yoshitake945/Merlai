"""
Main FastAPI application for Merlai music generation service.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.midi import MIDIGenerator
from ..core.music import MusicGenerator
from ..core.plugins import PluginManager
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    print("Starting Merlai music generation service...")

    # Initialize core components
    app.state.music_generator = MusicGenerator(use_ai_models=True)
    app.state.midi_generator = MIDIGenerator()
    app.state.plugin_manager = PluginManager()

    # Load AI model
    try:
        app.state.music_generator.load_model()
        print("AI model loaded successfully")
    except Exception as e:
        print(f"Warning: Failed to load AI model: {e}")

    # Scan for plugins
    plugins = app.state.plugin_manager.scan_plugins()
    print(f"Found {len(plugins)} plugins")

    yield

    # Shutdown
    print("Shutting down Merlai service...")


# Create FastAPI application
app = FastAPI(
    title="Merlai Music Generation API",
    description="AI-powered music creation assistant for filling missing notes",  # noqa: E501
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint."""
    return {
        "message": "Welcome to Merlai Music Generation API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": (
            hasattr(app.state, "music_generator")
            and app.state.music_generator.model is not None
        ),
        "plugins_loaded": (
            len(app.state.plugin_manager.plugins)
            if hasattr(app.state, "plugin_manager")
            else 0
        ),
    }


@app.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Readiness check endpoint."""
    return {"status": "ready"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    uvicorn.run(
        "merlai.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
