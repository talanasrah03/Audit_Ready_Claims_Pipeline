"""
RAG-style validation module.

Goal:
Validate extracted claims using:
- domain-specific business rules
- learned patterns from past human corrections
- database storage for auditability

What this script does:
- Reads cleaned claims
- Applies validation rules
- Detects issues (missing data, invalid values, anomalies)
- Uses past human feedback to adjust validation
- Assigns severity level
- Saves results (file + database)

Important concept:
This is NOT real RAG (Retrieval-Augmented Generation),
but a "RAG-style" system:
→ rules + memory + structured validation

Example:
If amount is outside expected range:
→ "Amount too high" issue is added
"""

import json   # Used to read and write structured data in JSON format
from datetime import datetime   # Used to parse and validate date values
from src.database.db import insert_claim, save_ai_result   # Used to store validated claims and AI results in the database
from src.config.config import CONFIGS   # Contains domain-specific validation rules and configurations
from src.learning.correction_memory import get_pattern_summary   # Retrieves learned patterns from past human corrections

# =========================
# LOAD DATA
# =========================
"""
Goal:
Load cleaned claims (output from previous step).

Logic:
- Read JSON file
- Convert into Python list

Example:
claims = [
    {"amount": 5000, "claim_type": "..."},
    ...
]
"""
with open("data/processed/cleaned_claims.json", "r") as f:
    claims = json.load(f)


# =========================
# LOAD LEARNING PATTERNS
# =========================
"""
Goal:
Retrieve learned patterns from past human corrections.

Logic:
get_pattern_summary() returns something like:
{
    "amount_corrections": 8,
    "type_corrections": 3
}

Meaning:
- amount corrected often → unstable field
- type corrected often → unreliable field
"""
patterns = get_pattern_summary()


# =========================
# HELPER FUNCTION
# =========================
def get_rule(claim_type, rules):
    """
    Goal:
    Find the rule corresponding to a claim type.

    Logic:
    - Loop through all rules
    - Return the matching one

    Example:
    claim_type = "Vehicle Theft"
    → returns rule with min/max amounts

    If not found:
    → return None
    """

    for rule in rules:
        if rule["claim_type"] == claim_type:
            return rule

    return None


# =========================
# MAIN LOOP
# =========================
"""
Goal:
Validate each claim.

Logic:
- Loop through all claims
- Apply validation rules
- Store results
"""

validated_claims = []

for claim in claims:

    # =========================
    # EXTRACT FIELDS SAFELY
    # =========================
    """
    .get() is used instead of direct access.

    Why?
    → prevents crashes if field is missing

    Example:
    claim = {}
    claim.get("amount") → None
    claim["amount"] → ❌ error
    """

    claim_type = claim.get("claim_type")
    amount = claim.get("amount")
    claim_date = claim.get("claim_date")
    customer_name = claim.get("customer_name")
    domain = claim.get("domain", "vehicle")


    # =========================
    # DOMAIN HANDLING
    # =========================
    """
    Goal:
    Select correct validation rules based on domain.

    Logic:
    - If domain exists → use it
    - If not → fallback to "vehicle"

    Why important:
    Prevents system crash when unknown domain appears
    """

    if domain not in CONFIGS:
        domain_config = CONFIGS["vehicle"]
        domain_warning = "Domain undefined in the system"
    else:
        domain_config = CONFIGS[domain]
        domain_warning = None

    rules = domain_config["rules"]


    # =========================
    # INITIAL VALIDATION OBJECT
    # =========================
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
    """
    Goal:
    Ensure required fields exist.

    Logic:
    If field is missing → mark invalid
    """

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
    """
    Goal:
    Validate amount against business rules.

    Logic:
    - Get rule for claim_type
    - Compare amount with min/max

    Example:
    min = 500, max = 50000

    amount = 100 → "too low"
    amount = 100000 → "too high"
    """

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
    """
    Goal:
    Ensure date is valid and realistic.

    Logic:
    - Parse date string
    - Check if future date

    Example:
    "2030-01-01" → invalid (future)
    """

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
    # 💣 LEARNING LAYER
    # =========================
    """
    Goal:
    Adjust validation based on past human corrections.

    Logic:
    If field is frequently corrected:
    → treat it as unstable

    Example:
    amount corrected > 5 times
    → flag as unstable
    """

    if patterns.get("amount_corrections", 0) > 5:
        validation["issues"].append("Amount field unstable (learned)")
        validation["valid"] = False

    if patterns.get("type_corrections", 0) > 5:
        validation["issues"].append("Claim type unstable (learned)")
        validation["valid"] = False


    # -------------------------
    # SEVERITY
    # -------------------------
    """
    Goal:
    Assign risk level based on number of issues.

    Logic:
    ≥ 2 issues → HIGH risk
    < 2 issues → LOW risk

    Example:
    ["Missing amount", "Future date"]
    → HIGH
    """

    if len(validation["issues"]) >= 2:
        validation["severity"] = "HIGH"
    else:
        validation["severity"] = "LOW"


    # =========================
    # MERGE RESULTS
    # =========================
    """
    Goal:
    Combine original claim + validation results.

    **claim:
    → copies all original fields

    Example:
    {"amount": 5000} + {"validation": {...}}
    """

    validated_claim = {
        **claim,
        "validation": validation
    }

    validated_claims.append(validated_claim)


    # -------------------------
    # SAVE TO DATABASE
    # -------------------------
    """
    Goal:
    Persist results for tracking and audit.

    claim_id logic:
    - use claim_id if available
    - otherwise fallback to doc_id
    """

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
"""
Goal:
Store validated claims for next pipeline step.

indent=2:
→ improves readability
"""

with open("data/processed/validated_claims.json", "w") as f:
    json.dump(validated_claims, f, indent=2)


print("RAG validation complete!")