from sqlalchemy.orm import Session
from app import models
from typing import Optional, List
from datetime import datetime

def get_filtered_reports(
    db: Session,
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[models.FacilityReport]:
    query = db.query(models.FacilityReport)
    if province:
        query = query.filter(models.FacilityReport.province == province)
    if district:
        query = query.filter(models.FacilityReport.district == district)
    if start_date:
        query = query.filter(models.FacilityReport.week_ending >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(models.FacilityReport.week_ending <= datetime.fromisoformat(end_date))
    return query.all()

def average(reports: List[models.FacilityReport], attr: str) -> Optional[float]:
    values = [getattr(r, attr) for r in reports if getattr(r, attr) is not None]
    return sum(values) / len(values) if values else None
