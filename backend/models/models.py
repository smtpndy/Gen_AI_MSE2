from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, Index, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    roll_number = Column(String(20), unique=True, nullable=False, index=True)
    branch = Column(String(50), nullable=False, index=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(15), nullable=True)
    face_encodings = Column(Text, nullable=True)  # JSON array of face encodings
    image_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    attendances = relationship("Attendance", back_populates="student")

    __table_args__ = (
        Index("idx_student_branch_active", "branch", "is_active"),
    )

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    time_in = Column(DateTime, default=datetime.utcnow)
    status = Column(String(10), default="present")
    confidence = Column(Float, nullable=True)
    marked_by = Column(String(20), default="face_recognition")
    student = relationship("Student", back_populates="attendances")

    __table_args__ = (
        Index("idx_attendance_student_date", "student_id", "date", unique=True),
        Index("idx_attendance_date", "date"),
    )

class FaceImage(Base):
    __tablename__ = "face_images"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    image_path = Column(String(255), nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow)
    angle = Column(String(20), nullable=True)
