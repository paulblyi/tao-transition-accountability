from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import crud
from app.llm_processor import (
    call_llm,
    process_comments_sampled,
    process_comments_keyword,
    process_comments_chunked
)
from app.utils import safe_json_loads
import json
import logging
import re

router = APIRouter(prefix="/api/report", tags=["report"])

# ----------------------------------------------------------------------
# Helper: limit items for LLM prompts
# ----------------------------------------------------------------------
def _limit_comments(data_list, max_items=20):
    return data_list[:max_items]

# ----------------------------------------------------------------------
# Rule-based fallback summaries (with llm_failed flag)
# ----------------------------------------------------------------------
def generate_capacity_summary(data: list) -> dict:
    if not data:
        return {"summary": "No capacity building data available.", "llm_failed": False}
    total = len(data)
    with_gaps = sum(1 for c in data if c.get('gaps_supported') is not None)
    with_testers = sum(1 for c in data if c.get('nurse_testers') is not None)
    with_viac = sum(1 for c in data if c.get('viac_trained') is not None)
    with_vl = sum(1 for c in data if c.get('vl_mentored') is not None)
    with_ahd = sum(1 for c in data if c.get('ahd_supported') is not None)
    with_oi_focal = sum(1 for c in data if c.get('oi_focal') == "Yes")
    summary = (
        f"Across {total} facilities, {with_gaps} reported capacity gaps. "
        f"{with_testers} facilities have nurse testers, {with_viac} have VIAC-trained staff, "
        f"{with_vl} have VL mentorship, {with_ahd} have AHD support, "
        f"and {with_oi_focal} have an OI focal person in place."
    )
    return {"summary": summary, "llm_failed": False}

def generate_financial_summary(data: list) -> dict:
    if not data:
        return {"summary": "No financial sustainability data available.", "llm_failed": False}
    total = len(data)
    has_histology = sum(1 for f in data if f.get('histology') == "Yes")
    has_airtime = sum(1 for f in data if f.get('airtime') == "Yes")
    has_fuel = sum(1 for f in data if f.get('fuel') == "Yes")
    has_stationery = sum(1 for f in data if f.get('stationery') == "Yes")
    has_cats = sum(1 for f in data if f.get('cats_stipends') == "Yes")
    summary = (
        f"Of {total} facilities, {has_histology} have histology coupons, "
        f"{has_airtime} have facility airtime, {has_fuel} have fuel for outreach, "
        f"{has_stationery} have stationery for VHCWs, and {has_cats} receive CATS stipends from NAC."
    )
    return {"summary": summary, "llm_failed": False}

def generate_challenges_summary(data: list) -> dict:
    if not data:
        return {"summary": "No challenges data available.", "llm_failed": False}
    total = len(data)
    challenges_mentioned = sum(1 for c in data if c.get('challenges') is not None)
    mitigations_mentioned = sum(1 for c in data if c.get('mitigations') is not None)
    summary = (
        f"Across {total} facilities, {challenges_mentioned} reported challenges, "
        f"and {mitigations_mentioned} have documented mitigation strategies."
    )
    return {"summary": summary, "llm_failed": False}

def generate_plans_summary(data: list) -> dict:
    if not data:
        return {"summary": "No plans data available.", "llm_failed": False}
    total = len(data)
    has_plan = sum(1 for p in data if p.get('plan') is not None)
    summary = f"Of {total} facilities, {has_plan} have documented plans for next week."
    return {"summary": summary, "llm_failed": False}

# ----------------------------------------------------------------------
# Helper to build comment blocks for a section
# ----------------------------------------------------------------------
def _build_comment_blocks(data, section_name: str) -> list:
    blocks = []
    for item in data:
        if not isinstance(item, dict) or not item.get('facility'):
            continue
        facility = item['facility']
        if section_name == "challenges":
            if item.get('challenges'):
                blocks.append(
                    f"Facility: {facility}\n"
                    f"Challenges: {item['challenges']}\n"
                    f"Mitigations: {item.get('mitigations', '')}"
                )
        else:
            lines = []
            for k, v in item.items():
                if k == 'facility' or not v:
                    continue
                lines.append(f"{k}: {v}")
            if lines:
                blocks.append(f"Facility: {facility}\n" + "\n".join(lines))
    return blocks

# ----------------------------------------------------------------------
# Helper: process a section with chosen analysis mode
# ----------------------------------------------------------------------
def _process_section_with_mode(data: list, blocks: list, fallback_func, analysis_mode: str):
    """
    Process a section using the chosen analysis mode.
    data: the original data list (e.g., cap_limited)
    blocks: the comment blocks built from data
    fallback_func: the rule-based summary function
    analysis_mode: "fallback", "sample", "keyword", "chunked"
    """
    if not data:
        return fallback_func([])
    
    if analysis_mode == "fallback":
        # Use the actual data to generate the rule-based summary
        return fallback_func(data)
    
    if not blocks:
        return fallback_func(data)  # fallback if no blocks available
    
    if analysis_mode == "chunked":
        result = process_comments_chunked(blocks)
    elif analysis_mode == "keyword":
        result = process_comments_keyword(blocks)
    else:  # "sample"
        result = process_comments_sampled(blocks, max_comments=15)
    
    # Ensure we return a dict with at least summary
    return result

# ----------------------------------------------------------------------
# Main endpoint – sections 4-7
# ----------------------------------------------------------------------
@router.get("/sections")
def get_report_sections(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip_llm: bool = False,
    analysis_mode: str = "sample",
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    if not reports:
        return {"error": "No data found for the selected filters."}

    # Build data lists (unchanged)
    capacity, financial, challenges, plans = [], [], [], []
    for r in reports:
        if not r.raw_data:
            continue
        capacity.append({
            "facility": r.facility,
            "gaps_supported": r.raw_data.get("Nurses with capacity gaps supported through mentorship"),
            "nurse_testers": r.raw_data.get("Number of MOHCC nurse testers"),
            "viac_trained": r.raw_data.get("MOHCC nurses trained in cervical cancer services"),
            "vl_mentored": r.raw_data.get("MOHCC nurses mentored on VL cascade"),
            "ahd_supported": r.raw_data.get("MOHCC nurses supported with AHD skills"),
            "logistics_supported": r.raw_data.get("MOHCC nurses supported with logistics skills"),
            "oi_zhi": r.raw_data.get("MOHCC nurses working in OI clinic with ZHI support"),
            "oi_focal": r.raw_data.get("MOHCC OIC focal person at facility?"),
            "vhw_mentored": r.raw_data.get("Community cadres/VHWs mentored in defaulter tracking"),
            "defaulter_tracked": r.raw_data.get("Number of defaulters tracked by VHCW (N)"),
            "defaulter_pct": r.raw_data.get("vhcw_defaulters_tracked_percentage"),
            "disruptions": r.raw_data.get("Did the site report any service delivery disruptions"),
            "support_gaps": r.raw_data.get("Who supported to address gaps?"),
        })
        financial.append({
            "facility": r.facility,
            "histology": r.raw_data.get("Histology Coupons"),
            "histology_comment": r.raw_data.get("Histology Coupons - Comments"),
            "airtime": r.raw_data.get("Facility Airtime"),
            "airtime_comment": r.raw_data.get("Facility Airtime - Comments"),
            "fuel": r.raw_data.get("Fuel for outreach/programme activities"),
            "fuel_comment": r.raw_data.get("Fuel for outreach/programme activities - Comments"),
            "stationery": r.raw_data.get("Provision of stationery to VHCWs"),
            "stationery_comment": r.raw_data.get("Provision of stationery to VHCWs - Comments"),
            "cats_stipends": r.raw_data.get("Provision of stipends for CATS by NAC"),
            "cats_comment": r.raw_data.get("Provision of stipends for CATS by NAC - Comments"),
        })
        challenges.append({
            "facility": r.facility,
            "challenges": r.raw_data.get("Key Challenges"),
            "mitigations": r.raw_data.get("Mitigation Strategies"),
        })
        plans.append({
            "facility": r.facility,
            "plan": r.raw_data.get("Facility planned activities for next week"),
        })

    cap_limited = _limit_comments(capacity, 20)
    fin_limited = _limit_comments(financial, 20)
    chal_limited = _limit_comments(challenges, 20)
    plan_limited = _limit_comments(plans, 20)

    summaries = {}
    any_llm_failed = False

    # If skip_llm is true, use rule-based summaries directly
    if skip_llm:
        summaries["capacity"] = generate_capacity_summary(cap_limited)
        summaries["financial"] = generate_financial_summary(fin_limited)
        summaries["challenges"] = generate_challenges_summary(chal_limited)
        summaries["plans"] = generate_plans_summary(plan_limited)
        return {
            "total_facilities": len(reports),
            "capacity": capacity,
            "financial": financial,
            "challenges": challenges,
            "plans": plans,
            "summaries": summaries,
            "llm_failed": False
        }

    # Build comment blocks for each section
    cap_blocks = _build_comment_blocks(cap_limited, "capacity")
    fin_blocks = _build_comment_blocks(fin_limited, "financial")
    chal_blocks = _build_comment_blocks(chal_limited, "challenges")
    plan_blocks = _build_comment_blocks(plan_limited, "plans")

    # Process each section with the chosen analysis_mode
    try:
        summaries["capacity"] = _process_section_with_mode(
            cap_limited, cap_blocks, generate_capacity_summary, analysis_mode
        )
    except Exception as e:
        logging.error(f"Capacity section failed: {e}")
        summaries["capacity"] = generate_capacity_summary(cap_limited)
        summaries["capacity"]["llm_failed"] = True
        any_llm_failed = True

    try:
        summaries["financial"] = _process_section_with_mode(
            fin_limited, fin_blocks, generate_financial_summary, analysis_mode
        )
    except Exception as e:
        logging.error(f"Financial section failed: {e}")
        summaries["financial"] = generate_financial_summary(fin_limited)
        summaries["financial"]["llm_failed"] = True
        any_llm_failed = True

    try:
        summaries["challenges"] = _process_section_with_mode(
            chal_limited, chal_blocks, generate_challenges_summary, analysis_mode
        )
    except Exception as e:
        logging.error(f"Challenges section failed: {e}")
        summaries["challenges"] = generate_challenges_summary(chal_limited)
        summaries["challenges"]["llm_failed"] = True
        any_llm_failed = True

    try:
        summaries["plans"] = _process_section_with_mode(
            plan_limited, plan_blocks, generate_plans_summary, analysis_mode
        )
    except Exception as e:
        logging.error(f"Plans section failed: {e}")
        summaries["plans"] = generate_plans_summary(plan_limited)
        summaries["plans"]["llm_failed"] = True
        any_llm_failed = True

    return {
        "total_facilities": len(reports),
        "capacity": capacity,
        "financial": financial,
        "challenges": challenges,
        "plans": plans,
        "summaries": summaries,
        "llm_failed": any_llm_failed,
    }