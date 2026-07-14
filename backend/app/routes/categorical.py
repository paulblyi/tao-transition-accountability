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
# 2. LLM‑generated governance insights (with comment limit)
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
    
    # Build structured text – limit to 30 comments
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
    
    if not comment_blocks:
        return {
            "total_facilities": len(reports),
            "summary": "No governance comments available for the selected filters.",
            "strengths": [],
            "challenges": [],
            "recommendations": []
        }

    combined_text = "\n".join(comment_blocks)
    
    prompt = f"""
You are an expert in HIV programme transition analysis. 
Based on the following governance and coordination comments from **{len(reports)}** facility visits, produce a structured summary.

Your output must be a valid JSON object with these keys:
- "summary": a concise overall summary (2-3 sentences) mentioning that this is based on **{len(reports)}** facilities.
- "strengths": a list of specific strengths (positive findings) observed.
- "challenges": a list of specific challenges or gaps identified.
- "recommendations": a list of actionable recommendations.

Comments:
{combined_text}

Return only valid JSON, no extra text.
"""
    try:
        response_text = call_llm(prompt, max_tokens=500)
        # Clean up markdown if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        #result = json.loads(response_text)
        result = safe_json_loads(response_text)
    except Exception as e:
        logging.error(f"Governance insights LLM failed: {e}")
          # Fallback: extract a short summary from the first few comments
        fallback_summary = f"Unable to generate structured insights. Raw response (first 200 chars): {response_text[:200]}..."
        result = {
            # "summary": f"Unable to generate insights at this time. Error: {str(e)}",
            "summary": fallback_summary,
            "strengths": [],
            "challenges": [],
            "recommendations": []
        }

    return {
        "total_facilities": len(reports),
        "summary": result.get("summary", ""),
        "strengths": result.get("strengths", []),
        "challenges": result.get("challenges", []),
        "recommendations": result.get("recommendations", [])
    }