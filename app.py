"""
Streamlit Dashboard for AI Claims Processing Pipeline

This interface allows:
- Viewing claims
- Inspecting risk scores
- Reviewing issues
- Performing human actions (approve / reject / correct / request info)
"""

import json
import streamlit as st
from src.database.db import save_human_review
from src.config.config import CONFIGS


# =========================
# PAGE CONFIGURATION
# =========================
st.set_page_config(page_title="AI Claims Pipeline", layout="wide")
st.title("AI Claims Processing Dashboard")


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

claim_id = claim.get("claim_id") or claim.get("doc_id")


# =========================
# DOMAIN HANDLING (FIXED 💣)
# =========================
domain = claim.get("domain", "vehicle")

domain_config = CONFIGS.get(domain)

if not domain_config:
    domain_config = CONFIGS["vehicle"]
    st.warning("⚠️ Domain undefined in the system — fallback to 'vehicle'")


claim_type_options = domain_config.get("claim_types", [])


# =========================
# DISPLAY CLAIM DATA
# =========================
st.subheader("Extracted Claim Data")
st.json(claim)



# =========================
# AI RISK ANALYSIS 🧠
# =========================
# =========================
# AI RISK ANALYSIS 🧠
# =========================
st.subheader("🧠 AI Risk Analysis")

st.write(f"Risk Level: {risk.get('risk_level')}")
st.write(f"Risk Score: {risk.get('risk_score')}")

st.write("AI Reasons:")

reasons = risk.get("reasons", [])

if reasons:
    for reason in reasons:
        st.info(reason)   # 👈 أزرق (AI)
else:
    st.success("No AI issues detected")
# =========================
# AI EXPLANATION 💣
# =========================
st.subheader("🧠 AI Explanation")

if reasons:
    if "Claim type mismatch" in reasons:
        st.info(
            "The AI model detected a mismatch in the claim type compared to expected patterns. "
            "This may indicate a classification error and requires review."
        )

    elif "Large amount mismatch" in reasons:
        st.info(
            "The predicted claim amount significantly differs from expected values. "
            "This could indicate extraction inaccuracies."
        )

    else:
        st.info(
            "The AI system detected minor inconsistencies in the claim data that may require attention."
        )

else:
    st.success(
        "The AI model processed this claim successfully without detecting inconsistencies."
    )

# =========================
# BUSINESS VALIDATION ⚖️
# =========================
st.subheader("⚖️ Business Validation")

issues = review.get("issues") if review else []

if issues:
    for issue in issues:
        st.warning(issue)   # 👈 أصفر (business rules)
else:
    st.success("No validation issues")
# =========================
# BUSINESS EXPLANATION 💣
# =========================
st.subheader("⚖️ Business Explanation")

if issues:
    if "Amount too high" in issues:
        st.warning(
            "The claim amount exceeds the expected range based on business rules. "
            "This may require additional verification."
        )

    elif "Amount too low" in issues:
        st.warning(
            "The claim amount is lower than expected and may be incomplete or incorrect."
        )

    else:
        st.warning(
            "The claim violates one or more business validation rules and should be reviewed."
        )

else:
    st.success(
        "The claim complies with all business rules and does not require further validation."
    )
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

    action = st.selectbox(
        "Choose Action",
        ["APPROVE", "REJECT", "CORRECT", "REQUEST_INFO"]
    )

    # =========================
    # APPROVE
    # =========================
    if action == "APPROVE":
        if st.button("Confirm Decision"):
            save_human_review(claim_id, "approve")
            st.success(f"Claim {selected_id} has been APPROVED")

    # =========================
    # REJECT
    # =========================
    elif action == "REJECT":
        if st.button("Confirm Decision"):
            save_human_review(claim_id, "reject")
            st.error(f"Claim {selected_id} has been REJECTED due to risk")

    # =========================
    # CORRECT
    # =========================
    elif action == "CORRECT":
        st.warning("Edit claim fields below:")

        new_name = st.text_input("Customer Name", claim.get("customer_name"))
        new_date = st.text_input("Claim Date", claim.get("claim_date"))

        current_type = claim.get("claim_type")
        index = (
            claim_type_options.index(current_type)
            if current_type in claim_type_options else 0
        )

        new_type = st.selectbox("Claim Type", claim_type_options, index=index)

        new_amount = st.number_input(
            "Amount",
            value=int(claim.get("amount") or 0)
        )

        if st.button("Save Correction"):
            corrected_data = {
                "customer_name": new_name,
                "claim_date": new_date,
                "claim_type": new_type,
                "amount": new_amount,
                "domain": domain
            }

            save_human_review(
                claim_id=claim_id,
                action="correct",
                corrected_fields=corrected_data,
                reviewer_note="Manual correction applied by reviewer"
            )

            st.success("Claim updated successfully")
            st.json(corrected_data)

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
            save_human_review(
                claim_id=claim_id,
                action="request_info",
                reviewer_note=f"Request sent to {email}"
            )

            st.success(f"Email sent to {email} (simulated)")
            st.info("Message preview:")
            st.write(message)


# =========================
# SUMMARY SECTION
# =========================
st.subheader("Summary")

high = sum(1 for r in risks if r["risk_level"] == "HIGH")
low = sum(1 for r in risks if r["risk_level"] == "LOW")

st.write(f"High Risk Claims: {high}")
st.write(f"Low Risk Claims: {low}")