import pandas as pd
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import FacilityReport
import json
from datetime import datetime
import numpy as np
from app.llm_processor import process_comments
import time

# Mapping of Excel column names to database column names (for numeric/metric columns)
NUMERIC_COLUMN_MAP = {
    'Total HTS provided at facility (D)': 'hts_total',
    'HTS provided by MOHCC staff (N)': 'hts_mohcc',
    'hts_mohcc_percentage': 'hts_mohcc_pct',
    'Total Viral Load collections done at facility (D)': 'vl_total',
    'Viral Load collections done by MOHCC (N)': 'vl_mohcc',
    'vl_collections_percentage': 'vl_mohcc_pct',
    'Total PrEP initiations done at facility (D)': 'prep_total',
    'PrEP initiations done by MOHCC (N)': 'prep_mohcc',
    'prep_initiations_percentage': 'prep_mohcc_pct',
    'Total Eligible PBFW initiated on PrEP at facility (D)': 'pbfw_total',
    'Eligible PBFW initiated on PrEP by MOHCC staff (N)': 'pbfw_mohcc',
    'pbfw_prep_prop_percentage': 'pbfw_mohcc_pct',
    'Total Defaulters tracking done at facility (D)': 'defaulter_total',
    'Defaulter tracking done by VHWs (N)': 'defaulter_vhw',
    'defaulter_tracking_percentage': 'defaulter_vhw_pct',
    'Total VIAC services provided at facility (D)': 'viac_total',
    'VIAC services provided by MOHCC cadres (N)': 'viac_mohcc',
    'viac_services_percentage': 'viac_mohcc_pct',
    'Total ART dispensed at facility (D)': 'art_total',
    'ART dispensed by MOHCC nurses (N)': 'art_mohcc',
    'art_dispensed_percentage': 'art_mohcc_pct',
    'Number of defaulters tracked by VHCW (N)': 'defaulter_vhcw',
    'vhcw_defaulters_tracked_percentage': 'defaulter_vhcw_pct',
}

# Columns that we store as separate fields (non-JSON)
SEPARATE_COLUMNS = [
    'province', 'district', 'facility', 'week_ending', 'tao_name',
    'visit_type', 'date_submitted', '_uuid', '_submission_time',
    'gps_lat', 'gps_lon', 'gps_alt', 'gps_precision'
]

def make_json_serializable(val):
    """Convert Pandas/NumPy types to JSON-serializable Python types."""
    if pd.isnull(val):
        return None
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.isoformat()
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    if isinstance(val, (np.floating, np.float64)):
        return float(val) if not np.isnan(val) else None
    if isinstance(val, np.bool_):
        return bool(val)
    return val

def load_excel(file_path: str):
    """Read Excel, map columns, and upsert into database."""
    # Read the Excel file
    df = pd.read_excel(file_path, sheet_name=0)  # adjust sheet name if needed
    df.columns = df.columns.str.strip()

    # Convert date columns
    if 'Week Ending' in df.columns:
        df['week_ending'] = pd.to_datetime(df['Week Ending'], errors='coerce')
    else:
        df['week_ending'] = None

    if 'Date Submitted' in df.columns:
        df['date_submitted'] = pd.to_datetime(df['Date Submitted'], errors='coerce')
    else:
        df['date_submitted'] = None

    if '_submission_time' in df.columns:
        df['_submission_time'] = pd.to_datetime(df['_submission_time'], errors='coerce')
    else:
        df['_submission_time'] = None

    # Map numeric columns (convert to numeric, coercing errors)
    for excel_col, db_col in NUMERIC_COLUMN_MAP.items():
        if excel_col in df.columns:
            df[db_col] = pd.to_numeric(df[excel_col], errors='coerce')
        else:
            df[db_col] = None

    # Map the separate columns (already handled dates above, now handle others)
    df['province'] = df.get('Province', '')
    df['district'] = df.get('District', '')
    df['facility'] = df.get('Facility', '')
    df['tao_name'] = df.get('Name of TAO', '')
    df['visit_type'] = df.get('Visit Type', '')
    df['_uuid'] = df.get('_uuid', '')

    # GPS coordinates
    df['gps_lat'] = pd.to_numeric(df.get('_GPS Coordinates_latitude', None), errors='coerce')
    df['gps_lon'] = pd.to_numeric(df.get('_GPS Coordinates_longitude', None), errors='coerce')
    df['gps_alt'] = pd.to_numeric(df.get('_GPS Coordinates_altitude', None), errors='coerce')
    df['gps_precision'] = pd.to_numeric(df.get('_GPS Coordinates_precision', None), errors='coerce')

    # Build raw_data JSON column with all columns not in separate or numeric lists
    all_cols = set(df.columns)
    exclude_cols = set(SEPARATE_COLUMNS) | set(NUMERIC_COLUMN_MAP.values()) | {'week_ending', 'date_submitted', '_submission_time'}
    exclude_cols.update(NUMERIC_COLUMN_MAP.keys())  # also exclude the original Excel names
    raw_cols = [col for col in all_cols if col not in exclude_cols and not col.startswith('Unnamed')]

    # For each row, create a dictionary of raw data, converting each value to JSON-serializable
    df['raw_data'] = df.apply(
        lambda row: {col: make_json_serializable(row[col]) for col in raw_cols if pd.notnull(row[col])},
        axis=1
    )

    # Save a copy of the final DataFrame to an Excel file for inspection
    df.to_excel("database_data.xlsx", index=False)
    print("✅ Saved processed DataFrame to database_data.xlsx")

    # Now upsert into database
    db: Session = SessionLocal()
    total_records = len(df)
    processed_count = 0
    total_time = 0
    
    for idx, row in df.iterrows():
        # Find existing record by _uuid, or create new
        existing = db.query(FacilityReport).filter_by(_uuid=row['_uuid']).first()
        if existing:
            report = existing
        else:
            report = FacilityReport()

        # Set the separate columns
        for col in SEPARATE_COLUMNS:
            setattr(report, col, row.get(col))

        # Set the numeric columns
        for db_col in NUMERIC_COLUMN_MAP.values():
            val = row.get(db_col)
            # If val is NaN, set to None (SQLAlchemy will interpret as NULL)
            if pd.isnull(val):
                val = None
            setattr(report, db_col, val)

        # Set the JSON raw data
        report.raw_data = row['raw_data']
        
        # ---- LLM processing ----
        if not report.insights:  # Only process if not already done
            # Extract comment fields from raw_data (keys with 'Comment' or 'Comments')
            comments_dict = {k: v for k, v in row['raw_data'].items() if 'Comment' in k or 'Comments' in k}
            if comments_dict:
                start = time.perf_counter()
                # Show progress before processing
                print(f"🔄 Processing record {idx+1}/{total_records} - {row['facility']}...")
                report.insights = process_comments(comments_dict)
                # time.sleep(12)  # 12 seconds between requests to respect 5/min limit (optional)
                processed_count += 1
                duration = time.perf_counter() - start
                print(f"✅ Record processing of: {idx+1} completed with {duration:.4f}s!")
                total_time += duration
            else:
                # If no comments, store a default
                report.insights = {"summary": "No comments to analyse.", "categories": [], "challenges": [], "mitigations": []}

        db.add(report)

    # Commit all changes at once
    db.commit()
    db.close()
    print(f"✅ ETL completed successfully. Processed {processed_count} records with LLM insights.")
    print(f"✅ Total time spent on LLM processing: {total_time:.2f} seconds")
    print(f"✅ Total records in Excel: {total_records}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3 or sys.argv[1] != '--file':
        print("Usage: python -m app.etl --file <path_to_excel>")
        sys.exit(1)
    file_path = sys.argv[2]
    load_excel(file_path)