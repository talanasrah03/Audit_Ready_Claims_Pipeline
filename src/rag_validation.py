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
- Assigns a severity level
- Saves results both to a file and to the database

Important concept:
This is NOT real RAG (Retrieval-Augmented Generation).

Why it is called "RAG-style":
- the system uses external structured knowledge
- that knowledge comes from domain rules and stored correction patterns
- validation decisions are guided by those external sources

So the idea is similar to RAG in spirit:
→ the model output is checked using additional retrieved knowledge
But here the retrieved knowledge is:
- configuration rules
- correction memory
rather than documents or vector search.
"""

import json   # Used to read and write structured data in JSON format
from datetime import datetime   # Used to parse and validate claim dates
from src.database.db import insert_claim, save_ai_result   # Used to store validated claims and AI results in the database
from src.config.config import CONFIGS   # Contains domain-specific validation rules and configurations
from src.learning.correction_memory import get_pattern_summary   # Retrieves learned patterns from past human corrections


# =========================
# LOAD DATA
# =========================
"""
Goal:
Load cleaned claims produced by the previous pipeline step.

Logic:
- Open the cleaned JSON file
- Convert it into a Python list of claim dictionaries

Example:
claims = [
    {"amount": 5000, "claim_type": "Vehicle Theft"},
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
get_pattern_summary() returns a dictionary such as:
{
    "amount_corrections": 8,
    "type_corrections": 3
}

Meaning:
- amount has often been corrected by humans
- claim_type has also been corrected, but less often

Why important:
These values help the system detect instability in certain fields.
"""

patterns = get_pattern_summary()


# =========================
# HELPER FUNCTION
# =========================
def get_rule(claim_type, rules):
    """
    Goal:
    Find the validation rule corresponding to the current claim type.

    Logic:
    - Loop through all rules for the domain
    - Return the rule whose claim_type matches

    Example:
    claim_type = "Vehicle Theft"
    → returns the rule containing its min_amount and max_amount

    If no rule matches:
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
Validate each cleaned claim.

Logic:
- Loop through all claims
- Apply rule-based checks
- Apply learning-based checks
- Build final validation result
- Save result for later steps
"""

validated_claims = []

for claim in claims:

    # =========================
    # EXTRACT FIELDS SAFELY
    # =========================
    """
    Goal:
    Read relevant claim fields safely.

    Logic:
    .get("field") means:
    - return the field value if it exists
    - return None if it does not exist

    Why important:
    This avoids crashes when a field is missing.

    Example:
    claim = {}
    claim.get("amount") → None
    claim["amount"] → would raise an error
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
    Select the correct validation rules based on domain.

    Logic:
    - If domain exists in CONFIGS → use that domain configuration
    - If not → fallback to "vehicle"
    - Add a warning because the domain was unknown

    Why important:
    This prevents the system from crashing when an unexpected domain appears.
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
    """
    Goal:
    Start a validation record for the current claim.

    Logic:
    - Assume the claim is valid at the beginning
    - Add issues later if problems are found
    """

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
    Ensure required fields are present.

    Logic:
    - If a field is missing or empty-like → mark the claim invalid
    - Add an issue explaining what is missing

    Important:
    `if not amount:` treats values like:
    - None
    - ""
    - 0

    as missing.

    In this project, amount = 0 is unlikely to be realistic,
    so this behavior is acceptable.
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
    Validate the amount against domain-specific business rules.

    Logic:
    - Find the rule matching the claim_type
    - Compare amount with min_amount and max_amount

    Example:
    min = 500, max = 50000

    amount = 100 → "Amount too low"
    amount = 100000 → "Amount too high"

    Important:
    This check runs only if:
    - a matching rule exists
    - amount is truthy

    So if amount is None, empty, or 0,
    this block is skipped.
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
    Ensure the claim date is valid and realistic.

    Logic:
    - Parse the date using YYYY-MM-DD format
    - Check whether the date is in the future
    - If parsing fails → mark format as invalid

    Example:
    "2030-01-01" → invalid (future date)
    "01/01/2030" → invalid format
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
    # LEARNING LAYER
    # =========================
    """
    Goal:
    Adjust validation using past human correction patterns.

    Logic:
    - If a field has been corrected many times in the past
    - treat it as unstable
    - add this as a new validation issue

    Example:
    amount corrected more than 5 times
    → add "Amount field unstable (learned)"

    Why important:
    This makes the system adaptive,
    even though it is still rule-based.
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
    Assign a severity level based on the number of issues.

    Logic:
    - 2 or more issues → HIGH
    - 0 or 1 issue → LOW

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
    Combine the original claim data with the validation result.

    Logic:
    **claim means:
    - copy all existing key-value pairs from the original claim
    - then add a new field called "validation"

    Example:
    original claim:
    {"amount": 5000}

    result:
    {"amount": 5000, "validation": {...}}
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
    Persist validation results for auditability and later use.

    claim_id logic:
    - use claim_id if available
    - otherwise fallback to doc_id

    Why important:
    This ensures each validated record still has an identifier,
    even if claim_id is missing.
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
Store validated claims for the next pipeline step.

Logic:
- Save all validated claims into JSON format

indent=2:
→ improves readability for humans
"""

with open("data/processed/validated_claims.json", "w") as f:
    json.dump(validated_claims, f, indent=2)


print("RAG validation complete!")