import sqlite3
import json

DB_PATH = "claims.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Claims table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        claim_id TEXT PRIMARY KEY,
        status TEXT,
        risk_level TEXT
    )
    """)

    # AI Results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_results (
        claim_id TEXT,
        extracted_data TEXT,
        consistency_score REAL,
        validation_issues TEXT,
        explanation TEXT,
        FOREIGN KEY (claim_id) REFERENCES claims (claim_id)
    )
    """)

    # Human Reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS human_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_id TEXT,
        action TEXT,
        corrected_fields TEXT,
        reviewer_note TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (claim_id) REFERENCES claims (claim_id)
    )
    """)

    # Customer Feedback table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_id TEXT,
        message TEXT,
        additional_info TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (claim_id) REFERENCES claims (claim_id)
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
# AI RESULT SAVE
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
# HUMAN REVIEW SAVE 
# =========================
def save_human_review(claim_id, action, corrected_fields=None, reviewer_note=None):
    conn = get_connection()
    cursor = conn.cursor()

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
# Costumer feedback
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



def get_claim(claim_id):

    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT claim_id, status, risk_level FROM claims WHERE claim_id = ?",
        (claim_id,)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "claim_id": result[0],
            "status": result[1],
            "risk_level": result[2]
        }

    return None 

# =========================
# AUDIT TABLE
# =========================
def create_audit_table():
    

    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_id TEXT,
        action TEXT,
        timestamp TEXT,
        details TEXT
    )
    """)

    conn.commit()
    conn.close()


# =========================
# LOG ACTION
# =========================
def log_action(claim_id, action, details):
    import sqlite3
    from datetime import datetime

    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO audit_logs (claim_id, action, timestamp, details)
        VALUES (?, ?, ?, ?)
    """, (
        claim_id,
        action,
        datetime.now().isoformat(),
        str(details)
    ))

    conn.commit()
    conn.close()


# =========================
# GET AUDIT LOGS
# =========================
def get_audit_logs(claim_id):
    import sqlite3

    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT action, timestamp, details
        FROM audit_logs
        WHERE claim_id = ?
    """, (claim_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "action": r[0],
            "timestamp": r[1],
            "details": r[2]
        }
        for r in rows
    ]