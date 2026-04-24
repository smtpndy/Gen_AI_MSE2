import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

SCHEMA_CONTEXT = """
Database Schema (SQLite/PostgreSQL):

Table: students
- id (INTEGER, PK)
- student_id (TEXT, unique)
- name (TEXT)
- roll_number (TEXT, unique)
- branch (TEXT) -- e.g., CSE, ECE, ME, CE, EE
- email (TEXT)
- phone (TEXT)
- image_count (INTEGER)
- is_active (BOOLEAN)
- registered_at (DATETIME)

Table: attendance
- id (INTEGER, PK)
- student_id (INTEGER, FK -> students.id)
- date (TEXT) -- format: YYYY-MM-DD
- time_in (DATETIME)
- status (TEXT) -- 'present' or 'absent'
- confidence (REAL) -- face recognition confidence percentage
- marked_by (TEXT) -- 'face_recognition' or 'manual'

Table: admins
- id (INTEGER, PK)
- username (TEXT)
- email (TEXT)
- role (TEXT)
- created_at (DATETIME)

Today's date: {today}
"""

SYSTEM_PROMPT = """You are an AI assistant for a Face Recognition Attendance Management System.
Convert natural language queries into SQLite-compatible SQL queries.

Rules:
1. Return ONLY a JSON object with keys: "sql", "explanation", "summary_hint"
2. Use only SELECT statements (no INSERT/UPDATE/DELETE)
3. Always JOIN attendance with students when referencing student info
4. Use date format YYYY-MM-DD
5. For "last week" use date >= date('now', '-7 days')
6. For "this month" use strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
7. For "low attendance" use students with less than 75% attendance
8. Always include student name, student_id, branch in results when relevant
9. Limit results to 100 rows unless asked for all
10. sql must be valid SQLite SQL

Example response:
{"sql": "SELECT s.name, s.branch, COUNT(a.id) as days_present FROM students s LEFT JOIN attendance a ON s.id = a.student_id WHERE a.date >= date('now', '-7 days') GROUP BY s.id ORDER BY days_present DESC LIMIT 50", "explanation": "Shows attendance for all students in the last 7 days", "summary_hint": "attendance_by_student"}
"""

def call_openai(prompt: str, system: str = "") -> str:
    """Call OpenAI API and return text response."""
    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{OPENAI_BASE_URL}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"OpenAI call failed: {e}")
        raise


def natural_language_to_sql(query: str) -> dict:
    """Convert NL query to SQL using OpenAI."""
    today = datetime.now().strftime("%Y-%m-%d")
    schema = SCHEMA_CONTEXT.format(today=today)
    full_prompt = f"{schema}\n\nUser query: {query}\n\nRespond with JSON only."
    
    if not OPENAI_API_KEY:
        return _rule_based_fallback(query, today)
    
    raw = call_openai(full_prompt, SYSTEM_PROMPT)
    # Strip markdown fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().strip("```")
    return json.loads(raw)


def _rule_based_fallback(query: str, today: str) -> dict:
    """Fallback rule-based query parsing when no API key."""
    q = query.lower()
    
    if "low attendance" in q or "below 75" in q or "poor attendance" in q:
        sql = """
            SELECT s.name, s.student_id, s.roll_number, s.branch,
                   COUNT(a.id) as days_present,
                   ROUND(COUNT(a.id) * 100.0 / (SELECT COUNT(DISTINCT date) FROM attendance), 1) as attendance_pct
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
            WHERE s.is_active = 1
            GROUP BY s.id
            HAVING attendance_pct < 75 OR attendance_pct IS NULL
            ORDER BY attendance_pct ASC
        """
        return {"sql": sql, "explanation": "Students with less than 75% attendance", "summary_hint": "low_attendance"}
    
    if "today" in q:
        sql = f"""
            SELECT s.name, s.student_id, s.roll_number, s.branch, a.time_in, a.confidence
            FROM attendance a JOIN students s ON a.student_id = s.id
            WHERE a.date = '{today}' ORDER BY a.time_in DESC
        """
        return {"sql": sql, "explanation": f"Today's attendance ({today})", "summary_hint": "today_attendance"}
    
    if "last week" in q or "this week" in q:
        sql = """
            SELECT s.name, s.student_id, s.branch, COUNT(a.id) as days_present
            FROM students s LEFT JOIN attendance a ON s.id = a.student_id
            WHERE a.date >= date('now', '-7 days')
            GROUP BY s.id ORDER BY days_present DESC
        """
        return {"sql": sql, "explanation": "Attendance for the last 7 days", "summary_hint": "weekly_attendance"}
    
    if "branch" in q:
        branches = ["cse", "ece", "me", "ce", "ee", "it"]
        branch_map = {"cse": "CSE", "ece": "ECE", "me": "ME", "ce": "CE", "ee": "EE", "it": "IT"}
        detected = next((branch_map[b] for b in branches if b in q), None)
        branch_filter = f"AND s.branch = '{detected}'" if detected else ""
        sql = f"""
            SELECT s.name, s.student_id, s.roll_number, s.branch, COUNT(a.id) as total_present
            FROM students s LEFT JOIN attendance a ON s.id = a.student_id
            WHERE s.is_active = 1 {branch_filter}
            GROUP BY s.id ORDER BY s.branch, s.name
        """
        return {"sql": sql, "explanation": f"Attendance by branch{' - ' + detected if detected else ''}", "summary_hint": "branch_attendance"}
    
    if "total" in q or "summary" in q or "overview" in q:
        sql = """
            SELECT a.date, COUNT(a.id) as present_count,
                   (SELECT COUNT(*) FROM students WHERE is_active=1) as total_students
            FROM attendance a
            GROUP BY a.date ORDER BY a.date DESC LIMIT 30
        """
        return {"sql": sql, "explanation": "Daily attendance summary", "summary_hint": "daily_summary"}
    
    # Default
    sql = f"""
        SELECT s.name, s.student_id, s.branch, a.date, a.status
        FROM attendance a JOIN students s ON a.student_id = s.id
        WHERE a.date = '{today}' ORDER BY s.name
    """
    return {"sql": sql, "explanation": "Today's attendance records", "summary_hint": "default"}


def execute_query_safe(db: Session, sql: str) -> list:
    """Execute a SELECT query safely."""
    sql = sql.strip()
    if not sql.upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    # Basic injection prevention
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
    for kw in forbidden:
        if kw in sql.upper():
            raise ValueError(f"Query contains forbidden keyword: {kw}")
    result = db.execute(text(sql))
    columns = list(result.keys())
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows


def summarize_results(rows: list, hint: str, query: str) -> str:
    """Generate a human-readable summary of query results."""
    count = len(rows)
    if count == 0:
        return "No records found for your query."
    
    if hint == "low_attendance":
        return f"Found {count} student(s) with low attendance (below 75%). The lowest attendance is {rows[-1].get('attendance_pct', 'N/A')}%."
    if hint == "today_attendance":
        return f"{count} student(s) marked present today."
    if hint == "weekly_attendance":
        top = rows[0] if rows else {}
        return f"Last week's data: {count} student records. Top attendance: {top.get('name', 'N/A')} with {top.get('days_present', 0)} days."
    if hint == "branch_attendance":
        branches = {}
        for r in rows:
            b = r.get('branch', 'Unknown')
            branches[b] = branches.get(b, 0) + 1
        summary = ", ".join([f"{b}: {c}" for b, c in branches.items()])
        return f"Attendance data for {count} students. Branches: {summary}"
    if hint == "daily_summary":
        latest = rows[0] if rows else {}
        return f"Showing {count} days of data. Most recent: {latest.get('date', 'N/A')} — {latest.get('present_count', 0)} present out of {latest.get('total_students', 0)} students."
    return f"Query returned {count} record(s)."


def process_ai_query(db: Session, query: str) -> dict:
    """Main entry point for AI query processing."""
    try:
        parsed = natural_language_to_sql(query)
        sql = parsed.get("sql", "")
        explanation = parsed.get("explanation", "")
        hint = parsed.get("summary_hint", "default")
        
        rows = execute_query_safe(db, sql)
        summary = summarize_results(rows, hint, query)
        
        # Try AI summary if key available
        if OPENAI_API_KEY and rows:
            try:
                ai_summary_prompt = f"User asked: '{query}'\nData: {json.dumps(rows[:10])}\nProvide a 2-3 sentence insight summary."
                summary = call_openai(ai_summary_prompt, "You are an attendance analytics assistant. Be concise and insightful.")
            except Exception:
                pass  # Use rule-based summary
        
        suggestions = [
            "Show today's attendance",
            "Who has low attendance?",
            "Show CSE branch attendance this month",
            "Show attendance summary last week",
            "Which students haven't attended this week?"
        ]
        
        return {
            "query": query,
            "sql_query": sql,
            "result": {"rows": rows[:100], "count": len(rows), "explanation": explanation},
            "summary": summary,
            "suggestions": suggestions[:3]
        }
    except Exception as e:
        logger.error(f"AI query error: {e}")
        return {
            "query": query,
            "sql_query": None,
            "result": {"rows": [], "count": 0, "explanation": "Query failed"},
            "summary": f"Could not process query: {str(e)}",
            "suggestions": ["Show today's attendance", "Who has low attendance?"]
        }
