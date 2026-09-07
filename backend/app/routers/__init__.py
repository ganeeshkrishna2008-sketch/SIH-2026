from app.routers.cameras import router as cameras_router
from app.routers.detections import router as detections_router
from app.routers.trajectories import router as trajectories_router
from app.routers.analytics import router as analytics_router
from app.routers.alerts import router as alerts_router
from app.routers.anpr import router as anpr_router
from app.routers.associations import router as associations_router

__all__ = [
    "cameras_router",
    "detections_router",
    "trajectories_router",
    "analytics_router",
    "alerts_router",
    "anpr_router",
    "associations_router",
]
