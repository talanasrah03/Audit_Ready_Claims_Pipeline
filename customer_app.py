"""
Customer Portal (Streamlit UI)

Goal:
Provide a live customer-facing portal for:
- viewing claim details
- checking current claim status
- seeing reviewer-side updates
- sending responses to the insurance company
- tracking previously sent customer messages

This version is live-connected with the internal reviewer dashboard through SQLite.

Customer view rule:
- show the current live effective claim
- do not show before/after change panels
- do not list changed field names
"""

import json
import sqlite3

import pandas as pd
import streamlit as st

from src.database.db import save_customer_feedback


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Customer Portal", layout="centered")

st.title("📄 Customer Claim Portal")
st.caption("Access your claim, view live status, and communicate with the insurance company")


# =========================
# HELPERS
# =========================
def load_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Missing file: {path}")
        st.stop()
    except json.JSONDecodeError:
        st.error(f"Invalid JSON format in file: {path}")
        st.stop()


def get_connection():
    conn = sqlite3.connect("claims.db")
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables_exist(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS human_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id TEXT,
            action TEXT,
            corrected_fields TEXT,
            reviewer_note TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS customer_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id TEXT,
            message TEXT,
            additional_info TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
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


def resolve_claim(user_input, claims):
    """
    Let the customer search by either doc_id or claim_id.
    """
    cleaned = (user_input or "").strip()

    for claim in claims:
        doc_id = str(claim.get("doc_id", "")).strip()
        claim_id = str(claim.get("claim_id", "")).strip()

        if cleaned == doc_id or cleaned == claim_id:
            return claim

    return None


def get_latest_human_review(conn, claim_id):
    row = conn.execute("""
        SELECT id, action, corrected_fields, reviewer_note, timestamp
        FROM human_reviews
        WHERE claim_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (claim_id,)).fetchone()

    return dict(row) if row else None


def get_human_review_history(conn, claim_id):
    rows = conn.execute("""
        SELECT id, action, corrected_fields, reviewer_note, timestamp
        FROM human_reviews
        WHERE claim_id = ?
        ORDER BY id DESC
    """, (claim_id,)).fetchall()

    return [dict(r) for r in rows]


def get_customer_feedback_history(conn, claim_id):
    rows = conn.execute("""
        SELECT message, additional_info, timestamp
        FROM customer_feedback
        WHERE claim_id = ?
        ORDER BY id DESC
    """, (claim_id,)).fetchall()

    return [dict(r) for r in rows]


def map_customer_status(latest_review):
    if not latest_review:
        return "UNDER_REVIEW"

    action = latest_review.get("action")

    if action == "approve":
        return "APPROVED"
    if action == "reject":
        return "REJECTED"
    if action == "request_info":
        return "NEED_INFO"
    if action == "correct":
        return "UPDATED_AFTER_REVIEW"

    return "UNDER_REVIEW"


def display_customer_status(status):
    if status == "APPROVED":
        st.success("✅ Your claim has been approved.")
    elif status == "REJECTED":
        st.error("❌ Your claim has been rejected.")
    elif status == "NEED_INFO":
        st.warning("📩 Additional information is required from you.")
    elif status == "UPDATED_AFTER_REVIEW":
        st.info("✏️ Your claim was updated during review and is still being processed.")
    else:
        st.warning("⏳ Your claim is under review.")


def parse_corrected_fields(value):
    if not value:
        return {}

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    return {}


def apply_single_review(claim_state, review):
    """
    Apply one correction on top of the current claim state.
    """
    updated = claim_state.copy()

    if review and review.get("action") == "correct":
        corrected_fields = parse_corrected_fields(review.get("corrected_fields"))
        if corrected_fields:
            updated.update(corrected_fields)

    return updated


def build_effective_claim(original_claim, review_history):
    """
    Build the live customer-visible claim by replaying all corrections
    from oldest to newest.
    """
    effective_claim = original_claim.copy()

    chronological_reviews = list(reversed(review_history))
    for review in chronological_reviews:
        effective_claim = apply_single_review(effective_claim, review)

    return effective_claim


# =========================
# LOAD DATA
# =========================
claims = load_json_file("data/processed/cleaned_claims.json")


# =========================
# INPUT
# =========================
claim_id_input = st.text_input("🔎 Enter your Claim ID", key="claim_input")
st.caption("You can use either doc_id or claim_id")

col_search, col_refresh = st.columns(2)
with col_search:
    if st.button("Search Claim"):
        st.session_state["searched_claim"] = claim_id_input.strip()

with col_refresh:
    if st.button("🔄 Refresh Live Data"):
        st.rerun()


# =========================
# DISPLAY CLAIM
# =========================
if "searched_claim" in st.session_state:
    searched_claim = st.session_state["searched_claim"]

    claim = resolve_claim(searched_claim, claims)

    if not claim:
        st.error("❌ Claim not found. Please check your Claim ID.")

    else:
        claim_id = claim.get("claim_id") or claim.get("doc_id")

        conn = get_connection()
        ensure_tables_exist(conn)

        latest_review = get_latest_human_review(conn, claim_id)
        review_history = get_human_review_history(conn, claim_id)
        customer_history = get_customer_feedback_history(conn, claim_id)

        status = map_customer_status(latest_review)
        effective_claim = build_effective_claim(claim, review_history)

        st.markdown("---")
        st.subheader("📄 Claim Details")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Claim ID:** {effective_claim.get('claim_id') or claim_id}")
            st.write(f"**Customer Name:** {effective_claim.get('customer_name', 'Unknown')}")
            st.write(f"**Date:** {effective_claim.get('claim_date', 'Unknown')}")

        with col2:
            st.write(f"**Type:** {effective_claim.get('claim_type', 'Unknown')}")
            st.write(f"**Amount:** {effective_claim.get('amount', 'Unknown')}")
            st.write(f"**Domain:** {effective_claim.get('domain', 'vehicle')}")

        st.subheader("📊 Live Claim Status")
        display_customer_status(status)

        if latest_review:
            st.markdown("### 🧑‍💼 Latest Reviewer Update")
            st.write(f"**Latest Action:** {latest_review.get('action')}")
            st.write(f"**Updated At:** {latest_review.get('timestamp')}")

            reviewer_note = latest_review.get("reviewer_note")
            if reviewer_note:
                st.write(f"**Reviewer Note:** {reviewer_note}")

        st.markdown("### 🕘 Reviewer History")
        if review_history:
            review_df = pd.DataFrame(review_history)
            st.dataframe(review_df, use_container_width=True)
        else:
            st.info("No reviewer updates available yet.")

        st.subheader("💬 Your Response")

        colA, colB, colC = st.columns(3)

        if colA.button("✅ Confirm"):
            save_customer_feedback(
                claim_id=claim_id,
                message="CONFIRM",
                additional_info=""
            )
            st.success("✅ Your confirmation has been sent to the insurance team.")
            st.rerun()

        if colB.button("⚠️ Dispute"):
            save_customer_feedback(
                claim_id=claim_id,
                message="DISPUTE",
                additional_info=""
            )
            st.warning("⚠️ Your dispute has been sent to the insurance team.")
            st.rerun()

        if colC.button("📩 Provide Info"):
            st.session_state["show_message"] = True

        if st.session_state.get("show_message"):
            st.markdown("### 📩 Send Additional Information")

            user_message = st.text_area(
                "Write your message to the insurance team",
                key="customer_message_box"
            )

            if st.button("📤 Send Message"):
                save_customer_feedback(
                    claim_id=claim_id,
                    message="PROVIDE_INFO",
                    additional_info=user_message
                )

                st.success("📨 Your message has been sent to the insurance team.")
                st.rerun()

        st.markdown("### 🗂️ Your Feedback History")
        if customer_history:
            customer_df = pd.DataFrame(customer_history)
            st.dataframe(customer_df, use_container_width=True)
        else:
            st.info("You have not sent any responses yet.")

        conn.close()