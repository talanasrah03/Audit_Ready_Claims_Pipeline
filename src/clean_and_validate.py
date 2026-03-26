"""
This script is responsible for cleaning and slightly standardizing the extracted claims data.

Context in the project:
After extracting information from raw insurance claims (using an AI model),
the data may contain inconsistencies (especially in numeric fields like "amount").

This file takes the extracted data and:
- Keeps important fields as they are (to avoid losing information)
- Lightly cleans the "amount" field to ensure it is usable as a number
- Preserves the domain field
- Outputs a new cleaned dataset for the next steps of the pipeline

Important design choice:
We intentionally use a "SAFE MODE" approach:
→ We avoid aggressive cleaning to prevent accidental data corruption.
→ Only minimal transformation is applied where necessary.

Input:
- data/processed/extracted_claims_v3.json

Output:
- data/processed/cleaned_claims.json
"""

import json
import re


# =========================
# LOAD EXTRACTED CLAIMS
# =========================
with open("data/processed/extracted_claims_v3.json", "r") as f:
    claims = json.load(f)


# This list will store all cleaned claims
cleaned = []


# =========================
# PROCESS EACH CLAIM
# =========================
for claim in claims:
    # Create a cleaned version of the claim
    cleaned_claim = {
        "doc_id": claim.get("doc_id"),
        "claim_id": claim.get("claim_id"),
        "customer_name": claim.get("customer_name"),
        "claim_date": claim.get("claim_date"),
        "claim_type": claim.get("claim_type"),
        "domain": claim.get("domain", "car"),  # default domain for backward compatibility
        "amount": None
    }

    # =========================
    # CLEAN AMOUNT FIELD
    # =========================
    value = claim.get("amount")

    if value:
        numbers = re.findall(r"\d+", str(value))

        if numbers:
            cleaned_claim["amount"] = int("".join(numbers))

    cleaned.append(cleaned_claim)


# =========================
# SAVE CLEANED DATA
# =========================
with open("data/processed/cleaned_claims.json", "w") as f:
    json.dump(cleaned, f, indent=2)


# =========================
# FINAL CONFIRMATION
# =========================
print("Cleaning complete (SAFE MODE)")