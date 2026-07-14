from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import crud
from app.llm_processor import call_llm
import json
import logging
from app.utils import safe_json_loads

router = APIRouter(prefix="/api/categorical", tags=["categorical"])

# ----------------------------------------------------------------------
# Helper: Generate a fallback summary from governance indicator counts
# ----------------------------------------------------------------------
def _generate_fallback_summary(reports: list) -> dict:
    """Generate a structured summary from governance indicator counts."""
    if not reports:
        return {
            "summary": "No governance data available.",
            "strengths": [],
            "challenges": [],
            "recommendations": []
        }

    total = len(reports)
    focal_person = sum(1 for r in reports if r.raw_data and r.raw_data.get("Sustainability Transition Focal Person in place?") in ["Yes", "yes", "true"])
    hcc_func = sum(1 for r in reports if r.raw_data and r.raw_data.get("Availability and functionality of Health Centre Committee") in ["Yes", "yes", "true"])
    sust_plan = sum(1 for r in reports if r.raw_data and r.raw_data.get("Availability of facility sustainability plan?") in ["Yes", "yes", "true"])
    hcc_meeting = sum(1 for r in reports if r.raw_data and r.raw_data.get("Was the HCC/Health facility meeting done") in ["Yes", "yes", "true"])

    summary = (
        f"Among {total} facilities, {focal_person} have a Sustainability Transition Focal Person, "
        f"{hcc_func} have a functional HCC, {sust_plan} have a sustainability plan, "
        f"and {hcc_meeting} have held an HCC meeting."
    )

    strengths = [
        f"{focal_person} facilities have a focal person in place",
        f"{hcc_func} facilities have a functional HCC",
        f"{sust_plan} facilities have a sustainability plan",
        f"{hcc_meeting} facilities have held an HCC meeting"
    ]

    challenges = []
    if total - focal_person > 0:
        challenges.append(f"{total - focal_person} facilities lack a focal person")
    if total - hcc_func > 0:
        challenges.append(f"{total - hcc_func} facilities lack a functional HCC")
    if total - sust_plan > 0:
        challenges.append(f"{total - sust_plan} facilities lack a sustainability plan")
    if total - hcc_meeting > 0:
        challenges.append(f"{total - hcc_meeting} facilities have not held an HCC meeting")

    recommendations = []
    if total - focal_person > 0:
        recommendations.append("Ensure all facilities have a designated Sustainability Transition Focal Person.")
    if total - hcc_func > 0:
        recommendations.append("Revitalise HCCs and ensure regular meetings are held.")
    if total - sust_plan > 0:
        recommendations.append("Develop and implement sustainability plans at all facilities.")
    if total - hcc_meeting > 0:
        recommendations.append("Track and document all HCC meetings to ensure accountability.")

    return {
        "summary": summary,
        "strengths": strengths,
        "challenges": challenges,
        "recommendations": recommendations
    }


# ----------------------------------------------------------------------
# 1. Categorical summary (counts of Yes/No/Unknown)
# ----------------------------------------------------------------------
@router.get("/summary")
def get_categorical_summary(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    
    # Order reports by facility name for deterministic ordering
    reports = sorted(reports, key=lambda r: r.facility or "")
    
    # Define the governance indicators (exact column names from Excel)
    indicators = [
        {
            "key": "Sustainability Transition Focal Person in place?",
            "label": "Sustainability Transition Focal Person",
            "comment_key": "Comments",
            "field": "sust_focal_person"
        },
        {
            "key": "Availability and functionality of Health Centre Committee",
            "label": "Health Centre Committee Functionality",
            "comment_key": "Comments.1",
            "field": "hcc_functionality"
        },
        {
            "key": "Availability of facility sustainability plan?",
            "label": "Facility Sustainability Plan",
            "comment_key": "Comments.2",
            "field": "sust_plan_available"
        },
        {
            "key": "Was the HCC/Health facility meeting done",
            "label": "HCC/Health Facility Meeting",
            "comment_key": "Comments.3",
            "field": "hcc_meeting_done"
        }
    ]

    results = []
    for indicator in indicators:
        yes_count = 0
        no_count = 0
        unknown_count = 0
        sample_comments = []
        all_comments = []

        for report in reports:
            if not report.raw_data:
                continue
            
            # Get the value from raw_data using the key
            value = report.raw_data.get(indicator["key"])
            # Normalize value
            if value is not None:
                value_str = str(value).strip().lower()
                if value_str in ['yes', 'true', '1']:
                    yes_count += 1
                elif value_str in ['no', 'false', '0']:
                    no_count += 1
                else:
                    unknown_count += 1
            else:
                unknown_count += 1
            
            # Collect comment
            comment = report.raw_data.get(indicator["comment_key"])
            if comment:
                all_comments.append({
                    "facility": report.facility,
                    "comment": str(comment)[:150] + "..." if len(str(comment)) > 150 else str(comment)
                })
                # Keep only first 5 for preview
                if len(sample_comments) < 5:
                    sample_comments.append(all_comments[-1])

        total = yes_count + no_count + unknown_count
        results.append({
            "indicator": indicator["label"],
            "yes": yes_count,
            "no": no_count,
            "unknown": unknown_count,
            "total": total,
            "yes_percentage": round((yes_count / total * 100) if total > 0 else 0, 1),
            "comments": sample_comments,
            "total_comments": len(all_comments)
        })
    return results


# ----------------------------------------------------------------------
# 2. LLM‑generated governance insights (with fallback)
# ----------------------------------------------------------------------
@router.get("/insights")
def get_governance_insights(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    
    if not reports:
        return {
            "total_facilities": 0,
            "summary": "No facilities found for the selected filters.",
            "strengths": [],
            "challenges": [],
            "recommendations": []
        }

    # Define the governance indicators (same as above)
    indicators = [
        ("Sustainability Transition Focal Person in place?", "Comments"),
        ("Availability and functionality of Health Centre Committee", "Comments.1"),
        ("Availability of facility sustainability plan?", "Comments.2"),
        ("Was the HCC/Health facility meeting done", "Comments.3")
    ]
    
    # Build structured text – limit to 20 comments
    comment_blocks = []
    MAX_COMMENTS = 20
    count = 0
    for report in reports:
        if count >= MAX_COMMENTS:
            break
        if not report.raw_data:
            continue
        facility = report.facility
        for indicator, comment_key in indicators:
            value = report.raw_data.get(indicator)
            comment = report.raw_data.get(comment_key)
            if value and comment:
                comment_blocks.append(
                    f"Facility: {facility}\n"
                    f"  Indicator: {indicator}\n"
                    f"  Response: {value}\n"
                    f"  Comment: {comment}\n"
                )
                count += 1
                if count >= MAX_COMMENTS:
                    break
    
    # If there are comments, try LLM; otherwise use fallback
    if comment_blocks:
        combined_text = "\n".join(comment_blocks)
        prompt = f"""
You are an expert in HIV programme transition and accountability. 
The ACCE project is transitioning to MOHCC ownership in Zimbabwe.

**Context**:
- {len(reports)} facilities are being assessed for transition readiness.
- Each facility should have a Sustainability Transition Focal Person, a functional HCC, a sustainability plan, and regular HCC meetings.
- Accountability to the donor and MOHCC requires evidence of transition progress.

**Governance Comments**:
{combined_text}

Based on these comments, produce a JSON output with:
1. "summary": a concise summary (2-3 sentences) stating **how many facilities are transition-ready** versus those needing attention. Mention specific districts or facilities if patterns emerge.
2. "strengths": list of governance strengths that support a smooth transition.
3. "challenges": list of governance gaps that **pose a risk to the transition**.
4. "recommendations": actionable steps to **strengthen governance and accountability** before project end.

Return only valid JSON, no extra text.
"""
        try:
            response_text = call_llm(prompt, max_tokens=500)
            # Clean up markdown if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            result = safe_json_loads(response_text)
            return {
                "total_facilities": len(reports),
                "summary": result.get("summary", ""),
                "strengths": result.get("strengths", []),
                "challenges": result.get("challenges", []),
                "recommendations": result.get("recommendations", [])
            }
        except Exception as e:
            logging.error(f"Governance insights LLM failed: {e}")
            # Fallback to rule-based summary
            fallback = _generate_fallback_summary(reports)
            return {
                "total_facilities": len(reports),
                "summary": fallback["summary"],
                "strengths": fallback["strengths"],
                "challenges": fallback["challenges"],
                "recommendations": fallback["recommendations"]
            }
    else:
        # No comments – use rule-based fallback
        fallback = _generate_fallback_summary(reports)
        return {
            "total_facilities": len(reports),
            "summary": fallback["summary"],
            "strengths": fallback["strengths"],
            "challenges": fallback["challenges"],
            "recommendations": fallback["recommendations"]
        }