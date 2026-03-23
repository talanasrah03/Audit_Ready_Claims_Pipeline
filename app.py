import streamlit as st
import json

st.set_page_config(page_title="AI Claims Pipeline", layout="wide")

st.title("🚨 AI Claims Processing Dashboard")

# =========================
# LOAD DATA
# =========================
with open("data/processed/cleaned_claims.json") as f:
    claims = json.load(f)

with open("data/processed/risk_scores.json") as f:
    risks = json.load(f)

# merge data
risk_dict = {r["doc_id"]: r for r in risks}

# =========================
# SELECT CLAIM
# =========================
claim_ids = [c["doc_id"] for c in claims]
selected_id = st.selectbox("Select a claim", claim_ids)

claim = next(c for c in claims if c["doc_id"] == selected_id)
risk = risk_dict.get(selected_id, {})

# =========================
# DISPLAY CLAIM
# =========================
st.subheader("📄 Extracted Claim Data")

st.json(claim)

# =========================
# DISPLAY RISK
# =========================
st.subheader("🚨 Risk Analysis")

st.write(f"**Risk Level:** {risk.get('risk_level')}")
st.write(f"**Risk Score:** {risk.get('risk_score')}")

st.write("**Reasons:**")
for reason in risk.get("reasons", []):
    st.write(f"- {reason}")

# =========================
# SUMMARY
# =========================
st.subheader("📊 Summary")

high = sum(1 for r in risks if r["risk_level"] == "HIGH")
low = sum(1 for r in risks if r["risk_level"] == "LOW")

st.write(f"🔴 High Risk Claims: {high}")
st.write(f"🟢 Low Risk Claims: {low}")