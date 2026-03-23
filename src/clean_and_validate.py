import json
import re

with open("data/processed/extracted_claims_v3.json", "r") as f:
    claims = json.load(f)

cleaned = []

for claim in claims:
    cleaned_claim = {
        "doc_id": claim.get("doc_id"),
        "claim_id": claim.get("claim_id"),

        # 🔥 DO NOT OVER-CLEAN
        "customer_name": claim.get("customer_name"),
        "claim_date": claim.get("claim_date"),

        # only normalize claim type
        "claim_type": claim.get("claim_type"),

        # 🔥 only clean amount lightly
        "amount": None
    }

    # clean amount ONLY if needed
    value = claim.get("amount")

    if value:
        numbers = re.findall(r"\d+", str(value))
        if numbers:
            cleaned_claim["amount"] = int("".join(numbers))

    cleaned.append(cleaned_claim)

with open("data/processed/cleaned_claims.json", "w") as f:
    json.dump(cleaned, f, indent=2)

print("✅ Cleaning complete (SAFE MODE)")