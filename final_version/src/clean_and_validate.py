"""
This script is responsible for cleaning and slightly standardizing the extracted claims data.

Context in the project:
After extracting information from raw insurance claims (using an AI model),
the data may contain inconsistencies (especially in numeric fields like "amount").

This file takes the extracted data and:
- Keeps important fields as they are (to avoid losing information)
- Lightly cleans the "amount" field to ensure it is usable as a number
- Outputs a new cleaned dataset for the next steps of the pipeline (e.g., risk scoring)

Important design choice:
We intentionally use a "SAFE MODE" approach:
→ We avoid aggressive cleaning to prevent accidental data corruption.
→ Only minimal transformation is applied where necessary.

Input:
- data/processed/extracted_claims_v3.json

Output:
- data/processed/cleaned_claims.json
"""

import json   # Used to read and write JSON files (structured data format)
import re     # Used for simple text processing (especially extracting numbers)


# =========================
# LOAD EXTRACTED CLAIMS
# =========================
# Open the JSON file containing the previously extracted claims
with open("data/processed/extracted_claims_v3.json", "r") as f:
    claims = json.load(f)  
    # json.load converts the JSON file into a Python list of dictionaries


# This list will store all cleaned claims
cleaned = []


# =========================
# PROCESS EACH CLAIM
# =========================
# We loop through each claim one by one
for claim in claims:

    # Create a new dictionary for the cleaned version of the claim
    cleaned_claim = {
        # Keep identifiers as they are (no transformation needed)
        "doc_id": claim.get("doc_id"),
        "claim_id": claim.get("claim_id"),

        # IMPORTANT: We do NOT over-clean these fields
        # We keep them exactly as extracted to avoid losing meaning
        "customer_name": claim.get("customer_name"),
        "claim_date": claim.get("claim_date"),

        # Claim type could later be normalized if needed
        "claim_type": claim.get("claim_type"),

        # Amount will be cleaned separately
        "amount": None
    }


    # =========================
    # CLEAN AMOUNT FIELD (LIGHT CLEANING ONLY)
    # =========================
    # Extract the original value of "amount"
    value = claim.get("amount")

    # Only attempt cleaning if a value exists
    if value:
        # Convert the value to string and extract all numeric parts
        # Example:
        # "€1,200.50" → ["1", "200", "50"]
        numbers = re.findall(r"\d+", str(value))

        # If we found numbers, combine them into a single integer
        if numbers:
            # Join all number parts and convert to integer
            # ["1", "200", "50"] → "120050" → 120050
            cleaned_claim["amount"] = int("".join(numbers))


    # Add the cleaned claim to the final list
    cleaned.append(cleaned_claim)


# =========================
# SAVE CLEANED DATA
# =========================
# Write the cleaned claims into a new JSON file
with open("data/processed/cleaned_claims.json", "w") as f:
    json.dump(cleaned, f, indent=2)
    # indent=2 makes the file more readable (formatted nicely)


# =========================
# FINAL CONFIRMATION
# =========================
print("Cleaning complete (SAFE MODE)")