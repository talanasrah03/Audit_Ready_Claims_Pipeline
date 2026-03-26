import streamlit as st
import json
from src.database.db import save_customer_feedback

# =========================
# PAGE CONFIGURATION
# =========================
st.set_page_config(page_title="Customer Portal", layout="centered")

st.title("Customer Claim Portal")
st.caption("Access your claim details and respond to the insurance company")


# =========================
# LOAD DATA
# =========================
with open("data/processed/cleaned_claims.json") as f:
    claims = json.load(f)

with open("data/processed/human_review_queue.json") as f:
    reviews = json.load(f)


# =========================
# LOOKUP TABLES
# =========================
claim_dict = {c["doc_id"]: c for c in claims}
review_dict = {r["doc_id"]: r for r in reviews}


# =========================
# USER INPUT
# =========================
claim_id_input = st.text_input("Enter your Claim ID")
st.caption("Example: claim_1")


# =========================
# SEARCH BUTTON
# =========================
if st.button("Search Claim"):

    claim = claim_dict.get(claim_id_input)
    review = review_dict.get(claim_id_input)

    # =========================
    # ERROR CASE
    # =========================
    if not claim:
        st.error("❌ Claim not found. Please check your Claim ID.")

    else:
        # =========================
        # DISPLAY CLAIM
        # =========================
        st.subheader("Claim Details")

        st.write(f"**Customer Name:** {claim.get('customer_name')}")
        st.write(f"**Date:** {claim.get('claim_date')}")
        st.write(f"**Type:** {claim.get('claim_type')}")
        st.write(f"**Amount:** {claim.get('amount')}")

        # =========================
        # STATUS
        # =========================
        st.subheader("Status")

        if review:
            st.warning("⏳ Your claim is currently under review.")
        else:
            st.success("✅ Your claim has been processed.")

        # =========================
        # CUSTOMER ACTION
        # =========================
        st.subheader("Your Response")

        action = st.selectbox(
            "Choose an action",
            ["CONFIRM", "DISPUTE", "PROVIDE_INFO"]
        )

        message = st.text_area("Add a message (optional)")

        # =========================
        # SUBMIT
        # =========================
        if st.button("Submit Response"):

            # 💣 SAVE TO DATABASE (REAL ACTION)
            save_customer_feedback(
                claim_id=claim_id_input,
                message={
                    "action": action,
                    "message": message
                }
            )

            st.success("✅ Your response has been submitted successfully.")

            st.info("📩 Submitted Information:")
            st.json({
                "claim_id": claim_id_input,
                "action": action,
                "message": message
            })