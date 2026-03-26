"""
RAG-style validation with:
- domain-based rules
- learning from past human corrections
- database persistence
"""

import json
from datetime import datetime
from src.database.db import insert_claim, save_ai_result
from src.config.config import CONFIGS
from src.learning.correction_memory import get_pattern_summary


# =========================
# LOAD DATA
# =========================
with open("data/processed/cleaned_claims.json", "r") as f:
    claims = json.load(f)

# Load learned patterns 💣
patterns = get_pattern_summary()


# =========================
# HELPER FUNCTION
# =========================
def get_rule(claim_type, rules):
    for rule in rules:
        if rule["claim_type"] == claim_type:
            return rule
    return None


# =========================
# MAIN LOOP
# =========================
validated_claims = []

for claim in claims:

    claim_type = claim.get("claim_type")
    amount = claim.get("amount")
    claim_date = claim.get("claim_date")
    customer_name = claim.get("customer_name")
    domain = claim.get("domain", "vehicle")

    # =========================
    # DOMAIN HANDLING
    # =========================
    if domain not in CONFIGS:
        domain_config = CONFIGS["vehicle"]  # fallback
        domain_warning = "Domain undefined in the system"
    else:
        domain_config = CONFIGS[domain]
        domain_warning = None

    rules = domain_config["rules"]

    validation = {
        "doc_id": claim["doc_id"],
        "valid": True,
        "issues": []
    }

    # Add domain warning if needed
    if domain_warning:
        validation["issues"].append(domain_warning)
        validation["valid"] = False

    # -------------------------
    # BASIC RULES
    # -------------------------
    if not claim_type:
        validation["valid"] = False
        validation["issues"].append("Missing claim_type")

    if not amount:
        validation["valid"] = False
        validation["issues"].append("Missing amount")

    if not customer_name:
        validation["valid"] = False
        validation["issues"].append("Missing customer_name")

    if not claim_date:
        validation["valid"] = False
        validation["issues"].append("Missing claim_date")

    # -------------------------
    # RANGE CHECK
    # -------------------------
    rule = get_rule(claim_type, rules)

    if rule and amount:
        if amount < rule["min_amount"]:
            validation["valid"] = False
            validation["issues"].append("Amount too low")

        if amount > rule["max_amount"]:
            validation["valid"] = False
            validation["issues"].append("Amount too high")

    # -------------------------
    # DATE VALIDATION
    # -------------------------
    if claim_date:
        try:
            date_obj = datetime.strptime(claim_date, "%Y-%m-%d")
            if date_obj > datetime.now():
                validation["valid"] = False
                validation["issues"].append("Future date")
        except:
            validation["valid"] = False
            validation["issues"].append("Invalid date format")

    # =========================
    # 💣 LEARNING FROM PAST CORRECTIONS
    # =========================
    if patterns.get("amount_corrections", 0) > 5:
        validation["issues"].append("Amount field unstable (learned)")
        validation["valid"] = False

    if patterns.get("type_corrections", 0) > 5:
        validation["issues"].append("Claim type unstable (learned)")
        validation["valid"] = False

    # -------------------------
    # SEVERITY
    # -------------------------
    if len(validation["issues"]) >= 2:
        validation["severity"] = "HIGH"
    else:
        validation["severity"] = "LOW"

    validated_claim = {
        **claim,
        "validation": validation
    }

    validated_claims.append(validated_claim)

    # -------------------------
    # SAVE TO DB
    # -------------------------
    claim_id = claim.get("claim_id") or claim.get("doc_id")

    insert_claim(
        claim_id=claim_id,
        status="validated",
        risk_level=validation["severity"]
    )

    save_ai_result(
        claim_id=claim_id,
        extracted_data=validated_claim,
        consistency_score=1.0,
        issues=validation["issues"],
        explanation="Validation completed with learning layer"
    )


# =========================
# SAVE FILE
# =========================
with open("data/processed/validated_claims.json", "w") as f:
    json.dump(validated_claims, f, indent=2)

print("RAG validation complete!")