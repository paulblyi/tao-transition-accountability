from app.database import SessionLocal
from app.models import FacilityReport
from app.llm_processor import process_comments

def update_existing_insights():
    db = SessionLocal()
    reports = db.query(FacilityReport).filter(FacilityReport.insights.is_(None)).all()
    print(f"Processing {len(reports)} reports...")
    for report in reports:
        # Extract comments from raw_data
        comments_dict = {k: v for k, v in report.raw_data.items() if 'Comment' in k or 'Comments' in k}
        if comments_dict:
            report.insights = process_comments(comments_dict)
        else:
            report.insights = {"summary": "No comments to analyse.", "categories": [], "challenges": [], "mitigations": []}
    db.commit()
    db.close()
    print("Done!")

if __name__ == "__main__":
    update_existing_insights()