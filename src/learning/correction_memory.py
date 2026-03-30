"""
Human correction memory system.

Goal:
Learn from past human corrections and adapt system behavior over time.

What this module does:
- Reads human corrections from the database
- Analyzes which fields are frequently corrected
- Builds simple patterns (counts) to detect instability

Important concept:
This is NOT machine learning.
This is rule-based learning from human feedback.

Why this matters:
If humans keep correcting the same field:
→ that field is considered less reliable
→ the system should treat it with more caution

Example:
If "amount" is corrected 10 times:
→ system learns that amount is unstable
→ future validations can become stricter
"""

import sqlite3   # Used to connect to the SQLite database and execute queries
import json      # Used to convert stored JSON strings into Python dictionaries


# Path to the database file
DB_PATH = "claims.db"


# =========================
# DATABASE CONNECTION
# =========================
def get_connection():
    """
    Goal:
    Create a connection to the database.

    Logic:
    - Open the SQLite database file
    - Return a connection object
    - Other functions use this connection to read stored corrections

    Important:
    Each call creates a new connection.
    This helps avoid shared-state problems and keeps operations isolated.

    Example:
    conn = get_connection()
    → now SQL queries can be executed on claims.db
    """

    return sqlite3.connect(DB_PATH)


# =========================
# LOAD CORRECTIONS
# =========================
def load_corrections():
    """
    Goal:
    Retrieve all past human corrections from the database.

    Logic:
    - Select only rows where action = "correct"
    - Read the corrected_fields column
    - Convert stored JSON strings into Python dictionaries

    Example:
    Database value:
    '{"amount": 5000}'

    After conversion:
    {"amount": 5000}

    Important:
    Some rows may contain NULL / empty corrected_fields.
    Those rows are ignored because there is nothing meaningful to learn from them.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT corrected_fields
    FROM human_reviews
    WHERE action = 'correct'
    """)

    """
    fetchall():
    → returns all matching rows as a list of tuples

    Example:
    [
        ('{"amount": 5000}',),
        ('{"claim_type": "Vehicle Theft"}',)
    ]
    """
    results = cursor.fetchall()
    conn.close()

    corrections = []

    # Process each correction row
    for (corrected_fields,) in results:

        if corrected_fields:
            """
            Convert JSON string → Python dictionary

            Example:
            '{"amount": 5000}' → {"amount": 5000}
            """

            corrections.append(json.loads(corrected_fields))

    return corrections


# =========================
# BUILD PATTERNS
# =========================
def build_patterns(corrections):
    """
    Goal:
    Analyze corrections and extract meaningful patterns.

    Logic:
    - Count how many times certain fields were corrected
    - Use those counts as simple instability signals

    Important:
    This version tracks only:
    - amount
    - claim_type

    That means:
    - if other fields are corrected, they are ignored here
    - only these tracked fields contribute to the returned summary

    Example:
    corrections = [
        {"amount": 5000},
        {"amount": 3000},
        {"claim_type": "Theft"}
    ]

    Result:
    → amount_corrections = 2
    → type_corrections = 1

    Interpretation:
    - amount is corrected more often → may be less reliable
    - claim_type is corrected less often
    """

    patterns = {
        "amount_corrections": 0,
        "type_corrections": 0
    }

    for c in corrections:

        """
        Check if "amount" exists in the correction dictionary.

        Logic:
        If the key exists:
        → a human reviewer corrected the amount field
        → increase the corresponding counter
        """
        if "amount" in c:
            patterns["amount_corrections"] += 1

        """
        Check if "claim_type" exists in the correction dictionary.

        Example:
        {"claim_type": "Vehicle Theft"}
        → this increases type_corrections by 1
        """
        if "claim_type" in c:
            patterns["type_corrections"] += 1

    return patterns


# =========================
# MAIN FUNCTION
# =========================
def get_pattern_summary():
    """
    Goal:
    Provide a summary of learned correction patterns.

    Logic:
    1. Load all corrections from the database
    2. Analyze them
    3. Return a structured summary

    Example output:
    {
        "amount_corrections": 8,
        "type_corrections": 3
    }

    Meaning:
    → amount has been corrected many times
    → claim_type has been corrected fewer times

    How the system uses this:
    - to increase validation strictness
    - to increase risk score
    - to detect unstable fields

    Important:
    If there are no past corrections yet,
    this function still works and returns:

    {
        "amount_corrections": 0,
        "type_corrections": 0
    }
    """

    corrections = load_corrections()
    return build_patterns(corrections)