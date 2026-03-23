"""
This script builds an interactive dashboard using Streamlit.

Context in the project:
This is the front-end (user interface) of the AI claims processing pipeline.

The backend pipeline has already:
- Extracted claims (AI)
- Cleaned data
- Evaluated accuracy
- Assigned risk scores
- Identified claims needing human review

This dashboard allows a human user (e.g., insurance employee) to:
- Browse claims
- View AI results
- Understand risk levels
- Review issues
- Take actions (approve, reject, correct, request info)

This simulates a real internal tool used in insurance companies.

Inputs:
- cleaned_claims.json → extracted data
- risk_scores.json → risk analysis
- human_review_queue.json → claims needing human action
"""

import streamlit as st
import json


# =========================
# PAGE CONFIGURATION
# =========================
# Sets page title and layout
st.set_page_config(page_title="AI Claims Pipeline", layout="wide")

st.title("AI Claims Processing Dashboard")


# =========================
# LOAD DATA
# =========================
# Load processed data from pipeline
with open("data/processed/cleaned_claims.json") as f:
    claims = json.load(f)

with open("data/processed/risk_scores.json") as f:
    risks = json.load(f)

with open("data/processed/human_review_queue.json") as f:
    review_data = json.load(f)


# =========================
# PREPARE LOOKUPS
# =========================
# Convert lists to dictionaries for fast access
risk_dict = {r["doc_id"]: r for r in risks}
review_dict = {r["doc_id"]: r for r in review_data}


# =========================
# SELECT CLAIM
# =========================
# Dropdown selection
claim_ids = [c["doc_id"] for c in claims]
selected_id = st.selectbox("Select a claim", claim_ids)

# Get selected claim
claim = next(c for c in claims if c["doc_id"] == selected_id)

# Get associated data
risk = risk_dict.get(selected_id, {})
review = review_dict.get(selected_id)


# =========================
# DISPLAY CLAIM DATA
# =========================
st.subheader("Extracted Claim Data")
st.json(claim)


# =========================
# DISPLAY RISK ANALYSIS
# =========================
st.subheader("Risk Analysis")

st.write(f"Risk Level: {risk.get('risk_level')}")
st.write(f"Risk Score: {risk.get('risk_score')}")

st.write("Reasons:")
for reason in risk.get("reasons", []):
    st.write(f"- {reason}")


# =========================
# HUMAN REVIEW SECTION
# =========================
st.subheader("Human Review")

if review:
    st.write(f"Status: {review.get('status')}")
    st.write(f"Recommended Action: {review.get('recommended_action')}")

    st.write("Issues:")
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
    # APPROVE
    # =========================
    if action == "APPROVE":
        if st.button("Confirm Decision"):
            st.success(f"Claim {selected_id} has been APPROVED")

    # =========================
    # REJECT
    # =========================
    elif action == "REJECT":
        if st.button("Confirm Decision"):
            st.error(f"Claim {selected_id} has been REJECTED due to risk")

    # =========================
    # CORRECT
    # =========================
    elif action == "CORRECT":
        st.warning("Edit claim fields below:")

        new_name = st.text_input("Customer Name", claim.get("customer_name"))
        new_date = st.text_input("Claim Date", claim.get("claim_date"))

        options = [
            "Vehicle Theft",
            "Single Vehicle Collision",
            "Multi-vehicle Collision",
            "Parked Car"
        ]

        current_type = claim.get("claim_type")
        index = options.index(current_type) if current_type in options else 0

        new_type = st.selectbox("Claim Type", options, index=index)

        new_amount = st.number_input("Amount", value=int(claim.get("amount") or 0))

        if st.button("Save Correction"):
            st.success("Claim updated successfully (simulated)")
            st.json({
                "customer_name": new_name,
                "claim_date": new_date,
                "claim_type": new_type,
                "amount": new_amount
            })

    # =========================
    # REQUEST INFO
    # =========================
    elif action == "REQUEST_INFO":
        st.warning("Request additional information")

        email = st.text_input("Customer Email", "customer@example.com")

        message = st.text_area(
            "Message",
            f"""Dear Customer,

We need additional information regarding your claim ({selected_id}).

Please provide supporting documents and clarify the reported issue.

Best regards,
Insurance Team
"""
        )

        if st.button("Send Email"):
            st.success(f"Email sent to {email} (simulated)")
            st.info("Message preview:")
            st.write(message)


# =========================
# SUMMARY SECTION
# =========================
st.subheader("Summary")

# Count number of claims per risk level
high = sum(1 for r in risks if r["risk_level"] == "HIGH")
low = sum(1 for r in risks if r["risk_level"] == "LOW")

st.write(f"High Risk Claims: {high}")
st.write(f"Low Risk Claims: {low}")