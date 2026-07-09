from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FacilityReport

router = APIRouter(prefix="/api/filters", tags=["filters"])

@router.get("/provinces")
def get_provinces(db: Session = Depends(get_db)):
    provinces = db.query(FacilityReport.province).distinct().order_by(FacilityReport.province).all()
    return [p[0] for p in provinces if p[0]]

@router.get("/districts")
def get_districts(
    province: str = Query(None, description="Filter districts by province"),
    db: Session = Depends(get_db)
):
    query = db.query(FacilityReport.district).distinct().order_by(FacilityReport.district)
    if province:
        query = query.filter(FacilityReport.province == province)
    districts = query.all()
    return [d[0] for d in districts if d[0]]