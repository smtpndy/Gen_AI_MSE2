# 👁️ FaceAttend — AI Face Recognition Attendance System

A production-ready, full-stack AI-powered attendance system using real-time face recognition, natural language AI queries, and automated reporting.

---

## 🚀 Quick Start

```bash
# 1. Clone / extract project
cd faceattend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Run setup (installs deps + initializes DB)
python setup.py

# 4. Edit environment variables
cp .env.example .env
# → Set OPENAI_API_KEY in .env

# 5. Start server
bash start.sh
# OR:
uvicorn backend.main:app --reload --port 8000

# 6. Open: http://localhost:8000
#    Login: admin / Admin@123
```

---

## 🐳 Docker

```bash
docker-compose up --build
# App → http://localhost:8000
```

---

## 📁 Project Structure

```
faceattend/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # SQLAlchemy engine & session
│   ├── models/models.py        # DB models: Student, Attendance, Admin
│   ├── schemas/schemas.py      # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py             # Login, JWT token
│   │   ├── students.py         # Student CRUD + face upload
│   │   ├── attendance.py       # Face recognition + mark attendance
│   │   ├── reports.py          # PDF + Excel download
│   │   └── ai_query.py         # Natural language → SQL
│   ├── services/
│   │   ├── face_service.py     # OpenCV + face_recognition logic
│   │   ├── attendance_service.py
│   │   ├── report_service.py   # ReportLab + openpyxl
│   │   ├── ai_service.py       # OpenAI + rule-based NL→SQL
│   │   └── admin_service.py
│   └── utils/
│       ├── auth.py             # JWT + bcrypt
│       └── logger.py
├── frontend/
│   ├── index.html              # Login page
│   ├── dashboard.html          # Stats overview
│   ├── register.html           # Student registration + face capture
│   ├── attendance.html         # Live camera attendance
│   ├── students.html           # Student management
│   ├── reports.html            # Report generation
│   ├── ai-query.html           # AI natural language query
│   ├── css/style.css           # Shared styles
│   └── js/app.js               # Shared JS utilities
├── database/                   # SQLite DB + face images
├── reports/                    # Generated PDF/Excel files
├── backups/                    # DB backups
├── scripts/
│   ├── backup_db.py            # Daily backup script
│   ├── seed_demo_data.py       # Demo data seeder
│   └── install_face_recognition.sh
├── setup.py                    # One-click setup
├── start.sh                    # Start server
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./database/attendance.db` | DB connection string |
| `SECRET_KEY` | *(change this!)* | JWT signing key |
| `OPENAI_API_KEY` | *(required for AI)* | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model to use |
| `FACE_TOLERANCE` | `0.5` | Face match tolerance (lower = stricter) |
| `TOKEN_EXPIRE_HOURS` | `24` | JWT token expiry |

---

## 🔑 Default Credentials

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `Admin@123` |

> Change immediately in production!

---

## 📸 Face Recognition Flow

1. **Register** student with ID, name, roll, branch
2. **Capture** 20–50 images via webcam (multiple angles)
3. **Live Attendance**: camera scans faces → matches encodings → marks attendance
4. **Tolerance**: `0.5` = ~80–90% accuracy; lower = stricter but more misses

### Face Recognition Dependencies

```bash
# Linux/macOS:
bash scripts/install_face_recognition.sh

# Windows (use pre-built wheels):
pip install cmake dlib face-recognition opencv-python-headless
```

> If `face_recognition` is unavailable, system runs in **mock mode** (still functional for testing).

---

## 🤖 AI Query Examples

| Query | What it does |
|---|---|
| "Show today's attendance" | Lists today's present students |
| "Who has low attendance?" | Students below 75% |
| "Show CSE branch last week" | Branch-filtered weekly view |
| "Give attendance summary" | Daily counts for last 30 days |
| "Which students haven't attended this week?" | Absent detection |

Add `OPENAI_API_KEY` for AI-powered summaries; falls back to rule-based parsing otherwise.

---

## 📊 Reports

- **PDF**: Full attendance table with styling (ReportLab)
- **Excel**: Multi-sheet workbook with summary tab (openpyxl)
- **Filters**: Date range, branch, individual student

---

## 🔐 Security

- Passwords hashed with **bcrypt**
- API protected with **JWT Bearer tokens**
- Face encodings stored as JSON (not raw images in DB)
- Environment-based secrets (never hardcoded)

---

## 🗄️ Database Schema

```
students        → id, student_id, name, roll_number, branch, face_encodings, ...
attendance      → id, student_id (FK), date, time_in, status, confidence, ...
admins          → id, username, hashed_password, role, ...
face_images     → id, student_id (FK), image_path, angle, ...
```

Indexes on: `student_id`, `roll_number`, `branch`, `attendance.date`, `attendance.(student_id, date)`

---

## 🔄 Daily Backup

```bash
# Add to crontab (runs at 2 AM daily):
0 2 * * * /path/to/venv/bin/python /path/to/scripts/backup_db.py
```

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| Frontend | HTML5, CSS3, Vanilla JS |
| Face AI | OpenCV, face_recognition (dlib) |
| GenAI | OpenAI GPT-4o-mini |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Reports | ReportLab (PDF), openpyxl (Excel) |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Deploy | Docker, Uvicorn |

---

## 📝 License

MIT License — free to use and modify.
