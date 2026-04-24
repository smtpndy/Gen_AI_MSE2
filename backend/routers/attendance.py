import logging
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.database import get_db
from backend.models.models import Student, Attendance, Admin
from backend.schemas.schemas import AttendanceManual, AttendanceResponse, FaceRecognitionResult
from backend.services.face_service import process_frame_for_recognition
from backend.services.attendance_service import mark_attendance, get_attendance_summary
from backend.utils.auth import get_current_admin
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

class FrameData(BaseModel):
    frame: str  # base64

@router.post("/recognize", response_model=FaceRecognitionResult)
def recognize_face(
    frame_data: FrameData,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    students = db.query(Student).filter(
        Student.is_active == True,
        Student.face_encodings.isnot(None)
    ).all()

    students_data = [
        {
            "student_id": s.student_id,
            "name": s.name,
            "roll_number": s.roll_number,
            "face_encodings": s.face_encodings
        }
        for s in students
    ]

    result = process_frame_for_recognition(frame_data.frame, students_data)

    if not result.get("success"):
        return FaceRecognitionResult(success=False, message=result.get("message", "Unknown error"))

    student = db.query(Student).filter(Student.student_id == result["student_id"]).first()
    if not student:
        return FaceRecognitionResult(success=False, message="Student not found in database")

    attendance_result = mark_attendance(db, student.id, confidence=result.get("confidence"))

    return FaceRecognitionResult(
        success=True,
        student_id=student.student_id,
        name=student.name,
        confidence=result.get("confidence"),
        already_marked=attendance_result["already_marked"],
        message=attendance_result["message"] if attendance_result["already_marked"] else f"✓ Attendance marked for {student.name}"
    )

@router.post("/mark-manual")
def mark_manual(
    data: AttendanceManual,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    student = db.query(Student).filter(Student.student_id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    result = mark_attendance(db, student.id, marked_by="manual", target_date=data.date)
    return result

@router.get("/today")
def today_attendance(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    today = date.today().strftime("%Y-%m-%d")
    records = db.query(Attendance, Student).join(Student).filter(Attendance.date == today).all()
    return {
        "date": today,
        "records": [
            {
                "id": att.id,
                "student_id": stu.student_id,
                "name": stu.name,
                "roll_number": stu.roll_number,
                "branch": stu.branch,
                "time_in": att.time_in.strftime("%H:%M:%S"),
                "status": att.status,
                "confidence": att.confidence
            }
            for att, stu in records
        ],
        "count": len(records)
    }

@router.get("/summary")
def attendance_summary(
    target_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    return get_attendance_summary(db, target_date)

@router.get("/history")
def attendance_history(
    student_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch: Optional[str] = None,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    query = db.query(Attendance, Student).join(Student)
    if student_id:
        query = query.filter(Student.student_id == student_id)
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    if branch:
        query = query.filter(Student.branch == branch)
    records = query.order_by(Attendance.date.desc()).limit(500).all()
    return [
        {
            "id": att.id,
            "student_id": stu.student_id,
            "name": stu.name,
            "roll_number": stu.roll_number,
            "branch": stu.branch,
            "date": att.date,
            "time_in": att.time_in.strftime("%H:%M:%S") if att.time_in else None,
            "status": att.status,
            "confidence": att.confidence,
            "marked_by": att.marked_by
        }
        for att, stu in records
    ]

@router.get("/stats/overview")
def overview_stats(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    from sqlalchemy import func, distinct
    today = date.today().strftime("%Y-%m-%d")
    total_students = db.query(Student).filter(Student.is_active==True).count()
    today_present = db.query(Attendance).filter(Attendance.date==today).count()
    total_records = db.query(Attendance).count()
    branches = db.query(distinct(Student.branch)).filter(Student.is_active==True).count()
    recent = db.query(Attendance, Student).join(Student).order_by(Attendance.time_in.desc()).limit(5).all()
    return {
        "total_students": total_students,
        "today_present": today_present,
        "today_absent": max(0, total_students - today_present),
        "today_percentage": round(today_present / total_students * 100, 1) if total_students else 0,
        "total_records": total_records,
        "branches": branches,
        "recent_entries": [
            {"name": stu.name, "time": att.time_in.strftime("%H:%M"), "branch": stu.branch}
            for att, stu in recent
        ]
    }
