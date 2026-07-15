from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app import crud
from app.models import FacilityReport
from app.llm_processor import call_llm

router = APIRouter(prefix="/api/coverage", tags=["coverage"])

@router.get("/district")
def get_district_coverage(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns coverage metrics and identifies facilities not tracked recently.
    """
    # Get all reports for the filter
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    
    if not reports:
        return {
            "district": district,
            "province": province,
            "total_tracked_ever": 0,
            "tracked_in_last_30_days": 0,
            "not_tracked_recently": [],
            "percentage_covered": 0,
            "facility_list": []
        }

    # Distinct facilities ever tracked
    all_facilities = set(r.facility for r in reports if r.facility)
    
    # Facilities tracked in the last 30 days
    cutoff = datetime.now() - timedelta(days=30)
    recent_facilities = set(
        r.facility for r in reports 
        if r.week_ending and r.week_ending >= cutoff and r.facility
    )
    
    # Not tracked recently
    not_tracked = all_facilities - recent_facilities

    # Calculate percentage coverage
    total = len(all_facilities)
    covered = len(recent_facilities)
    pct = round((covered / total * 100) if total > 0 else 0, 1)

    # Get last visit date for each facility (to show urgency)
    last_visit = {}
    for r in reports:
        if r.facility:
            if r.facility not in last_visit or (r.week_ending and r.week_ending > last_visit[r.facility]):
                last_visit[r.facility] = r.week_ending

    # Build priority list (facilities not tracked recently, with days since last visit)
    priority = []
    for f in not_tracked:
        if f in last_visit and last_visit[f]:
            days = (datetime.now() - last_visit[f]).days
            priority.append({
                "facility": f,
                "last_visit": last_visit[f].isoformat() if last_visit[f] else None,
                "days_since": days
            })
        else:
            priority.append({
                "facility": f,
                "last_visit": None,
                "days_since": None
            })

    # Sort by days_since descending (most urgent first)
    priority.sort(key=lambda x: x["days_since"] if x["days_since"] is not None else 0, reverse=True)

    return {
        "district": district,
        "province": province,
        "total_facilities": total,
        "tracked_in_last_30_days": covered,
        "not_tracked_recently": priority[:10],  # Top 10 urgent
        "percentage_covered": pct,
        "all_facilities": list(all_facilities),
        "last_visit_dates": {k: v.isoformat() if v else None for k, v in last_visit.items()}
    }


@router.get("/risk")
def get_transition_risk(
    province: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Calculates a transition risk score for each facility based on:
    - Governance gaps (missing focal person, no HCC, no plan, no meetings)
    - Time since last visit
    - Number of challenges reported
    """
    reports = crud.get_filtered_reports(db, province, district, None, None)
    
    if not reports:
        return {"facilities": []}

    # Group by facility (take the most recent report for each)
    facility_map = {}
    for r in reports:
        if r.facility not in facility_map or (r.week_ending and r.week_ending > facility_map[r.facility]["week_ending"]):
            facility_map[r.facility] = {
                "facility": r.facility,
                "district": r.district,
                "province": r.province,
                "week_ending": r.week_ending,
                "raw_data": r.raw_data or {},
                "insights": r.insights or {}
            }

    # Calculate risk score
    risk_list = []
    for f, data in facility_map.items():
        raw = data["raw_data"]
        score = 0
        details = []

        # 1. Governance gaps (each missing = +1)
        if raw.get("Sustainability Transition Focal Person in place?") not in ["Yes", "yes", "true"]:
            score += 1
            details.append("Missing Sustainability Focal Person")
        if raw.get("Availability and functionality of Health Centre Committee") not in ["Yes", "yes", "true"]:
            score += 1
            details.append("HCC not functional")
        if raw.get("Availability of facility sustainability plan?") not in ["Yes", "yes", "true"]:
            score += 1
            details.append("No sustainability plan")
        if raw.get("Was the HCC/Health facility meeting done") not in ["Yes", "yes", "true"]:
            score += 1
            details.append("No recent HCC meeting")

        # 2. Time since last visit (if > 30 days, +1; > 60 days, +2)
        if data["week_ending"]:
            days = (datetime.now() - data["week_ending"]).days
            if days > 60:
                score += 2
                details.append(f"Not visited for {days} days")
            elif days > 30:
                score += 1
                details.append(f"Not visited for {days} days")

        # 3. Challenges mentioned (if any, +1)
        challenges = raw.get("Key Challenges")
        if challenges:
            score += 1
            details.append("Challenges reported")

        risk_level = "Low"
        if score >= 4:
            risk_level = "High"
        elif score >= 2:
            risk_level = "Medium"

        risk_list.append({
            "facility": f,
            "district": data["district"],
            "province": data["province"],
            "risk_score": score,
            "risk_level": risk_level,
            "details": details[:3],  # Top 3 reasons
            "last_visit": data["week_ending"].isoformat() if data["week_ending"] else None
        })

    # Sort by risk score descending
    risk_list.sort(key=lambda x: x["risk_score"], reverse=True)

    return {
        "total_facilities": len(risk_list),
        "high_risk": sum(1 for r in risk_list if r["risk_level"] == "High"),
        "medium_risk": sum(1 for r in risk_list if r["risk_level"] == "Medium"),
        "low_risk": sum(1 for r in risk_list if r["risk_level"] == "Low"),
        "facilities": risk_list
    }

@router.get("/narrative")
def get_risk_narrative(
    province: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, None, None)
    if not reports:
        return {"narrative": "No data available for the selected filters."}

    # ---- Compute risk counts and coverage (reuse logic) ----
    facility_map = {}
    for r in reports:
        if r.facility not in facility_map or (r.week_ending and r.week_ending > facility_map[r.facility]["week_ending"]):
            facility_map[r.facility] = {
                "facility": r.facility,
                "district": r.district,
                "province": r.province,
                "week_ending": r.week_ending,
                "raw_data": r.raw_data or {},
            }

    risk_list = []
    for f, data in facility_map.items():
        raw = data["raw_data"]
        score = 0
        # Governance gaps
        if raw.get("Sustainability Transition Focal Person in place?") not in ["Yes", "yes", "true"]:
            score += 1
        if raw.get("Availability and functionality of Health Centre Committee") not in ["Yes", "yes", "true"]:
            score += 1
        if raw.get("Availability of facility sustainability plan?") not in ["Yes", "yes", "true"]:
            score += 1
        if raw.get("Was the HCC/Health facility meeting done") not in ["Yes", "yes", "true"]:
            score += 1
        # Time since last visit
        if data["week_ending"]:
            days = (datetime.now() - data["week_ending"]).days
            if days > 60:
                score += 2
            elif days > 30:
                score += 1
        # Challenges
        if raw.get("Key Challenges"):
            score += 1

        risk_list.append({
            "facility": f,
            "risk_score": score,
            "last_visit": data["week_ending"]
        })

    # Counts
    high = sum(1 for r in risk_list if r["risk_score"] >= 4)
    medium = sum(1 for r in risk_list if 2 <= r["risk_score"] <= 3)
    low = sum(1 for r in risk_list if r["risk_score"] <= 1)
    total = len(risk_list)
    coverage_pct = 0
    if total > 0:
        cutoff = datetime.now() - timedelta(days=30)
        recent = sum(1 for r in risk_list if r["last_visit"] and r["last_visit"] >= cutoff)
        coverage_pct = round((recent / total) * 100, 1)

    # Build prompt
    prompt = f"""
You are an expert in HIV programme transition and accountability. 
Based on the following aggregated risk and coverage data for the selected level, produce a concise narrative (2-4 sentences) that:
- Summarises the overall **accountability** and **transition readiness** of the facilities.
- Highlights the proportion of facilities at high, medium, and low risk.
- Mentions the coverage percentage (facilities visited in the last 30 days).
- If applicable, mention the number of facilities not visited recently.

Data:
- Total facilities: {total}
- High risk: {high}
- Medium risk: {medium}
- Low risk: {low}
- Coverage (visited in last 30 days): {coverage_pct}%

The narrative should be actionable and should help decision-makers understand where to focus their attention.
Return only the narrative text, no extra formatting.
"""
    try:
        narrative = call_llm(prompt, max_tokens=300)
    except Exception as e:
        logging.error(f"Narrative LLM failed: {e}")
        narrative = (
            f"Among {total} facilities, {high} are high risk, {medium} medium risk, {low} low risk. "
            f"Coverage is {coverage_pct}% (facilities visited in the last 30 days). "
            "Please review the data and prioritise high-risk facilities and those not visited recently."
        )

    return {"narrative": narrative}