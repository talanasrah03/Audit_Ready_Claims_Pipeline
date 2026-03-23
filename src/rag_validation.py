import json
from datetime import datetime

# =========================
# LOAD CLEANED CLAIMS
# =========================
with open("data/processed/cleaned_claims.json", "r") as f:
    claims = json.load(f)

# =========================
# KNOWLEDGE BASE (RAG RULES)
# =========================
rules = [
    {"claim_type": "Vehicle Theft", "min_amount": 500, "max_amount": 50000},
    {"claim_type": "Single Vehicle Collision", "min_amount": 200, "max_amount": 30000},
    {"claim_type": "Multi-vehicle Collision", "min_amount": 1000, "max_amount": 70000},
    {"claim_type": "Parked Car", "min_amount": 50, "max_amount": 10000},
]

# =========================
# HELPER: GET RULE
# =========================
def get_rule(claim_type):
    for rule in rules:
        if rule["claim_type"] == claim_type:
            return rule
    return None

# =========================
# VALIDATION
# =========================
validated_claims = []

for claim in claims:
    claim_type = claim.get("claim_type")
    amount = claim.get("amount")
    claim_date = claim.get("claim_date")
    customer_name = claim.get("customer_name")

    validation = {
        "doc_id": claim["doc_id"],
        "valid": True,
        "issues": []
    }

    # =========================
    # RULE 1 — Missing claim_type
    # =========================
    if not claim_type:
        validation["valid"] = False
        validation["issues"].append("Missing claim_type")

    # =========================
    # RULE 2 — Missing amount
    # =========================
    if not amount:
        validation["valid"] = False
        validation["issues"].append("Missing amount")

    # =========================
    # RULE 3 — Missing customer_name
    # =========================
    if not customer_name:
        validation["valid"] = False
        validation["issues"].append("Missing customer_name")

    # =========================
    # RULE 4 — Missing claim_date
    # =========================
    if not claim_date:
        validation["valid"] = False
        validation["issues"].append("Missing claim_date")

    # =========================
    # RULE 5 & 6 — Amount range check
    # =========================
    rule = get_rule(claim_type)

    if rule and amount:
        if amount < rule["min_amount"]:
            validation["valid"] = False
            validation["issues"].append("Amount too low for claim type")

        if amount > rule["max_amount"]:
            validation["valid"] = False
            validation["issues"].append("Amount exceeds expected range")

    # =========================
    # RULE 7 — Scenario consistency
    # =========================
    if claim_type == "Parked Car" and amount and amount > 15000:
        validation["valid"] = False
        validation["issues"].append("Unrealistic damage for parked car")

    if claim_type == "Vehicle Theft" and amount and amount < 1000:
        validation["valid"] = False
        validation["issues"].append("Amount too low for theft")

    # =========================
    # RULE 8 — Date validation
    # =========================
    if claim_date:
        try:
            date_obj = datetime.strptime(claim_date, "%Y-%m-%d")
            if date_obj > datetime.now():
                validation["valid"] = False
                validation["issues"].append("Claim date in the future")
        except:
            validation["valid"] = False
            validation["issues"].append("Invalid date format")
    # =========================
    # RULE 9 — Severity
    # =========================

    if len(validation["issues"]) >= 2:
         validation["severity"] = "HIGH"
    else:
        validation["severity"] = "LOW"
    # =========================
    # SAVE RESULT
    # =========================
    validated_claims.append({
        **claim,
        "validation": validation
    })

# =========================
# SAVE FILE
# =========================
with open("data/processed/validated_claims.json", "w") as f:
    json.dump(validated_claims, f, indent=2)

print("✅ RAG validation complete!")