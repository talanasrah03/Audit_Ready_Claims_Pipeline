import json
import re

# =========================
# LOAD EXTRACTED DATA
# =========================
with open("data/processed/extracted_claims_v2.json", "r", encoding="utf-8") as f:
    claims = json.load(f)

# =========================
# CLEAN AMOUNT (STRONG)
# =========================
def clean_amount(value):
    if not value:
        return None

    value = str(value).lower().replace(",", "").strip()

    # handle "50k"
    if "k" in value:
        try:
            return int(float(value.replace("k", "")) * 1000)
        except:
            return None

    # extract numbers
    numbers = re.findall(r"\d+", value)
    if not numbers:
        return None

    return int(numbers[0])

# =========================
# NORMALIZE CLAIM TYPE (STRONG)
# =========================
def normalize_claim_type(value):
    if not value:
        return None

    value = value.lower()

    if any(word in value for word in ["theft", "stolen"]):
        return "Vehicle Theft"

    if any(word in value for word in ["multi", "multiple", "several"]):
        return "Multi-vehicle Collision"

    if any(word in value for word in ["single", "one vehicle"]):
        return "Single Vehicle Collision"

    if any(word in value for word in ["park", "parking"]):
        return "Parked Car"

    return None

# =========================
# CLEAN NAME
# =========================
def clean_name(value):
    if not value:
        return None
    return value.strip().title()

# =========================
# CLEAN DATA
# =========================
cleaned = []

for claim in claims:
    cleaned_claim = {
        "doc_id": claim.get("doc_id"),
        "claim_id": claim.get("claim_id"),
        "customer_name": clean_name(claim.get("customer_name")),
        "claim_date": claim.get("claim_date"),
        "claim_type": normalize_claim_type(claim.get("claim_type")),
        "amount": clean_amount(claim.get("amount"))
    }

    cleaned.append(cleaned_claim)

# =========================
# SAVE CLEANED DATA
# =========================
with open("data/processed/cleaned_claims.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, indent=2, ensure_ascii=False)

print("✅ Cleaning & validation complete!")