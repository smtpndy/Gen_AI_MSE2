import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.models import Student, Admin, FaceImage
from backend.schemas.schemas import StudentCreate, StudentUpdate, StudentResponse
from backend.services.face_service import get_face_encoding, encode_image_from_base64, save_face_image, detect_faces_in_image
from backend.utils.auth import get_current_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=StudentResponse)
def register_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    if db.query(Student).filter(Student.student_id == student_data.student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already registered")
    if db.query(Student).filter(Student.roll_number == student_data.roll_number).first():
        raise HTTPException(status_code=400, detail="Roll number already registered")
    student = Student(**student_data.dict())
    db.add(student)
    db.commit()
    db.refresh(student)
    logger.info(f"Student registered: {student.student_id}")
    return student

@router.post("/{student_id}/upload-face")
async def upload_face_image(
    student_id: str,
    image_data: str = Form(...),
    angle: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    image_array = encode_image_from_base64(image_data)
    if image_array is None:
        raise HTTPException(status_code=400, detail="Invalid image data")

    face_count = detect_faces_in_image(image_array)
    if face_count == 0:
        raise HTTPException(status_code=400, detail="No face detected in image")
    if face_count > 1:
        raise HTTPException(status_code=400, detail="Multiple faces detected. Please capture one face at a time")

    encoding = get_face_encoding(image_array)
    if encoding is None:
        raise HTTPException(status_code=400, detail="Could not extract face features")

    # Update stored encodings
    existing = json.loads(student.face_encodings) if student.face_encodings else []
    existing.append(encoding)
    student.face_encodings = json.dumps(existing)
    student.image_count = len(existing)

    # Save image file
    img_path = save_face_image(student_id, image_array, student.image_count)

    # Store face image record
    face_img = FaceImage(student_id=student.id, image_path=img_path, angle=angle)
    db.add(face_img)
    db.commit()

    return {
        "success": True,
        "images_captured": student.image_count,
        "message": f"Face image {student.image_count} captured successfully"
    }

@router.get("/", response_model=List[StudentResponse])
def list_students(
    branch: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    query = db.query(Student)
    if active_only:
        query = query.filter(Student.is_active == True)
    if branch:
        query = query.filter(Student.branch == branch)
    return query.order_by(Student.name).all()

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: str, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: str,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, val in data.dict(exclude_unset=True).items():
        setattr(student, field, val)
    db.commit()
    db.refresh(student)
    return student

@router.delete("/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.is_active = False
    db.commit()
    return {"message": "Student deactivated"}

@router.get("/branches/list")
def get_branches(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    from sqlalchemy import distinct
    branches = db.query(distinct(Student.branch)).filter(Student.is_active == True).all()
    return {"branches": [b[0] for b in branches]}
