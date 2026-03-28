import streamlit as st
import json
from src.database.db import save_customer_feedback

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Customer Portal", layout="centered")

st.title("📄 Customer Claim Portal")
st.caption("Access your claim and communicate with the insurance company")


# =========================
# LOAD DATA
# =========================
with open("data/processed/cleaned_claims.json") as f:
    claims = json.load(f)

with open("data/processed/human_review_queue.json") as f:
    reviews = json.load(f)


# =========================
# LOOKUPS
# =========================
claim_dict = {c["doc_id"]: c for c in claims}
review_dict = {r["doc_id"]: r for r in reviews}


# =========================
# INPUT
# =========================
claim_id_input = st.text_input("🔎 Enter your Claim ID", key="claim_input")
st.caption("Example: claim_1")


# =========================
# SEARCH (STATE FIX)
# =========================
if st.button("Search Claim"):
    st.session_state["searched_claim"] = claim_id_input


# =========================
# DISPLAY CLAIM
# =========================
if "searched_claim" in st.session_state:

    claim_id = st.session_state["searched_claim"]

    claim = claim_dict.get(claim_id)
    review = review_dict.get(claim_id)

    if not claim:
        st.error("❌ Claim not found. Please check your Claim ID.")

    else:
        # =========================
        # CLAIM DETAILS
        # =========================
        st.markdown("---")
        st.subheader("📄 Claim Details")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Customer Name:** {claim.get('customer_name')}")
            st.write(f"**Date:** {claim.get('claim_date')}")

        with col2:
            st.write(f"**Type:** {claim.get('claim_type')}")
            st.write(f"**Amount:** {claim.get('amount')}")

        # =========================
        # STATUS
        # =========================
        st.subheader("📊 Claim Status")

        if review:
            status = review.get("status", "UNDER_REVIEW")

            if status == "APPROVED":
                st.success("✅ Your claim has been approved.")

            elif status == "REJECTED":
                st.error("❌ Your claim has been rejected.")

            elif status == "NEED_INFO":
                st.warning("📩 Additional information is required.")

            else:
                st.warning("⏳ Your claim is under review.")

        else:
            st.info("Processing information not available yet.")

        # =========================
        # CUSTOMER ACTIONS
        # =========================
        st.subheader("💬 Your Response")

        colA, colB, colC = st.columns(3)

        # -------------------------
        # ✅ CONFIRM
        # -------------------------
        if colA.button("✅ Confirm"):
            save_customer_feedback(
                claim_id=claim_id,
                message="CONFIRM",
                additional_info=""
            )

            st.success("✅ Your confirmation has been sent to the insurance team.")

        # -------------------------
        # ⚠️ DISPUTE
        # -------------------------
        if colB.button("⚠️ Dispute"):
            save_customer_feedback(
                claim_id=claim_id,
                message="DISPUTE",
                additional_info=""
            )

            st.warning("⚠️ Your dispute has been sent to the insurance team.")

        # -------------------------
        # 📩 REQUEST INFO (WITH INPUT)
        # -------------------------
        if colC.button("📩 Provide Info"):
            st.session_state["show_message"] = True

        # -------------------------
        # MESSAGE FORM (ONLY HERE)
        # -------------------------
        if st.session_state.get("show_message"):
            st.markdown("### 📩 Send Additional Information")

            user_message = st.text_area(
                "Write your message to the insurance team"
            )

            if st.button("📤 Send Message"):
                save_customer_feedback(
                    claim_id=claim_id,
                    message="PROVIDE_INFO",
                    additional_info=user_message
                )

                st.success("📨 Your message has been sent to the insurance team.")