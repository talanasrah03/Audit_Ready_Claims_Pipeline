import sqlite3
import json
from datetime import datetime

DB_PATH = "claims.db"


# =========================
# CONNECTION
# =========================
def get_connection():
    return sqlite3.connect(DB_PATH)


# =========================
# INIT DATABASE (RUN ONCE)
# =========================
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # CLAIMS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        claim_id TEXT PRIMARY KEY,
        status TEXT,
        risk_level TEXT
    )
    """)

    # AI RESULTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_results (
        claim_id TEXT,
        extracted_data TEXT,
        consistency_score REAL,
        validation_issues TEXT,
        explanation TEXT
    )
    """)

    # HUMAN REVIEWS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS human_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_id TEXT,
        action TEXT,
        corrected_fields TEXT,
        reviewer_note TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # CUSTOMER FEEDBACK
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_id TEXT,
        message TEXT,
        additional_info TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # AUDIT LOGS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_id TEXT,
        actor TEXT,
        action TEXT,
        details TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# =========================
# CLAIM INSERT
# =========================
def insert_claim(claim_id, status="pending", risk_level="LOW"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO claims (claim_id, status, risk_level)
    VALUES (?, ?, ?)
    """, (claim_id, status, risk_level))

    conn.commit()
    conn.close()


# =========================
# SAVE AI RESULT
# =========================
def save_ai_result(claim_id, extracted_data, consistency_score, issues, explanation):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO ai_results (claim_id, extracted_data, consistency_score, validation_issues, explanation)
    VALUES (?, ?, ?, ?, ?)
    """, (
        claim_id,
        json.dumps(extracted_data),
        consistency_score,
        json.dumps(issues),
        explanation
    ))

    conn.commit()
    conn.close()


# =========================
# SAVE HUMAN REVIEW ✅ FIXED
# =========================
def save_human_review(claim_id, action, corrected_fields=None, reviewer_note=None):
    conn = get_connection()
    cursor = conn.cursor()

    # ensure table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS human_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_id TEXT,
        action TEXT,
        corrected_fields TEXT,
        reviewer_note TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    INSERT INTO human_reviews (claim_id, action, corrected_fields, reviewer_note)
    VALUES (?, ?, ?, ?)
    """, (
        claim_id,
        action,
        json.dumps(corrected_fields) if corrected_fields else None,
        reviewer_note
    ))

    # update claim status
    if action == "approve":
        status = "approved"
    elif action == "reject":
        status = "rejected"
    elif action == "request_info":
        status = "pending_info"
    else:
        status = "under_review"

    cursor.execute("""
    UPDATE claims SET status = ?
    WHERE claim_id = ?
    """, (status, claim_id))

    conn.commit()
    conn.close()


# =========================
# CUSTOMER FEEDBACK
# =========================
def save_customer_feedback(claim_id, message, additional_info=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO customer_feedback (claim_id, message, additional_info)
    VALUES (?, ?, ?)
    """, (
        claim_id,
        message,
        additional_info
    ))

    conn.commit()
    conn.close()


# =========================
# AUDIT LOGGING
# =========================
def log_audit_event(claim_id, actor, action, details=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_id TEXT,
        actor TEXT,
        action TEXT,
        details TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    INSERT INTO audit_logs (claim_id, actor, action, details)
    VALUES (?, ?, ?, ?)
    """, (claim_id, actor, action, details))

    conn.commit()
    conn.close()


# =========================
# GET AUDIT LOGS
# =========================
def get_audit_logs(claim_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT actor, action, details, timestamp
    FROM audit_logs
    WHERE claim_id = ?
    ORDER BY timestamp DESC
    """, (claim_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "actor": r[0],
            "action": r[1],
            "details": r[2],
            "timestamp": r[3]
        }
        for r in rows
    ]