from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/api/insights", tags=["insights"])

@router.get("/", response_model=schemas.InsightResponse)
def get_insights(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    insights = [r.insights for r in reports if r.insights]
    return {"insights": insights}
