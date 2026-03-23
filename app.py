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

with open("data/processed/human_review_queue.json") as f:
    review_data = json.load(f)

# =========================
# PREPARE LOOKUPS
# =========================
risk_dict = {r["doc_id"]: r for r in risks}
review_dict = {r["doc_id"]: r for r in review_data}

# =========================
# SELECT CLAIM
# =========================
claim_ids = [c["doc_id"] for c in claims]
selected_id = st.selectbox("Select a claim", claim_ids)

claim = next(c for c in claims if c["doc_id"] == selected_id)
risk = risk_dict.get(selected_id, {})
review = review_dict.get(selected_id)

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
# HUMAN REVIEW
# =========================
st.subheader("👤 Human Review")

if review:
    st.write(f"**Status:** {review.get('status')}")
    st.write(f"**Recommended Action:** {review.get('recommended_action')}")

    st.write("**Issues:**")
    for issue in review.get("issues", []):
        st.write(f"- {issue}")

    # =========================
    # ACTION SELECTION
    # =========================
    action = st.selectbox(
        "Choose Action",
        ["APPROVE", "REJECT", "CORRECT", "REQUEST_INFO"]
    )

    # =========================
    # APPROVE / REJECT
    # =========================
    if action == "APPROVE":
        if st.button("Confirm Decision"):
             st.success(f"✅ Claim {selected_id} has been APPROVED")

    elif action == "REJECT":
         if st.button("Confirm Decision"):
             st.error(f"🚫 Claim {selected_id} has been REJECTED due to risk")
    # =========================
    # CORRECT (EDIT CLAIM)
    # =========================
    elif action == "CORRECT":
        st.warning("✏️ Edit claim fields below:")

        new_name = st.text_input("Customer Name", claim.get("customer_name"))
        new_date = st.text_input("Claim Date", claim.get("claim_date"))
        new_type = st.selectbox(
            "Claim Type",
            ["Vehicle Theft", "Single Vehicle Collision", "Multi-vehicle Collision", "Parked Car"],
            index=0 if not claim.get("claim_type") else [
                "Vehicle Theft",
                "Single Vehicle Collision",
                "Multi-vehicle Collision",
                "Parked Car"
            ].index(claim.get("claim_type"))
        )
        new_amount = st.number_input("Amount", value=int(claim.get("amount") or 0))

        if st.button("Save Correction"):
            st.success("✅ Claim updated successfully (simulated)")

            st.json({
                "customer_name": new_name,
                "claim_date": new_date,
                "claim_type": new_type,
                "amount": new_amount
            })

    # =========================
    # REQUEST INFO (EMAIL SIMULATION)
    # =========================
    elif action == "REQUEST_INFO":
        st.warning("📧 Request additional information")

        email = st.text_input("Customer Email", "customer@example.com")

        message = st.text_area(
            "Message",
            f"""
Dear Customer,

We need additional information regarding your claim ({selected_id}).

Please provide supporting documents and clarify the reported issue.

Best regards,
Insurance Team
"""
        )

        if st.button("Send Email"):
            st.success(f"📧 Email sent to {email} (simulated)")
            st.info("Message preview:")
            st.write(message)
        
# =========================
# CUSTOMER FEEDBACK
# =========================
st.subheader("💬 Customer Feedback")

feedback_type = st.selectbox(
    "Feedback Type",
    ["CONFIRM", "DISPUTE", "ADD_INFO"]
)

feedback_message = st.text_area(
    "Your Message",
    "Write your feedback here..."
)

if st.button("Submit Feedback"):
    st.success("✅ Feedback submitted successfully (simulated)")

    st.info("📨 Feedback Summary:")
    st.write({
        "claim_id": selected_id,
        "type": feedback_type,
        "message": feedback_message
    })

# =========================
# SUMMARY
# =========================
st.subheader("📊 Summary")

high = sum(1 for r in risks if r["risk_level"] == "HIGH")
low = sum(1 for r in risks if r["risk_level"] == "LOW")

st.write(f"🔴 High Risk Claims: {high}")
st.write(f"🟢 Low Risk Claims: {low}")