from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_engine import AnalyticsEngine
from app.schemas.analytics import AnalyticsSummaryResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(db: Session = Depends(get_db)):
    return AnalyticsEngine.get_summary_analytics(db)
