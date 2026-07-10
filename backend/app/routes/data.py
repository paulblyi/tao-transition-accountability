from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/api/data", tags=["data"])

@router.get("/aggregated", response_model=schemas.AggregatedResponse)
def get_aggregated(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    # Compute aggregates (simplified)
    total = len(reports)
    avg_hts = crud.average(reports, "hts_mohcc_pct")
    avg_vl = crud.average(reports, "vl_mohcc_pct")
    # Categorical counts (example: HCC availability)
    hcc_counts = {}
    # You can compute this from the comments or separate columns
    # For now, return empty
    return {
        "total_facilities": total,
        "avg_hts_mohcc_pct": avg_hts,
        "avg_vl_mohcc_pct": avg_vl,
        "categorical": {}
    }

""" @router.get("/table")
def get_table_data(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    # Convert to list of dicts for the table
    return [{"facility": r.facility, "district": r.district, "week_ending": r.week_ending, "hts_pct": r.hts_mohcc_pct} for r in reports]
 """
@router.get("/table")
def get_table_data(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    
    # Format for the table
    table_data = []
    for r in reports:
        table_data.append({
            "facility": r.facility,
            "district": r.district,
            "province": r.province,
            "week_ending": r.week_ending.isoformat() if r.week_ending else None,
            "visit_type": r.visit_type,
            "hts_mohcc_pct": r.hts_mohcc_pct,
            "vl_mohcc_pct": r.vl_mohcc_pct,
            "prep_mohcc_pct": r.prep_mohcc_pct,
            "viac_mohcc_pct": r.viac_mohcc_pct,
            "art_mohcc_pct": r.art_mohcc_pct,
        })
    
    return table_data
