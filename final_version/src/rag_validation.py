"""
This script performs validation of extracted claims using rule-based logic
(simulating a simple RAG-style knowledge base).

Context in the project:
After extracting and cleaning the claims, we need to verify whether the data makes sense.

This step answers:
"Is this claim realistic and complete?"

This is NOT AI-based validation.
Instead, we use predefined business rules (knowledge base) to check consistency.

Main responsibilities:
- Detect missing fields
- Validate numerical ranges
- Check logical consistency between fields
- Validate dates
- Assign severity levels

Input:
- data/processed/cleaned_claims.json

Output:
- data/processed/validated_claims.json
"""


import json
from datetime import datetime


# =========================
# LOAD CLEANED CLAIMS
# =========================
"""
Each claim already has structured fields like:
{
    "doc_id": "claim_1",
    "customer_name": "...",
    "claim_type": "...",
    "amount": 12000
}
"""
with open("data/processed/cleaned_claims.json", "r") as f:
    claims = json.load(f)


# =========================
# KNOWLEDGE BASE (RULES)
# =========================
"""
This acts as a simplified "knowledge base".

Each rule defines:
- a claim_type
- a minimum acceptable amount
- a maximum acceptable amount

This simulates domain knowledge:
→ e.g. a vehicle theft usually costs more than 500
→ a parked car damage is usually lower

Structure:
rule = {
    "claim_type": "...",
    "min_amount": ...,
    "max_amount": ...
}
"""
rules = [
    {"claim_type": "Vehicle Theft", "min_amount": 500, "max_amount": 50000},
    {"claim_type": "Single Vehicle Collision", "min_amount": 200, "max_amount": 30000},
    {"claim_type": "Multi-vehicle Collision", "min_amount": 1000, "max_amount": 70000},
    {"claim_type": "Parked Car", "min_amount": 50, "max_amount": 10000},
]


# =========================
# HELPER FUNCTION
# =========================
def get_rule(claim_type):
    """
    Find the corresponding rule for a given claim_type.

    How it works:
    - loop through all rules
    - return the first matching one

    If no rule is found:
    → return None

    This allows flexible validation depending on claim type.
    """
    for rule in rules:
        if rule["claim_type"] == claim_type:
            return rule
    return None


# =========================
# VALIDATION PROCESS
# =========================
validated_claims = []

"""
We process each claim and build a validation result.

Each claim gets a "validation" object like:

"validation": {
    "valid": True/False,
    "issues": ["..."],
    "severity": "LOW/HIGH"
}
"""

for claim in claims:

    # Extract fields
    claim_type = claim.get("claim_type")
    amount = claim.get("amount")
    claim_date = claim.get("claim_date")
    customer_name = claim.get("customer_name")


    # Initialize validation result
    validation = {
        "doc_id": claim["doc_id"],
        "valid": True,
        "issues": []
    }


    # =========================
    # RULE 1 — Missing claim_type
    # =========================
    """
    If claim_type is missing or empty:
    → mark claim as invalid
    → add issue description
    """
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
    """
    Check if the amount is within expected range for this claim type.

    Example:
    Vehicle Theft → min=500, max=50000

    Conditions:
    amount < min → too low
    amount > max → too high
    """

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
    """
    Additional business logic rules:

    Example 1:
    Parked Car damage usually small → large amounts are suspicious

    Example 2:
    Vehicle Theft → should not have extremely low amount
    """

    if claim_type == "Parked Car" and amount and amount > 15000:
        validation["valid"] = False
        validation["issues"].append("Unrealistic damage for parked car")

    if claim_type == "Vehicle Theft" and amount and amount < 1000:
        validation["valid"] = False
        validation["issues"].append("Amount too low for theft")


    # =========================
    # RULE 8 — Date validation
    # =========================
    """
    Validate date format and logic.

    Step 1:
    Try to parse date using:
    datetime.strptime(date_string, format)

    Format:
    "%Y-%m-%d" → 2025-03-22

    Step 2:
    Compare with current date:
    if date > today → invalid (future date)
    """

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
    # RULE 9 — SEVERITY LEVEL
    # =========================
    """
    Severity is based on number of issues.

    Formula:
    number_of_issues = len(validation["issues"])

    If number_of_issues >= 2:
        severity = HIGH
    else:
        severity = LOW

    Example:
    issues = ["Missing amount"] → LOW
    issues = ["Missing amount", "Invalid date"] → HIGH
    """

    if len(validation["issues"]) >= 2:
        validation["severity"] = "HIGH"
    else:
        validation["severity"] = "LOW"


    # =========================
    # SAVE VALIDATED CLAIM
    # =========================
    """
    We merge:
    - original claim data
    - validation results

    **claim means:
    unpack all original fields

    Result:
    {
        ...original fields...,
        "validation": {...}
    }
    """
    validated_claims.append({
        **claim,
        "validation": validation
    })


# =========================
# SAVE OUTPUT
# =========================
with open("data/processed/validated_claims.json", "w") as f:
    json.dump(validated_claims, f, indent=2)


# =========================
# FINAL MESSAGE
# =========================
print("RAG validation complete!")