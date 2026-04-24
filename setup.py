#!/usr/bin/env python3
"""
setup.py — Full project setup for FaceAttend
Run: python setup.py
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DIRS = [
    "database/face_images",
    "reports",
    "backups",
    "logs",
    "frontend/css",
    "frontend/js",
    "frontend/pages",
    "backend/routers",
    "backend/services",
    "backend/models",
    "backend/schemas",
    "backend/utils",
    "scripts",
]

def banner(msg):
    print(f"\n{'='*50}")
    print(f"  {msg}")
    print('='*50)

def create_dirs():
    banner("Creating project directories...")
    for d in DIRS:
        path = ROOT / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {d}/")

def create_env():
    banner("Setting up environment...")
    env_example = ROOT / ".env.example"
    env_file = ROOT / ".env"
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("  ✓ Created .env from .env.example")
        print("  ⚠  Edit .env and add your OPENAI_API_KEY")
    else:
        print("  ✓ .env already exists")

def install_deps():
    banner("Installing Python dependencies...")
    req = ROOT / "requirements.txt"
    if not req.exists():
        print("  ⚠  requirements.txt not found, skipping")
        return
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(req)
        ])
        print("  ✓ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠  Dependency install error: {e}")
        print("     Try: pip install -r requirements.txt")
        print("     For face_recognition: bash scripts/install_face_recognition.sh")

def init_db():
    banner("Initializing database...")
    try:
        sys.path.insert(0, str(ROOT))
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        from backend.database import engine, Base
        Base.metadata.create_all(bind=engine)
        from backend.services.admin_service import ensure_default_admin
        ensure_default_admin()
        print("  ✓ Database tables created")
        print("  ✓ Default admin created: admin / Admin@123")
    except Exception as e:
        print(f"  ⚠  DB init error: {e}")

def seed_demo():
    banner("Seeding demo data...")
    try:
        subprocess.check_call([sys.executable, str(ROOT / "scripts/seed_demo_data.py")])
    except Exception as e:
        print(f"  ⚠  Seeding error: {e}")

def print_summary():
    banner("✅ Setup Complete!")
    print("""
  Next steps:
  ─────────────────────────────────────────────
  1. Edit .env and set your OPENAI_API_KEY

  2. Start the server:
       python -m uvicorn backend.main:app --reload --port 8000
     OR:
       bash start.sh

  3. Open browser:
       http://localhost:8000

  4. Login with:
       Username: admin
       Password: Admin@123

  5. Docker (optional):
       docker-compose up --build

  ─────────────────────────────────────────────
  Face Recognition Setup:
    bash scripts/install_face_recognition.sh

  Daily Backup (add to cron):
    0 2 * * * python /path/to/scripts/backup_db.py
  ─────────────────────────────────────────────
    """)

if __name__ == "__main__":
    print("🚀 FaceAttend Setup Script")
    create_dirs()
    create_env()
    install_deps()
    init_db()
    if "--seed" in sys.argv or "--demo" in sys.argv:
        seed_demo()
    print_summary()
