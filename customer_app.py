"""
Customer Portal (Streamlit UI)

Goal:
Provide a simple interface for customers to:
- view their claim details
- check claim status
- send responses to the insurance company

This simulates the customer-side experience in a real system.

What this script does:
- loads processed claim data
- lets the customer search by claim ID
- shows claim details and current status
- allows the customer to confirm, dispute, or send more information
- stores customer feedback in the database
"""

import streamlit as st   # Used to build the interactive customer-facing web interface
import json   # Used to load claim and review data stored in JSON files

from src.database.db import save_customer_feedback   # Used to save customer responses in the database


# =========================
# PAGE CONFIG
# =========================
"""
Goal:
Configure the web page layout and browser title.

layout="centered":
→ content is displayed in a narrower centered area
→ good for simple forms and customer-facing pages

page_title:
→ text shown in the browser tab
"""

st.set_page_config(page_title="Customer Portal", layout="centered")

st.title("📄 Customer Claim Portal")
st.caption("Access your claim and communicate with the insurance company")


# =========================
# LOAD DATA
# =========================
"""
Goal:
Load the data needed by the customer portal.

claims:
→ cleaned claim data
→ contains customer-facing information such as:
   name, date, type, amount

reviews:
→ review queue or review status information
→ used to determine whether a claim is under review,
   approved, rejected, or needs more information
"""

with open("data/processed/cleaned_claims.json") as f:
    claims = json.load(f)

with open("data/processed/human_review_queue.json") as f:
    reviews = json.load(f)


# =========================
# LOOKUPS (IMPORTANT)
# =========================
"""
Goal:
Convert lists into dictionaries for faster access.

Why important:
Without this:
→ the app would need to loop through all claims every time a user searches

With this:
→ claim data can be retrieved instantly using the claim ID

Example:
claim_dict["claim_1"]
→ returns the claim directly
"""

claim_dict = {c["doc_id"]: c for c in claims}
review_dict = {r["doc_id"]: r for r in reviews}


# =========================
# INPUT FIELD
# =========================
"""
Goal:
Allow the customer to type a claim ID.

text_input:
→ creates a text box in the interface

key:
→ gives this input field a unique name in Streamlit state handling

Why key matters:
It helps Streamlit keep track of this specific input widget.
"""

claim_id_input = st.text_input("🔎 Enter your Claim ID", key="claim_input")

st.caption("Example: claim_1")


# =========================
# SEARCH BUTTON (STATE FIX)
# =========================
"""
Goal:
Trigger claim search only when the user clicks the button.

Logic:
- Read whatever the user typed
- Store it in st.session_state["searched_claim"]

What is st.session_state?
→ a small memory area used by Streamlit
→ it keeps values even when the page updates after a button click

Why important:
Without session_state:
→ the page can reset after interaction
→ the searched claim may disappear
"""

if st.button("Search Claim"):
    st.session_state["searched_claim"] = claim_id_input


# =========================
# DISPLAY CLAIM
# =========================
"""
Goal:
Display claim information only after the user has searched.

Logic:
- Check whether a searched claim is stored in session_state
- If yes, load and display the matching claim
"""

if "searched_claim" in st.session_state:

    claim_id = st.session_state["searched_claim"]

    claim = claim_dict.get(claim_id)
    review = review_dict.get(claim_id)

    # =========================
    # ERROR CASE
    # =========================
    """
    Goal:
    Handle invalid claim IDs safely.

    Logic:
    - If no matching claim exists
    - show an error message instead of crashing
    """

    if not claim:
        st.error("❌ Claim not found. Please check your Claim ID.")

    else:

        # =========================
        # CLAIM DETAILS
        # =========================
        """
        Goal:
        Show the main details of the claim.

        st.columns(2):
        → split the page into 2 vertical sections
        → makes the layout easier to read
        """

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
        """
        Goal:
        Show the current state of the claim.

        Logic:
        - If review data exists, use its status
        - Otherwise show a generic processing message

        Status meanings:
        - APPROVED  → claim accepted
        - REJECTED  → claim refused
        - NEED_INFO → more information required
        - anything else → still under review
        """

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
        """
        Goal:
        Let the customer respond to the claim.

        Available actions:
        - Confirm     → customer agrees with the claim details
        - Dispute     → customer disagrees with the claim
        - Provide Info → customer wants to send additional information
        """

        st.subheader("💬 Your Response")

        colA, colB, colC = st.columns(3)


        # -------------------------
        # CONFIRM
        # -------------------------
        """
        Goal:
        Let the customer confirm that the displayed claim is correct.

        Logic:
        - Save a feedback record in the database
        - Store message type = CONFIRM
        """

        if colA.button("✅ Confirm"):
            save_customer_feedback(
                claim_id=claim_id,
                message="CONFIRM",
                additional_info=""
            )

            st.success("✅ Your confirmation has been sent to the insurance team.")


        # -------------------------
        # DISPUTE
        # -------------------------
        """
        Goal:
        Let the customer indicate disagreement with the claim.

        Logic:
        - Save a feedback record in the database
        - Store message type = DISPUTE
        """

        if colB.button("⚠️ Dispute"):
            save_customer_feedback(
                claim_id=claim_id,
                message="DISPUTE",
                additional_info=""
            )

            st.warning("⚠️ Your dispute has been sent to the insurance team.")


        # -------------------------
        # PROVIDE INFO
        # -------------------------
        """
        Goal:
        Open a text form so the customer can send more details.

        Logic:
        - Clicking the button does not send data yet
        - It only tells the interface to show the message form
        """

        if colC.button("📩 Provide Info"):
            st.session_state["show_message"] = True


        # -------------------------
        # MESSAGE FORM
        # -------------------------
        """
        Goal:
        Display a text box for additional information.

        Why use session_state here?
        → keeps the message form visible after button clicks

        Important note:
        Once opened, this form stays visible
        until the page state changes or is reset.
        """

        if st.session_state.get("show_message"):

            st.markdown("### 📩 Send Additional Information")

            user_message = st.text_area(
                "Write your message to the insurance team"
            )

            if st.button("📤 Send Message"):
                """
                Goal:
                Save the additional message in the database.

                Logic:
                - message type = PROVIDE_INFO
                - additional_info = actual customer text
                """

                save_customer_feedback(
                    claim_id=claim_id,
                    message="PROVIDE_INFO",
                    additional_info=user_message
                )

                st.success("📨 Your message has been sent to the insurance team.")