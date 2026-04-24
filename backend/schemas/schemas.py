from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Auth
class AdminLogin(BaseModel):
    username: str
    password: str

class AdminCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "admin"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str

# Student
class StudentCreate(BaseModel):
    student_id: str
    name: str
    roll_number: str
    branch: str
    email: Optional[str] = None
    phone: Optional[str] = None

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    branch: Optional[str] = None
    is_active: Optional[bool] = None

class StudentResponse(BaseModel):
    id: int
    student_id: str
    name: str
    roll_number: str
    branch: str
    email: Optional[str]
    phone: Optional[str]
    image_count: int
    is_active: bool
    registered_at: datetime

    class Config:
        from_attributes = True

# Attendance
class AttendanceManual(BaseModel):
    student_id: str
    date: Optional[str] = None
    status: str = "present"

class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    date: str
    time_in: datetime
    status: str
    confidence: Optional[float]
    student_name: Optional[str] = None
    roll_number: Optional[str] = None
    branch: Optional[str] = None

    class Config:
        from_attributes = True

# Reports
class ReportFilter(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    branch: Optional[str] = None
    student_id: Optional[str] = None

# AI Query
class AIQueryRequest(BaseModel):
    query: str

class AIQueryResponse(BaseModel):
    query: str
    sql_query: Optional[str] = None
    result: dict
    summary: str
    suggestions: Optional[List[str]] = None

# Face Recognition
class FaceRecognitionResult(BaseModel):
    success: bool
    student_id: Optional[str] = None
    name: Optional[str] = None
    confidence: Optional[float] = None
    already_marked: bool = False
    message: str
