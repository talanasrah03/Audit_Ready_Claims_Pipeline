"""
Streamlit Dashboard for AI Claims Processing Pipeline
"""

import json
import random
import streamlit as st
import sqlite3
import pandas as pd

from src.database.db import save_human_review, log_audit_event
from src.config.config import CONFIGS
from src.learning.consistency import compute_consistency


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="AI Claims Pipeline", layout="wide")


# =========================
# HELPERS
# =========================
def safe_int(value, default=0):
    try:
        return int(float(value))
    except:
        return default


def simulate_ai_outputs(base_claim):
    outputs = []
    base_amount = safe_int(base_claim.get("amount"), 0)

    for _ in range(3):
        noisy = base_claim.copy()

        if random.random() < 0.3:
            noisy["amount"] = base_amount + random.randint(-50, 50)
        else:
            noisy["amount"] = base_amount

        outputs.append(noisy)

    return outputs


# =========================
# LOAD DATA
# =========================
with open("data/processed/cleaned_claims.json") as f:
    claims = json.load(f)

with open("data/processed/risk_scores.json") as f:
    risks = json.load(f)

with open("data/processed/human_review_queue.json") as f:
    review_data = json.load(f)


# =========================
# PREPARE DATA
# =========================
claim_ids = [c["doc_id"] for c in claims]
risk_dict = {r["doc_id"]: r for r in risks}
review_dict = {r["doc_id"]: r for r in review_data}


# =========================
# SIDEBAR
# =========================
st.sidebar.title("📊 Navigation")
selected_id = st.sidebar.selectbox("Select Claim", claim_ids)


# =========================
# RESET STATE
# =========================
if st.session_state.get("last") != selected_id:
    st.session_state["show_correct"] = False
    st.session_state["show_request"] = False
    st.session_state["last"] = selected_id


# =========================
# TITLE
# =========================
st.title("🚨 AI Claims Processing Dashboard")
st.caption("Audit-ready AI system with human-in-the-loop validation")


# =========================
# SELECT CLAIM
# =========================
try:
    claim = next(c for c in claims if c["doc_id"] == selected_id)
except StopIteration:
    st.error("Claim not found")
    st.stop()

risk = risk_dict.get(selected_id, {})
review = review_dict.get(selected_id, {})
claim_id = claim.get("claim_id") or claim.get("doc_id")


# =========================
# CONSISTENCY
# =========================
ai_outputs = simulate_ai_outputs(claim)
consistency_score, stable_output = compute_consistency(ai_outputs)


# =========================
# DOMAIN
# =========================
domain = claim.get("domain", "vehicle")
domain_config = CONFIGS.get(domain, CONFIGS["vehicle"])
claim_type_options = domain_config.get("claim_types", [])


# =========================
# SYSTEM OVERVIEW
# =========================
st.subheader("📊 System Overview")

high = sum(1 for r in risks if r.get("risk_level") == "HIGH")
low = sum(1 for r in risks if r.get("risk_level") == "LOW")
total = len(claims)

col1, col2, col3 = st.columns(3)
col1.metric("Total Claims", total)
col2.metric("High Risk", high)
col3.metric("Low Risk", low)


# =========================
# CLAIM + ACTION
# =========================
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📄 Claim Data")
    st.json(claim)

with col2:
    st.subheader("🤖 Recommended Action")

    recommended = review.get("recommended_action", "MANUAL_REVIEW")

    if recommended == "APPROVE":
        st.success("✅ APPROVE")
    elif recommended == "REJECT":
        st.error("❌ REJECT")
    else:
        st.warning("⚠️ MANUAL REVIEW")


# =========================
# SYSTEM TABS
# =========================
st.markdown("---")
st.header("🖥️ System Components")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧠 AI Risk",
    "🔁 AI Stability",
    "⚖️ Rules & Validation",
    "👤 Human Review",
    "🧾 Audit Trail"
])


# =========================
# AI RISK
# =========================
with tab1:
    st.subheader("AI Risk")

    st.write(f"Risk Level: {risk.get('risk_level')}")
    st.write(f"Risk Score: {risk.get('risk_score')}")

    reasons = risk.get("reasons", [])
    if reasons:
        for r in reasons:
            st.warning(r)
    else:
        st.success("No issues detected")


# =========================
# AI STABILITY
# =========================
with tab2:
    st.subheader("AI Stability")

    percent = int(consistency_score * 100)
    st.metric("Consistency Score", f"{percent}%")

    if percent >= 80:
        st.success("Stable: AI outputs are consistent")
    elif percent >= 50:
        st.warning("Moderate: Some variation detected")
    else:
        st.error("Unstable: AI outputs are inconsistent")

    colA, colB = st.columns(2)

    with colA:
        st.write("Original")
        st.json(claim)

    with colB:
        st.write("Stable Output")
        st.json(stable_output)


# =========================
# VALIDATION
# =========================
with tab3:
    st.subheader("Business Validation")

    issues = review.get("issues", [])

    if issues:
        for issue in issues:
            st.warning(issue)
    else:
        st.success("All rules satisfied")


# =========================
# HUMAN REVIEW (🔥 FIXED WITH AUDIT)
# =========================
with tab4:
    st.subheader("Human Review")

    colA, colB, colC, colD = st.columns(4)

    # APPROVE
    if colA.button("✅ Approve", key="approve_btn"):
        save_human_review(claim_id, "approve")
        log_audit_event(claim_id, "reviewer", "approve", "Claim approved")
        st.success("Approved")

    # REJECT
    if colB.button("❌ Reject", key="reject_btn"):
        save_human_review(claim_id, "reject")
        log_audit_event(claim_id, "reviewer", "reject", "Claim rejected")
        st.error("Rejected")

    # CORRECT
    if colC.button("✏️ Correct", key="correct_btn"):
        st.session_state["show_correct"] = True

    if st.session_state.get("show_correct"):
        new_amount = st.number_input("New Amount", value=safe_int(claim.get("amount")))

        if st.button("💾 Save Correction"):
            save_human_review(
                claim_id,
                "correct",
                corrected_fields={"amount": new_amount},
                reviewer_note="Manual correction"
            )

            log_audit_event(
                claim_id,
                "reviewer",
                "correct",
                f"Amount changed to {new_amount}"
            )

            st.success("Correction saved")

    # REQUEST INFO
    if colD.button("📩 Request Info", key="request_btn"):
        st.session_state["show_request"] = True

    if st.session_state.get("show_request"):
        msg = st.text_area("Message")

        if st.button("📤 Send Request"):
            save_human_review(claim_id, "request_info")

            log_audit_event(
                claim_id,
                "reviewer",
                "request_info",
                msg
            )

            st.success("Request sent")


# =========================
# AUDIT TRAIL
# =========================
with tab5:
    st.subheader("Audit Trail")

    conn = sqlite3.connect("claims.db")

    # ensure table exists
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

    df = pd.read_sql_query(
        f"""
        SELECT claim_id, actor, action, details, timestamp
        FROM audit_logs
        WHERE claim_id = '{claim_id}'
        ORDER BY timestamp DESC
        """,
        conn
    )

    conn.close()

    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No audit history yet — perform an action first")