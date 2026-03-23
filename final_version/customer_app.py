"""
This script builds a customer-facing portal using Streamlit.

Context in the project:
Unlike app.py (internal dashboard for insurance employees),
this file represents the CUSTOMER interface.

It simulates how a customer would:
- Check the status of their claim
- View extracted claim information
- Respond to the insurance company (confirm, dispute, or provide more info)

This creates a full end-to-end system:
AI pipeline → internal review → customer interaction

Main idea:
The system sends a claim ID to the customer (e.g. via email),
and the customer uses that ID to access their claim here.

Inputs:
- cleaned_claims.json → extracted claim data
- human_review_queue.json → indicates if claim is under review
"""


import streamlit as st
import json


# =========================
# PAGE CONFIGURATION
# =========================
"""
Set page title and layout.

layout="centered":
→ narrower layout, better for simple user interaction (customer view)
"""
st.set_page_config(page_title="Customer Portal", layout="centered")

st.title("Insurance Customer Portal")


# =========================
# LOAD DATA
# =========================
"""
claims:
→ contains extracted claim data (what the system knows)

reviews:
→ contains claims that are still under human review
"""
with open("data/processed/cleaned_claims.json") as f:
    claims = json.load(f)

with open("data/processed/human_review_queue.json") as f:
    reviews = json.load(f)


# =========================
# CREATE LOOKUP TABLES
# =========================
"""
Convert lists into dictionaries for fast access.

claim_dict:
→ allows quick lookup of claim by ID

review_dict:
→ allows quick check if claim is under review
"""
review_dict = {r["doc_id"]: r for r in reviews}
claim_dict = {c["doc_id"]: c for c in claims}


# =========================
# INPUT CLAIM ID
# =========================
"""
Customer enters their claim ID manually.

This simulates:
→ customer receiving claim ID via email
→ customer using it to access their claim
"""
claim_id_input = st.text_input("Enter your Claim ID (from email)")

st.caption("Example: claim_1")


# =========================
# SEARCH BUTTON
# =========================
"""
The logic below only runs when the user clicks the button.

This prevents automatic execution on every keystroke.
"""
if st.button("Search Claim"):

    # Retrieve claim and review data
    claim = claim_dict.get(claim_id_input)
    review = review_dict.get(claim_id_input)


    # =========================
    # ERROR CASE
    # =========================
    """
    If claim ID does not exist:
    → show error message
    """
    if not claim:
        st.error("Claim not found. Please check your Claim ID.")


    else:
        # =========================
        # DISPLAY CLAIM DATA
        # =========================
        """
        Show the information extracted by the system.

        This is what the system "understood" from the original claim.
        """
        st.subheader("Your Claim")

        st.write(f"Name: {claim.get('customer_name')}")
        st.write(f"Date: {claim.get('claim_date')}")
        st.write(f"Type: {claim.get('claim_type')}")
        st.write(f"Amount: {claim.get('amount')}")


        # =========================
        # CLAIM STATUS
        # =========================
        """
        Determine whether the claim is still under review.

        Logic:
        - If claim exists in review_dict → still being reviewed
        - Otherwise → already processed
        """
        st.subheader("Claim Status")

        if review:
            st.warning("Your claim is under review")
        else:
            st.success("Your claim has been processed")


        # =========================
        # CUSTOMER ACTIONS
        # =========================
        """
        Allows the customer to respond.

        Possible actions:
        - CONFIRM → customer agrees with claim
        - DISPUTE → customer disagrees
        - PROVIDE_INFO → customer adds more details
        """
        st.subheader("Your Actions")

        action = st.selectbox(
            "Choose Action",
            ["CONFIRM", "DISPUTE", "PROVIDE_INFO"]
        )


        # Customer message input
        message = st.text_area("Your Message")


        # =========================
        # SUBMIT RESPONSE
        # =========================
        """
        When user clicks submit:
        - simulate saving response
        - display confirmation
        - show summary of submitted data
        """
        if st.button("Submit"):
            st.success("Your response has been submitted")

            st.info("Summary:")
            st.write({
                "claim_id": claim_id_input,
                "action": action,
                "message": message
            })