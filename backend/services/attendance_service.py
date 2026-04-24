import logging
from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models.models import Attendance, Student

logger = logging.getLogger(__name__)

def mark_attendance(
    db: Session,
    student_db_id: int,
    confidence: float = None,
    marked_by: str = "face_recognition",
    target_date: str = None
) -> dict:
    today = target_date or date.today().strftime("%Y-%m-%d")
    existing = db.query(Attendance).filter(
        and_(Attendance.student_id == student_db_id, Attendance.date == today)
    ).first()
    if existing:
        return {"success": False, "already_marked": True, "message": "Attendance already marked for today"}
    record = Attendance(
        student_id=student_db_id,
        date=today,
        time_in=datetime.utcnow(),
        status="present",
        confidence=confidence,
        marked_by=marked_by
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"success": True, "already_marked": False, "record_id": record.id, "message": "Attendance marked successfully"}

def get_attendance_summary(db: Session, date_str: str = None) -> dict:
    target = date_str or date.today().strftime("%Y-%m-%d")
    records = db.query(Attendance).filter(Attendance.date == target).all()
    total_students = db.query(Student).filter(Student.is_active == True).count()
    return {
        "date": target,
        "present": len(records),
        "total": total_students,
        "absent": max(0, total_students - len(records)),
        "percentage": round((len(records) / total_students * 100) if total_students else 0, 1)
    }
