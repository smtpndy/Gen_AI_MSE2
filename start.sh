#!/bin/bash
# start.sh — Quick start for FaceAttend
set -e
cd "$(dirname "$0")"

echo "🚀 Starting FaceAttend AI Attendance System..."

# Create .env if missing
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠  Created .env from .env.example — please edit OPENAI_API_KEY"
fi

# Create required directories
mkdir -p database/face_images reports backups logs

# Activate venv if present
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run migrations (creates DB tables)
python3 -c "
from backend.database import engine, Base
Base.metadata.create_all(bind=engine)
from backend.services.admin_service import ensure_default_admin
ensure_default_admin()
print('✓ Database ready')
"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   FaceAttend is running!             ║"
echo "║   → http://localhost:8000            ║"
echo "║   Login: admin / Admin@123           ║"
echo "╚══════════════════════════════════════╝"
echo ""

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
