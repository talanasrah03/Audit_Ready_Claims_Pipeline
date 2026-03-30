"""
Database management system for the claims pipeline.

Goal:
Store, retrieve, and track all claim-related data in a structured way.

What this file does:
- Creates and manages the database
- Stores claims, AI results, and human reviews
- Tracks customer feedback
- Logs all actions for auditability

Important concept:
Everything in the system is stored and traceable.

Example:
A claim can go through:
→ creation
→ AI validation
→ human review
→ customer feedback
→ audit logging

All these steps are stored in the database for transparency.
"""

import sqlite3   # Used to connect to and manage the SQLite database
import json      # Used to convert complex Python data (dict, list) into text for database storage


# Path to the SQLite database file
DB_PATH = "claims.db"


# =========================
# CONNECTION
# =========================
def get_connection():
    """
    Goal:
    Create a connection to the database.

    Logic:
    - Open the SQLite database file
    - Return a connection object
    - Other functions use this connection to run SQL queries

    Important:
    Each function opens and closes its own connection.
    This helps keep operations isolated and reduces conflicts.

    Example:
    conn = get_connection()
    → now SQL commands can be executed on claims.db
    """

    return sqlite3.connect(DB_PATH)


# =========================
# INIT DATABASE (RUN ONCE)
# =========================
def init_db():
    """
    Goal:
    Create all required database tables if they do not already exist.

    Logic:
    - Define the structure of each table
    - Use CREATE TABLE IF NOT EXISTS
      so the script can be run multiple times safely

    Why important:
    Without these tables:
    → the system would have nowhere to store claims, reviews, or logs

    Example:
    First run:
    → tables are created

    Later runs:
    → nothing breaks, because existing tables are kept
    """

    conn = get_connection()
    cursor = conn.cursor()

    # =========================
    # CLAIMS TABLE
    # =========================
    """
    Goal:
    Store the main claim record.

    Fields:
    - claim_id → unique identifier for the claim
    - status → current workflow state
    - risk_level → current assigned risk level

    Important:
    PRIMARY KEY means:
    → claim_id must be unique
    → no two rows can have the same claim_id

    Example:
    claim_id = "CLM-1001"
    status = "processed"
    risk_level = "HIGH"
    """

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        claim_id TEXT PRIMARY KEY,
        status TEXT,
        risk_level TEXT
    )
    """)

    # =========================
    # AI RESULTS TABLE
    # =========================
    """
    Goal:
    Store outputs produced by the AI system.

    Fields:
    - extracted_data → structured claim output
    - consistency_score → confidence/stability indicator
    - validation_issues → list of issues found
    - explanation → readable explanation of result

    Important:
    Some fields are stored as TEXT,
    but the content may actually represent JSON.

    Example:
    extracted_data = {"amount": 5000}
    → stored as the string '{"amount": 5000}'
    """

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_results (
        claim_id TEXT,
        extracted_data TEXT,
        consistency_score REAL,
        validation_issues TEXT,
        explanation TEXT
    )
    """)

    # =========================
    # HUMAN REVIEWS TABLE
    # =========================
    """
    Goal:
    Store actions taken by human reviewers.

    Fields:
    - id → unique numeric row ID
    - claim_id → related claim
    - action → reviewer decision
    - corrected_fields → fields manually changed
    - reviewer_note → optional note
    - timestamp → when this review happened

    Important:
    AUTOINCREMENT means:
    → the database automatically generates row numbers (1, 2, 3, ...)

    DEFAULT CURRENT_TIMESTAMP means:
    → the database automatically stores the current time when a row is created

    Example:
    action = "approve"
    corrected_fields = {"amount": 3000}
    """

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

    # =========================
    # CUSTOMER FEEDBACK TABLE
    # =========================
    """
    Goal:
    Store messages or feedback sent by the customer.

    Example:
    message = "DISPUTE"
    additional_info = "The amount is incorrect"
    """

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_id TEXT,
        message TEXT,
        additional_info TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # =========================
    # AUDIT LOGS TABLE
    # =========================
    """
    Goal:
    Track important actions performed in the system.

    Why important:
    This creates an audit trail,
    which makes the system explainable and traceable.

    Fields:
    - actor → who performed the action
    - action → what happened
    - details → extra explanation
    - timestamp → when it happened

    Example:
    actor = "AI"
    action = "VALIDATION"
    details = "Amount too high"
    """

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
# INSERT CLAIM
# =========================
def insert_claim(claim_id, status="pending", risk_level="LOW"):
    """
    Goal:
    Insert a new claim into the database,
    or replace the old one if it already exists.

    Logic:
    INSERT OR REPLACE means:
    - if claim_id does not exist → insert new row
    - if claim_id already exists → delete old row and insert new row

    Why useful:
    This makes updates simple,
    because the system can save the latest version of the claim record.

    Example:
    claim_id = "123"
    status = "processed"
    risk_level = "HIGH"
    """

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
    """
    Goal:
    Store AI processing results in the database.

    Logic:
    - Convert complex Python objects into JSON strings
    - Save them into the ai_results table

    Important:
    json.dumps(...)
    converts Python data into text.

    Why needed:
    SQLite cannot directly store Python dictionaries or lists.

    Example:
    {"amount": 5000} → '{"amount": 5000}'
    ["Missing date"] → '["Missing date"]'
    """

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
# SAVE HUMAN REVIEW
# =========================
def save_human_review(claim_id, action, corrected_fields=None, reviewer_note=None):
    """
    Goal:
    Record a human decision and update the main claim status.

    Logic:
    1. Save the review entry into the human_reviews table
    2. Convert corrected_fields to JSON if needed
    3. Update the status in the main claims table

    Mapping:
    approve      → approved
    reject       → rejected
    request_info → pending_info
    anything else → under_review

    Example:
    action = "approve"
    → status becomes "approved"
    """

    conn = get_connection()
    cursor = conn.cursor()

    # Safety step: ensure the table exists before inserting
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

    # =========================
    # UPDATE STATUS
    # =========================
    """
    Goal:
    Reflect the reviewer decision in the main claims table.

    Why important:
    The review should not stay only in the review history.
    The main claim status should also show the current workflow state.
    """

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
    """
    Goal:
    Store customer responses in the database.

    Logic:
    - Save the type of message
    - Save any optional extra information

    Example:
    message = "DISPUTE"
    additional_info = "Amount is incorrect"
    """

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
    """
    Goal:
    Record important actions in the audit log.

    Why important:
    This creates a history of what happened,
    who did it, and when it happened.

    Example:
    actor = "reviewer"
    action = "approve"
    details = "Claim approved"
    """

    conn = get_connection()
    cursor = conn.cursor()

    # Safety step: ensure the audit table exists
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
    """
    Goal:
    Retrieve the full audit history for one claim.

    Logic:
    - Select all rows related to the claim_id
    - Sort them by newest first
    - Convert raw database rows into dictionaries for easier use

    fetchall():
    → returns all matching rows as a list of tuples

    Example row:
    ("AI", "VALIDATION", "Amount too high", "2026-03-30 10:00:00")

    This function converts rows into a cleaner format like:
    {
        "actor": "AI",
        "action": "VALIDATION",
        "details": "Amount too high",
        "timestamp": "2026-03-30 10:00:00"
    }
    """

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

    """
    List comprehension:
    This is a short way to create a new list.

    Here it means:
    - take each database row
    - build a dictionary from it
    - return the full list of dictionaries
    """
    return [
        {
            "actor": r[0],
            "action": r[1],
            "details": r[2],
            "timestamp": r[3]
        }
        for r in rows
    ]