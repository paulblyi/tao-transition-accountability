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
# Helper: Ensure list items are plain strings
# ----------------------------------------------------------------------
def _ensure_string_list(data):
    """Convert any list of mixed types into a list of plain strings."""
    if not isinstance(data, list):
        return []
    result = []
    for item in data:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            # Try common keys: 'text', 'message', 'content', or join all values
            if 'text' in item:
                result.append(str(item['text']))
            elif 'message' in item:
                result.append(str(item['message']))
            elif 'content' in item:
                result.append(str(item['content']))
            else:
                # Fallback: join all values
                result.append(" ".join(str(v) for v in item.values()))
        else:
            result.append(str(item))
    return result

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
            "recommendations": [],
            "llm_failed": False
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
        "strengths": _ensure_string_list(strengths),
        "challenges": _ensure_string_list(challenges),
        "recommendations": _ensure_string_list(recommendations),
        "llm_failed": False
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
# 2. LLM‑generated governance insights (with fallback and string safety)
# ----------------------------------------------------------------------
@router.get("/insights")
def get_governance_insights(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip_llm: bool = False,
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    if not reports:
        return {
            "total_facilities": 0,
            "summary": "No facilities found for the selected filters.",
            "strengths": [],
            "challenges": [],
            "recommendations": [],
            "llm_failed": False
        }

    # If skip_llm is true, directly return fallback
    if skip_llm:
        fallback = _generate_fallback_summary(reports)
        fallback["total_facilities"] = len(reports)
        return fallback

    # Otherwise try LLM – include "Key achievements" as an indicator
    indicators = [
        ("Sustainability Transition Focal Person in place?", "Comments"),
        ("Availability and functionality of Health Centre Committee", "Comments.1"),
        ("Availability of facility sustainability plan?", "Comments.2"),
        ("Was the HCC/Health facility meeting done", "Comments.3"),
        ("Key achievements", None),   # <-- ADDED: no separate comment column
    ]

    comment_blocks = []
    MAX_COMMENTS = 20
    count = 0
    for report in reports:
        if count >= MAX_COMMENTS:
            break
        if not report.raw_data:
            continue
        facility = report.facility
        district_name = report.district or "Unknown"
        province_name = report.province or "Unknown"
        for indicator, comment_key in indicators:
            value = report.raw_data.get(indicator)
            if not value:
                continue
            if comment_key:
                comment = report.raw_data.get(comment_key)
                if comment:
                    comment_blocks.append(
                        f"Province: {province_name}\n"
                        f"District: {district_name}\n"
                        f"Facility: {facility}\n"
                        f"  Indicator: {indicator}\n"
                        f"  Response: {value}\n"
                        f"  Comment: {comment}\n"
                    )
                    count += 1
            else:
                # For Key achievements, use the value directly
                comment_blocks.append(
                    f"Province: {province_name}\n"
                    f"District: {district_name}\n"
                    f"Facility: {facility}\n"
                    f"  Key Achievement: {value}\n"
                )
                count += 1
            if count >= MAX_COMMENTS:
                break

    if not comment_blocks:
        fallback = _generate_fallback_summary(reports)
        fallback["total_facilities"] = len(reports)
        return fallback

    combined_text = "\n".join(comment_blocks)
    prompt = f"""
You are an expert in HIV programme transition and accountability.

**IMPORTANT RULES – YOU MUST FOLLOW THEM EXACTLY:**
1. ONLY mention districts and facilities that are EXPLICITLY listed in the comments below.
2. DO NOT invent or assume any district or facility names that are not in the comments.
3. The hierarchy is: Province -> District -> Facility.
4. If you are not sure about a name, DO NOT mention it.
5. The selected province is: {province or "All provinces"}.
6. The selected district is: {district or "All districts"}.

**Context**:
- {len(reports)} facilities are being assessed for transition readiness.
- Each facility should have a Sustainability Transition Focal Person, a functional HCC, a sustainability plan, and regular HCC meetings.

**Comments**:
{combined_text}

Based ONLY on the comments above, produce a JSON output with:
1. "summary": a concise 2-3 sentence summary. ONLY mention districts/facilities that appear in the comments.
2. "strengths": list of governance strengths observed (ONLY from the comments) – each as a plain string.
3. "challenges": list of governance gaps identified (ONLY from the comments) – each as a plain string.
4. "recommendations": actionable steps based on the challenges observed – each as a plain string.

Return only valid JSON, no extra text.
"""
    try:
        response_text = call_llm(prompt, max_tokens=500)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        result = safe_json_loads(response_text)
        return {
            "total_facilities": len(reports),
            "summary": result.get("summary", ""),
            "strengths": _ensure_string_list(result.get("strengths", [])),
            "challenges": _ensure_string_list(result.get("challenges", [])),
            "recommendations": _ensure_string_list(result.get("recommendations", [])),
            "llm_failed": False
        }
    except Exception as e:
        logging.error(f"Governance insights LLM failed: {e}")
        fallback = _generate_fallback_summary(reports)
        fallback["total_facilities"] = len(reports)
        fallback["llm_failed"] = True
        return fallback