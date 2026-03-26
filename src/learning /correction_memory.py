"""
This module builds a simple memory of past human corrections.

Goal:
Learn patterns from human corrections and adapt system behavior.

This is NOT machine learning.
This is rule-based learning from human feedback.
"""

import sqlite3
import json

DB_PATH = "claims.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def load_corrections():
    """
    Load all past human corrections from DB.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT corrected_fields
    FROM human_reviews
    WHERE action = 'correct'
    """)

    results = cursor.fetchall()
    conn.close()

    corrections = []

    for (corrected_fields,) in results:
        if corrected_fields:
            corrections.append(json.loads(corrected_fields))

    return corrections


def build_patterns(corrections):
    """
    Analyze corrections and extract patterns.
    """
    patterns = {
        "amount_corrections": 0,
        "type_corrections": 0
    }

    for c in corrections:
        if "amount" in c:
            patterns["amount_corrections"] += 1

        if "claim_type" in c:
            patterns["type_corrections"] += 1

    return patterns


def get_pattern_summary():
    """
    Main function to return learned patterns.
    """
    corrections = load_corrections()
    return build_patterns(corrections)