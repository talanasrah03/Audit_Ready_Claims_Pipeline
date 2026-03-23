import streamlit as st
import json

st.set_page_config(page_title="Customer Portal", layout="centered")

st.title("👤 Insurance Customer Portal")

# =========================
# LOAD DATA
# =========================
with open("data/processed/cleaned_claims.json") as f:
    claims = json.load(f)

with open("data/processed/human_review_queue.json") as f:
    reviews = json.load(f)

review_dict = {r["doc_id"]: r for r in reviews}
claim_dict = {c["doc_id"]: c for c in claims}

# =========================
# INPUT CLAIM ID
# =========================
claim_id_input = st.text_input("Enter your Claim ID (from email)")
st.caption("Example: claim_1")
# =========================
# SEARCH BUTTON
# =========================
if st.button("Search Claim"):

    claim = claim_dict.get(claim_id_input)
    review = review_dict.get(claim_id_input)

    if not claim:
        st.error("❌ Claim not found. Please check your Claim ID.")
    else:
        # =========================
        # DISPLAY CLAIM
        # =========================
        st.subheader("📄 Your Claim")

        st.write(f"**Name:** {claim.get('customer_name')}")
        st.write(f"**Date:** {claim.get('claim_date')}")
        st.write(f"**Type:** {claim.get('claim_type')}")
        st.write(f"**Amount:** {claim.get('amount')}")

        # =========================
        # STATUS
        # =========================
        st.subheader("📊 Claim Status")

        if review:
            st.warning("⏳ Your claim is under review")
        else:
            st.success("✅ Your claim has been processed")

        # =========================
        # CUSTOMER ACTIONS
        # =========================
        st.subheader("💬 Your Actions")

        action = st.selectbox(
            "Choose Action",
            ["CONFIRM", "DISPUTE", "PROVIDE_INFO"]
        )

        message = st.text_area("Your Message")

        if st.button("Submit"):
            st.success("✅ Your response has been submitted")

            st.info("📨 Summary:")
            st.write({
                "claim_id": claim_id_input,
                "action": action,
                "message": message
            })