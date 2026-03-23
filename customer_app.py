import streamlit as st
import json

# =========================
# PAGE CONFIGURATION
# =========================
# This sets the page title and uses a centered layout
# Centered layout is better for simple customer interaction
st.set_page_config(page_title="Customer Portal", layout="centered")

# Main title
st.title("Customer Claim Portal")

# Small description under title
st.caption("Access your claim details and respond to the insurance company")


# =========================
# LOAD DATA
# =========================
# Load processed claims data (what the system extracted)
with open("data/processed/cleaned_claims.json") as f:
    claims = json.load(f)

# Load human review queue (claims that still need review)
with open("data/processed/human_review_queue.json") as f:
    reviews = json.load(f)


# =========================
# CREATE LOOKUP TABLES
# =========================
# Convert lists to dictionaries for faster access by claim ID

# Dictionary of claims → key = claim_id
claim_dict = {c["doc_id"]: c for c in claims}

# Dictionary of review items → key = claim_id
review_dict = {r["doc_id"]: r for r in reviews}


# =========================
# USER INPUT
# =========================
# Customer enters their claim ID manually
# This simulates receiving the ID via email
claim_id_input = st.text_input("Enter your Claim ID")

# Example to guide the user
st.caption("Example: claim_1")


# =========================
# SEARCH BUTTON
# =========================
# The logic runs only when user clicks the button
# This avoids unnecessary re-execution on every keystroke
if st.button("Search Claim"):

    # Retrieve claim data
    claim = claim_dict.get(claim_id_input)

    # Check if claim is under review
    review = review_dict.get(claim_id_input)

    # =========================
    # ERROR CASE
    # =========================
    # If claim does not exist → show error
    if not claim:
        st.error("Claim not found. Please check your Claim ID.")

    else:
        # =========================
        # DISPLAY CLAIM INFORMATION
        # =========================
        st.subheader("Claim Details")

        st.write(f"**Customer Name:** {claim.get('customer_name')}")
        st.write(f"**Date:** {claim.get('claim_date')}")
        st.write(f"**Type:** {claim.get('claim_type')}")
        st.write(f"**Amount:** {claim.get('amount')}")


        # =========================
        # CLAIM STATUS
        # =========================
        st.subheader("Status")

        # If claim is in review queue → still under review
        if review:
            st.warning("Your claim is currently under review.")
        else:
            st.success("Your claim has been processed.")


        # =========================
        # CUSTOMER ACTIONS
        # =========================
        st.subheader("Your Response")

        # User selects an action
        action = st.selectbox(
            "Choose an action",
            ["CONFIRM", "DISPUTE", "PROVIDE_INFO"]
        )

        # User can write additional message
        message = st.text_area("Add a message (optional)")


        # =========================
        # SUBMIT BUTTON
        # =========================
        if st.button("Submit Response"):

            # Simulate saving response
            st.success("Your response has been submitted successfully.")

            # Display summary
            st.info("Submitted Information:")
            st.write({
                "claim_id": claim_id_input,
                "action": action,
                "message": message
            })