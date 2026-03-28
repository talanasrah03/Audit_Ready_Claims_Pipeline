"""
Streamlit Dashboard for AI Claims Processing Pipeline
"""

import json
import random
import streamlit as st
import sqlite3
import pandas as pd

from src.database.db import save_human_review
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
claim = next(c for c in claims if c["doc_id"] == selected_id)
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
# 📊 SYSTEM OVERVIEW
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
# 📄 CLAIM + 🤖 ACTION
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
# 🖥️ SYSTEM TABS
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
# 🧾 AUDIT TRAIL TAB (NEW 🔥)
# =========================
with tab5:
    colA, colB = st.columns([1, 2])

    with colA:
        st.subheader("Description")
        st.info("""
Tracks all actions and decisions in the system.

👉 Ensures full transparency and traceability for audits.
""")

    with colB:
        st.subheader("Result")

        conn = sqlite3.connect("claims.db")

        try:
            df = pd.read_sql_query(
                f"""
                SELECT claim_id, actor, action, details, timestamp
                FROM audit_logs
                WHERE claim_id = '{claim_id}'
                ORDER BY timestamp DESC
                """,
                conn
            )

            if not df.empty:
                st.dataframe(df)
            else:
                st.info("No audit history yet")

        except Exception as e:
            st.error("Audit table not found. Make sure it is created.")

        finally:
            conn.close()