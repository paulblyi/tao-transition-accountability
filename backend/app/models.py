from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from app.database import Base

class FacilityReport(Base):
    __tablename__ = "facility_reports"

    id = Column(Integer, primary_key=True, index=True)

    # Core filters
    province = Column(String)
    district = Column(String)
    facility = Column(String)
    week_ending = Column(DateTime)
    tao_name = Column(String)
    visit_type = Column(String)
    date_submitted = Column(DateTime)

    # Unique identifier
    _uuid = Column(String, unique=True)
    _submission_time = Column(DateTime)

    # GPS coordinates
    gps_lat = Column(Float)
    gps_lon = Column(Float)
    gps_alt = Column(Float)
    gps_precision = Column(Float)

    # Numeric metrics (all numeric – int or float)
    hts_total = Column(Integer)
    hts_mohcc = Column(Integer)
    hts_mohcc_pct = Column(Float)
    vl_total = Column(Integer)
    vl_mohcc = Column(Integer)
    vl_mohcc_pct = Column(Float)
    prep_total = Column(Integer)
    prep_mohcc = Column(Integer)
    prep_mohcc_pct = Column(Float)
    pbfw_total = Column(Integer)
    pbfw_mohcc = Column(Integer)
    pbfw_mohcc_pct = Column(Float)
    defaulter_total = Column(Integer)
    defaulter_vhw = Column(Integer)
    defaulter_vhw_pct = Column(Float)
    viac_total = Column(Integer)
    viac_mohcc = Column(Integer)
    viac_mohcc_pct = Column(Float)
    art_total = Column(Integer)
    art_mohcc = Column(Integer)
    art_mohcc_pct = Column(Float)
    defaulter_vhcw = Column(Integer)
    defaulter_vhcw_pct = Column(Float)

    # JSON fields for all extra data
    raw_data = Column(JSON)
    insights = Column(JSON)   # for LLM outputs (optional)