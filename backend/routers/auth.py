import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.models import Admin
from backend.schemas.schemas import AdminLogin, AdminCreate, TokenResponse
from backend.utils.auth import hash_password, verify_password, create_access_token, get_current_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login", response_model=TokenResponse)
def login(credentials: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(
        Admin.username == credentials.username,
        Admin.is_active == True
    ).first()
    if not admin or not verify_password(credentials.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    admin.last_login = datetime.utcnow()
    db.commit()
    token = create_access_token({"sub": admin.username, "role": admin.role})
    logger.info(f"Admin login: {admin.username}")
    return TokenResponse(access_token=token, username=admin.username, role=admin.role)

@router.post("/register", response_model=dict)
def register_admin(data: AdminCreate, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    if current.role != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can create admins")
    if db.query(Admin).filter(Admin.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    admin = Admin(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role
    )
    db.add(admin)
    db.commit()
    return {"message": "Admin created successfully", "username": admin.username}

@router.get("/me")
def get_me(current: Admin = Depends(get_current_admin)):
    return {
        "id": current.id,
        "username": current.username,
        "email": current.email,
        "role": current.role,
        "last_login": current.last_login
    }

@router.post("/logout")
def logout(current: Admin = Depends(get_current_admin)):
    return {"message": "Logged out successfully"}
