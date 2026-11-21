from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine
from app.routes import auth, syllabus, quiz, mentor, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="StudySync API",
    description="Zero-dependency, container-free 3-tier personalized academic mentorship platform for college students (SIH Problem Statement 26207: Smart Education)",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router)
app.include_router(syllabus.router)
app.include_router(quiz.router)
app.include_router(mentor.router)
app.include_router(analytics.router)


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint verifying system, database, and AI engine status."""
    return {
        "status": "healthy",
        "service": "StudySync API",
        "version": "2.0.0",
        "database": "sqlite_wal_fk_enabled",
        "ai_engine": f"{settings.GEMINI_MODEL} (with deterministic offline academic fallback)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Mount Static Files (Zero-build SPA frontend)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
