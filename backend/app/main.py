from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import PROJECT_NAME, API_V1_PREFIX
from app.database import engine, Base
from app.models import Camera, Vehicle, Detection, Alert
from app.routers import (
    cameras_router,
    detections_router,
    trajectories_router,
    analytics_router,
    alerts_router,
    anpr_router,
)

# Initialize database schema tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=PROJECT_NAME,
    description="City-Wide AI Engine for Multi-Camera ANPR Trajectory Tracking and Urban Traffic Analytics",
    version="2.0.0"
)

# Configure CORS for Frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve annotated ANPR output frames as static files
anpr_output_dir = Path(__file__).resolve().parent.parent.parent / "data" / "anpr_output"
anpr_output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/anpr-frames", StaticFiles(directory=str(anpr_output_dir)), name="anpr-frames")

# Register API Routers
app.include_router(cameras_router, prefix=API_V1_PREFIX)
app.include_router(detections_router, prefix=API_V1_PREFIX)
app.include_router(trajectories_router, prefix=API_V1_PREFIX)
app.include_router(analytics_router, prefix=API_V1_PREFIX)
app.include_router(alerts_router, prefix=API_V1_PREFIX)
app.include_router(anpr_router, prefix=API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "status": "online",
        "project": PROJECT_NAME,
        "phase": "Phase 2 — ANPR/OCR Active",
        "docs_url": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

