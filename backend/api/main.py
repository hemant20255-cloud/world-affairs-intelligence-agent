"""
FastAPI application entry point for the World Affairs Intelligence Agent.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.db.config import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield
    # Any teardown logic can go here


def create_app() -> FastAPI:
    app = FastAPI(
        title="World Affairs Intelligence Agent",
        description=(
            "A conversational AI agent for geopolitical intelligence. "
            "Query world affairs, browse collected events, and trigger "
            "live news collection."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    app.include_router(router)

    return app


app = create_app()
