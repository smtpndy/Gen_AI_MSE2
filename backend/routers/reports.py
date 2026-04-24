import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.models import Admin
from backend.schemas.schemas import ReportFilter
from backend.services.report_service import generate_pdf_report, generate_excel_report
from backend.utils.auth import get_current_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/pdf")
def download_pdf(
    filters: ReportFilter,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    try:
        path = generate_pdf_report(db, filters.start_date, filters.end_date, filters.branch, filters.student_id)
        return FileResponse(
            path,
            media_type="application/pdf",
            filename=path.split("/")[-1]
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.post("/excel")
def download_excel(
    filters: ReportFilter,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    try:
        path = generate_excel_report(db, filters.start_date, filters.end_date, filters.branch, filters.student_id)
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=path.split("/")[-1]
        )
    except Exception as e:
        logger.error(f"Excel generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

@router.get("/summary")
def report_summary(
    start_date: str = None,
    end_date: str = None,
    branch: str = None,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    from backend.services.report_service import get_filtered_attendance
    from sqlalchemy import func
    from backend.models.models import Attendance, Student

    records = get_filtered_attendance(db, start_date, end_date, branch)
    student_stats = {}
    for att, stu in records:
        if stu.student_id not in student_stats:
            student_stats[stu.student_id] = {
                "student_id": stu.student_id,
                "name": stu.name,
                "branch": stu.branch,
                "roll_number": stu.roll_number,
                "days_present": 0
            }
        student_stats[stu.student_id]["days_present"] += 1

    total_days = len(set(att.date for att, _ in records))
    for s in student_stats.values():
        s["percentage"] = round(s["days_present"] / total_days * 100, 1) if total_days else 0

    return {
        "total_records": len(records),
        "total_students": len(student_stats),
        "total_days": total_days,
        "students": sorted(student_stats.values(), key=lambda x: x["name"])
    }
