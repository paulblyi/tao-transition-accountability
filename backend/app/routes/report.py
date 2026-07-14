from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import crud
from app.llm_processor import call_llm
import json
import logging

router = APIRouter(prefix="/api/report", tags=["report"])

def _limit_comments(data_list, max_items=30):
    """Return only the first `max_items` items from the list."""
    return data_list[:max_items]

@router.get("/sections")
def get_report_sections(
    province: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
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

    # ------------------------------------------------------------------
    # LLM Summaries (aggregated) – limited to 30 facilities each
    # ------------------------------------------------------------------
    summaries = {}

    # 4. Capacity Building summary
    cap_limited = _limit_comments(capacity, 30)
    if cap_limited:
        cap_text = "\n".join([
            f"{c['facility']}: gaps_supported={c['gaps_supported']}, nurse_testers={c['nurse_testers']}, "
            f"viac_trained={c['viac_trained']}, vl_mentored={c['vl_mentored']}, ahd_supported={c['ahd_supported']}, "
            f"logistics_supported={c['logistics_supported']}, oi_focal={c['oi_focal']}, vhw_mentored={c['vhw_mentored']}, "
            f"defaulter_pct={c['defaulter_pct']}, disruptions={c['disruptions']}"
            for c in cap_limited if c.get('gaps_supported') is not None
        ])
        if cap_text:
            try:
                prompt_cap = f"""
You are an expert in HIV programme transition. Based on the following aggregated capacity-building data across {len(cap_limited)} facilities, produce a JSON summary with:
- "summary": a 2-3 sentence overview.
- "strengths": list of positive findings.
- "gaps": list of areas needing improvement.
- "recommendations": actionable steps.

Data:
{cap_text}
Return only valid JSON.
"""
                resp = call_llm(prompt_cap, max_tokens=300)
                summaries["capacity"] = json.loads(resp)
            except Exception as e:
                summaries["capacity"] = {"error": str(e)}
        else:
            summaries["capacity"] = {"summary": "No capacity data available for the selected filters."}
    else:
        summaries["capacity"] = {"summary": "No capacity data available."}

    # 5. Financial summary
    fin_limited = _limit_comments(financial, 30)
    if fin_limited:
        fin_text = "\n".join([
            f"{f['facility']}: histology={f['histology']}, airtime={f['airtime']}, fuel={f['fuel']}, "
            f"stationery={f['stationery']}, cats={f['cats_stipends']}"
            for f in fin_limited if f.get('histology') is not None
        ])
        if fin_text:
            try:
                prompt_fin = f"""
You are an expert in HIV programme transition. Based on the following aggregated financial sustainability data across {len(fin_limited)} facilities, produce a JSON summary with:
- "summary": a 2-3 sentence overview.
- "strengths": list of positive findings.
- "gaps": list of areas needing improvement.
- "recommendations": actionable steps.

Data:
{fin_text}
Return only valid JSON.
"""
                resp = call_llm(prompt_fin, max_tokens=300)
                summaries["financial"] = json.loads(resp)
            except Exception as e:
                summaries["financial"] = {"error": str(e)}
        else:
            summaries["financial"] = {"summary": "No financial data available for the selected filters."}
    else:
        summaries["financial"] = {"summary": "No financial data available."}

    # 6. Challenges summary
    chal_limited = _limit_comments(challenges, 30)
    if chal_limited:
        chal_text = "\n".join([
            f"{c['facility']}: Challenges: {c['challenges']} | Mitigations: {c['mitigations']}"
            for c in chal_limited if c.get('challenges')
        ])
        if chal_text:
            try:
                prompt_chal = f"""
You are an expert in HIV programme transition. Based on the following aggregated challenges and mitigations across {len(chal_limited)} facilities, produce a JSON summary with:
- "summary": a 2-3 sentence overview.
- "common_challenges": list of most frequent challenges.
- "effective_mitigations": list of promising mitigations.
- "recommendations": additional actions.

Data:
{chal_text}
Return only valid JSON.
"""
                resp = call_llm(prompt_chal, max_tokens=300)
                summaries["challenges"] = json.loads(resp)
            except Exception as e:
                summaries["challenges"] = {"error": str(e)}
        else:
            summaries["challenges"] = {"summary": "No challenges data available for the selected filters."}
    else:
        summaries["challenges"] = {"summary": "No challenges data available."}

    # 7. Plans summary
    plan_limited = _limit_comments(plans, 30)
    if plan_limited:
        plan_text = "\n".join([f"{p['facility']}: {p['plan']}" for p in plan_limited if p.get('plan')])
        if plan_text:
            try:
                prompt_plan = f"""
You are an expert in HIV programme transition. Based on the following planned activities across {len(plan_limited)} facilities, produce a JSON summary with:
- "summary": a 2-3 sentence overview.
- "common_activities": list of recurring activities.
- "priority_areas": list of priority areas to focus on.

Data:
{plan_text}
Return only valid JSON.
"""
                resp = call_llm(prompt_plan, max_tokens=300)
                summaries["plans"] = json.loads(resp)
            except Exception as e:
                summaries["plans"] = {"error": str(e)}
        else:
            summaries["plans"] = {"summary": "No plans data available for the selected filters."}
    else:
        summaries["plans"] = {"summary": "No plans data available."}

    return {
        "total_facilities": len(reports),
        "capacity": capacity,
        "financial": financial,
        "challenges": challenges,
        "plans": plans,
        "summaries": summaries,
    }