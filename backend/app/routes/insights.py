from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import crud
from app.llm_processor import process_comments
import json

router = APIRouter(prefix="/api/insights", tags=["insights"])

@router.get("/")
def get_insights(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    
    # Get individual insights
    insights = [r.insights for r in reports if r.insights]
    
    # Generate aggregated summary if there are reports
    if reports and len(reports) > 0:
        # Extract facility names
        facility_names = [r.facility for r in reports if r.facility]
        
        # Build a combined comments dict for aggregation
        combined_comments = {}
        for report in reports:
            if report.raw_data:
                for k, v in report.raw_data.items():
                    if 'Comment' in k or 'Comments' in k:
                        if k not in combined_comments:
                            combined_comments[k] = []
                        combined_comments[k].append(f"[{report.facility}] {v}")
        
        # Convert lists to strings
        combined_comments_str = {k: "\n".join(v[:3]) for k, v in combined_comments.items() if v}
        
        # Generate an aggregated summary
        aggregated_insight = process_comments(
            combined_comments_str,
            facility_name=None,
            total_facilities=len(reports)
        )
        
        # Add facility list to the summary
        if facility_names:
            facility_list = ", ".join(facility_names[:5])
            if len(facility_names) > 5:
                facility_list += f" and {len(facility_names) - 5} others"
            aggregated_insight['facilities'] = facility_list
            aggregated_insight['total_facilities'] = len(facility_names)
            aggregated_insight['summary'] = f"Based on {len(facility_names)} facilities including {facility_list}. " + aggregated_insight.get('summary', '')
    
    return {
        "insights": insights,
        "aggregated": aggregated_insight if reports else None,
        "total_facilities": len(reports),
        "facility_names": [r.facility for r in reports if r.facility]
    }
