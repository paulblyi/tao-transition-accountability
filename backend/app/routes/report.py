from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import crud
from app.llm_processor import call_llm
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
# Main endpoint
# ----------------------------------------------------------------------
@router.get("/sections")
def get_report_sections(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip_llm: bool = False,
    db: Session = Depends(get_db)
):
    reports = crud.get_filtered_reports(db, province, district, start_date, end_date)
    if not reports:
        return {"error": "No data found for the selected filters."}

    # ------------------------------------------------------------------
    # 4. Capacity Building and Workforce Transition
    # ------------------------------------------------------------------
    capacity = []
    for r in reports:
        if r.raw_data:
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

    # ------------------------------------------------------------------
    # 5. Financial Sustainability
    # ------------------------------------------------------------------
    financial = []
    for r in reports:
        if r.raw_data:
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

    # ------------------------------------------------------------------
    # 6. Challenges & Mitigations
    # ------------------------------------------------------------------
    challenges = []
    for r in reports:
        if r.raw_data:
            challenges.append({
                "facility": r.facility,
                "challenges": r.raw_data.get("Key Challenges"),
                "mitigations": r.raw_data.get("Mitigation Strategies"),
            })

    # ------------------------------------------------------------------
    # 7. Plan for Next Week
    # ------------------------------------------------------------------
    plans = []
    for r in reports:
        if r.raw_data:
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

    # ------------------------------------------------------------------
    # Helper to process each section
    # ------------------------------------------------------------------
    def process_section(name, data, prompt_builder, fallback_func):
        nonlocal any_llm_failed
        if skip_llm:
            return fallback_func(data)
        try:
            text = prompt_builder(data)
            if text:
                resp = call_llm(text, max_tokens=300)
                result = safe_json_loads(resp)
                result["llm_failed"] = False
                return result
            else:
                return fallback_func(data)
        except Exception as e:
            logging.error(f"{name} summary LLM failed: {e}")
            any_llm_failed = True
            fallback = fallback_func(data)
            fallback["llm_failed"] = True
            return fallback

    # Build prompts for each section
    def cap_prompt(data):
        cap_text = "\n".join([
            f"{c['facility']}: gaps_supported={c['gaps_supported']}, nurse_testers={c['nurse_testers']}, "
            f"viac_trained={c['viac_trained']}, vl_mentored={c['vl_mentored']}, ahd_supported={c['ahd_supported']}, "
            f"logistics_supported={c['logistics_supported']}, oi_focal={c['oi_focal']}, vhw_mentored={c['vhw_mentored']}, "
            f"defaulter_pct={c['defaulter_pct']}, disruptions={c['disruptions']}"
            for c in data if c.get('gaps_supported') is not None
        ])
        if not cap_text:
            return None
        return f"""
You are an expert in HIV programme transition. Based on the following aggregated capacity-building data across {len(data)} facilities, produce a JSON summary with:
- "summary": a 2-3 sentence overview.
- "strengths": list of positive findings.
- "gaps": list of areas needing improvement.
- "recommendations": actionable steps.

Data:
{cap_text}
Return only valid JSON.
"""

    def fin_prompt(data):
        fin_text = "\n".join([
            f"{f['facility']}: histology={f['histology']}, airtime={f['airtime']}, fuel={f['fuel']}, "
            f"stationery={f['stationery']}, cats={f['cats_stipends']}"
            for f in data if f.get('histology') is not None
        ])
        if not fin_text:
            return None
        return f"""
You are an expert in HIV programme transition. Based on the following aggregated financial sustainability data across {len(data)} facilities, produce a JSON summary with:
- "summary": a 2-3 sentence overview.
- "strengths": list of positive findings.
- "gaps": list of areas needing improvement.
- "recommendations": actionable steps.

Data:
{fin_text}
Return only valid JSON.
"""

    def chal_prompt(data):
        chal_text = "\n".join([
            f"{c['facility']}: Challenges: {c['challenges']} | Mitigations: {c['mitigations']}"
            for c in data if c.get('challenges')
        ])
        if not chal_text:
            return None
        return f"""
You are an expert in HIV programme transition. Based on the following aggregated challenges and mitigations across {len(data)} facilities, produce a JSON summary with:
- "summary": a 2-3 sentence overview.
- "common_challenges": list of most frequent challenges.
- "effective_mitigations": list of promising mitigations.
- "recommendations": additional actions.

Data:
{chal_text}
Return only valid JSON.
"""

    def plan_prompt(data):
        plan_text = "\n".join([f"{p['facility']}: {p['plan']}" for p in data if p.get('plan')])
        if not plan_text:
            return None
        return f"""
You are an expert in HIV programme transition. Based on the following planned activities across {len(data)} facilities, produce a JSON summary with:
- "summary": a 2-3 sentence overview.
- "common_activities": list of recurring activities.
- "priority_areas": list of priority areas to focus on.

Data:
{plan_text}
Return only valid JSON.
"""

    # Process all sections
    summaries["capacity"] = process_section("Capacity", cap_limited, cap_prompt, generate_capacity_summary)
    summaries["financial"] = process_section("Financial", fin_limited, fin_prompt, generate_financial_summary)
    summaries["challenges"] = process_section("Challenges", chal_limited, chal_prompt, generate_challenges_summary)
    summaries["plans"] = process_section("Plans", plan_limited, plan_prompt, generate_plans_summary)

    # ------------------------------------------------------------------
    # Final response
    # ------------------------------------------------------------------
    return {
        "total_facilities": len(reports),
        "capacity": capacity,
        "financial": financial,
        "challenges": challenges,
        "plans": plans,
        "summaries": summaries,
        "llm_failed": any_llm_failed,
    }