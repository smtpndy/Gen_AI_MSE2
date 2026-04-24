import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.models import Admin
from backend.schemas.schemas import AIQueryRequest, AIQueryResponse
from backend.services.ai_service import process_ai_query
from backend.utils.auth import get_current_admin

router = APIRouter()
logger = logging.getLogger(__name__)

EXAMPLE_QUERIES = [
    "Show attendance of CSE branch last week",
    "Who has low attendance?",
    "Show today's attendance",
    "How many students attended this month?",
    "Show students with attendance below 75%",
    "Give me attendance summary for last 7 days",
    "Which branch has the highest attendance?",
    "Show all absent students today"
]

@router.post("/query", response_model=AIQueryResponse)
def ai_query(
    request: AIQueryRequest,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    logger.info(f"AI Query from {current.username}: {request.query}")
    result = process_ai_query(db, request.query)
    return AIQueryResponse(**result)

@router.get("/examples")
def get_examples(current: Admin = Depends(get_current_admin)):
    return {"examples": EXAMPLE_QUERIES}

@router.get("/status")
def ai_status(current: Admin = Depends(get_current_admin)):
    import os
    has_key = bool(os.getenv("OPENAI_API_KEY", ""))
    return {
        "openai_configured": has_key,
        "mode": "openai" if has_key else "rule_based",
        "message": "OpenAI API configured" if has_key else "Running in rule-based mode. Add OPENAI_API_KEY for AI-powered queries."
    }
