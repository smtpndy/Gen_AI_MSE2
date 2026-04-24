import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from backend.database import engine, Base
from backend.routers import auth, students, attendance, reports, ai_query
from backend.utils.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Face Recognition Attendance System...")
    Base.metadata.create_all(bind=engine)
    from backend.services.admin_service import ensure_default_admin
    ensure_default_admin()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="AI Face Recognition Attendance System",
    version="1.0.0",
    lifespan=lifespan
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allows requests from:
#   • FastAPI itself (8000)
#   • VS Code Live Server (5500)
#   • Vite / React dev servers (3000, 5173)
#   • Any other localhost port (via regex)
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "null",  # file:// origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
# ──────────────────────────────────────────────────────────────────────────────

app.include_router(auth.router,       prefix="/api/auth",       tags=["Authentication"])
app.include_router(students.router,   prefix="/api/students",   tags=["Students"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["Attendance"])
app.include_router(reports.router,    prefix="/api/reports",    tags=["Reports"])
app.include_router(ai_query.router,   prefix="/api/ai",         tags=["AI Query"])

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "css")), name="css")
    app.mount("/js",     StaticFiles(directory=os.path.join(frontend_path, "js")),  name="js")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "AI Attendance System"}

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/{page}")
async def serve_page(page: str):
    # Skip API and static routes
    if page.startswith("api") or page.startswith("static") or page.startswith("js"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    file_path = os.path.join(frontend_path, f"{page}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_path, "index.html"))
