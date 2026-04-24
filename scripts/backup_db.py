#!/usr/bin/env python3
"""
Daily automated database backup script.
Run via cron: 0 2 * * * /path/to/venv/bin/python /path/to/scripts/backup_db.py
"""
import os
import sys
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/backup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./database/attendance.db")
KEEP_DAYS = int(os.getenv("BACKUP_KEEP_DAYS", "7"))

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)


def backup_sqlite():
    if not DB_URL.startswith("sqlite"):
        logger.info("Not SQLite — skipping file backup")
        return

    db_path = DB_URL.replace("sqlite:///", "").replace("sqlite://", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]

    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"attendance_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    shutil.copy2(db_path, backup_path)
    size = os.path.getsize(backup_path) / 1024
    logger.info(f"Backup created: {backup_path} ({size:.1f} KB)")

    cleanup_old_backups()


def cleanup_old_backups():
    cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
    removed = 0
    for f in Path(BACKUP_DIR).glob("attendance_backup_*.db"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            f.unlink()
            removed += 1
            logger.info(f"Removed old backup: {f.name}")
    if removed:
        logger.info(f"Cleaned up {removed} old backup(s)")
    else:
        logger.info("No old backups to clean up")


def list_backups():
    backups = sorted(Path(BACKUP_DIR).glob("attendance_backup_*.db"), reverse=True)
    if backups:
        logger.info(f"Current backups ({len(backups)}):")
        for b in backups:
            size = b.stat().st_size / 1024
            mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            logger.info(f"  {b.name} — {size:.1f} KB — {mtime}")
    else:
        logger.info("No backups found")


if __name__ == "__main__":
    logger.info("=== Starting database backup ===")
    backup_sqlite()
    list_backups()
    logger.info("=== Backup complete ===")
