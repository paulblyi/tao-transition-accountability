from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# --------------------------------------------
# 1. Single facility report (request/response)
# --------------------------------------------
class ReportBase(BaseModel):
    province: str
    district: str
    facility: str
    week_ending: datetime
    tao_name: str
    visit_type: str
    date_submitted: datetime
    raw_data: Dict[str, Any]   # all extra columns from Excel
    insights: Optional[Dict[str, Any]] = None

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    id: int

    class Config:
        from_attributes = True   # Pydantic V2 (replaces orm_mode)


# --------------------------------------------
# 2. Aggregated statistics (for dashboard cards & charts)
# --------------------------------------------
class AggregatedResponse(BaseModel):
    # Facility count
    total_facilities: int

    # HTS
    avg_hts_total: Optional[float] = None
    avg_hts_mohcc: Optional[float] = None
    avg_hts_mohcc_pct: Optional[float] = None

    # Viral Load
    avg_vl_total: Optional[float] = None
    avg_vl_mohcc: Optional[float] = None
    avg_vl_mohcc_pct: Optional[float] = None

    # PrEP
    avg_prep_total: Optional[float] = None
    avg_prep_mohcc: Optional[float] = None
    avg_prep_mohcc_pct: Optional[float] = None

    # PBFW on PrEP
    avg_pbfw_total: Optional[float] = None
    avg_pbfw_mohcc: Optional[float] = None
    avg_pbfw_mohcc_pct: Optional[float] = None

    # Defaulter tracking (VHWs)
    avg_defaulter_total: Optional[float] = None
    avg_defaulter_vhw: Optional[float] = None
    avg_defaulter_vhw_pct: Optional[float] = None

    # VIAC
    avg_viac_total: Optional[float] = None
    avg_viac_mohcc: Optional[float] = None
    avg_viac_mohcc_pct: Optional[float] = None

    # ART
    avg_art_total: Optional[float] = None
    avg_art_mohcc: Optional[float] = None
    avg_art_mohcc_pct: Optional[float] = None

    # Defaulter tracking (VHCWs) – note the different column name
    avg_defaulter_vhcw: Optional[float] = None
    avg_defaulter_vhcw_pct: Optional[float] = None

    # Categorical breakdowns (e.g., HCC availability counts)
    categorical: Dict[str, Dict[str, int]]  # key: column name, value: {category: count}


# --------------------------------------------
# 3. AI‑generated insights response
# --------------------------------------------
class InsightResponse(BaseModel):
    insights: List[Dict[str, Any]]