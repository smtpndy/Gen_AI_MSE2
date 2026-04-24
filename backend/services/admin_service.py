import logging
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models.models import Admin
from backend.utils.auth import hash_password

logger = logging.getLogger(__name__)

DEFAULT_ADMIN = {
    "username": "admin",
    "email": "admin@attendance.local",
    "password": "Admin@123",
    "role": "superadmin"
}

def ensure_default_admin():
    db = SessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.username == DEFAULT_ADMIN["username"]).first()
        if not existing:
            admin = Admin(
                username=DEFAULT_ADMIN["username"],
                email=DEFAULT_ADMIN["email"],
                hashed_password=hash_password(DEFAULT_ADMIN["password"]),
                role=DEFAULT_ADMIN["role"],
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info(f"Default admin created: {DEFAULT_ADMIN['username']} / {DEFAULT_ADMIN['password']}")
        else:
            logger.info("Default admin already exists")
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
        db.rollback()
    finally:
        db.close()
