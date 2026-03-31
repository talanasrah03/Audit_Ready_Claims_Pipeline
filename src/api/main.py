"""
This script creates the main API for processing insurance claims.

Goal:
Receive a claim, validate it using business rules and learned patterns,
assign a risk level, compute a confidence score, and store everything for audit.

What this script does:
- Validates claims (missing fields, incorrect values, business rules)
- Detects anomalies using learned correction patterns
- Assigns severity (LOW / HIGH risk)
- Computes a confidence score (how reliable the result is)
- Generates a clear explanation of the decision
- Stores all actions in a database for auditability

Important concept:
The system does NOT blindly trust AI outputs.
Instead, it:
→ validates them
→ explains them
→ logs everything for transparency
"""

from fastapi import FastAPI   # Used to create the web API and define endpoints
from datetime import datetime   # Used to validate and compare claim dates
import json   # Used to convert dictionaries into JSON strings before audit logging

from src.config.config import CONFIGS   # Contains domain-specific rules and validation settings
from src.learning.correction_memory import get_pattern_summary   # Loads learned instability patterns from past human corrections
from src.database.db import (
    insert_claim,         # Saves the main claim record in the database
    save_ai_result,       # Saves AI validation results and explanations
    get_claim,            # Retrieves a stored claim by its ID
    log_audit_event,      # Stores audit log events for traceability
    get_audit_logs,       # Retrieves audit history for a claim
    init_db               # Ensures required database tables exist before logging
)


# =========================
# INITIALIZATION
# =========================

"""
Goal:
Ensure the system is ready before processing any claims.

Logic:
- Create the audit table if it does not already exist
- Initialize the FastAPI application
- Load learned correction patterns

Why important:
Without this:
→ logging could fail because the audit table may not exist
→ the adaptive validation layer would not have access to learned patterns

Important detail:
This code runs when the file is loaded, not when the endpoint is called.

That means:
- audit table setup happens immediately
- learned patterns are loaded once at startup

Why this can be useful:
→ faster endpoint execution

Possible limitation:
→ if correction patterns change later in the database,
   this variable will not refresh automatically unless the app restarts
"""

init_db()

app = FastAPI()

patterns = get_pattern_summary()


# =========================
# HELPER FUNCTIONS
# =========================

def build_explanation(validation, severity):
    """
    Goal:
    Create a clear explanation for the final decision.

    Logic:
    - If claim is valid → return a simple success message
    - If claim is invalid → join all issues into one readable sentence

    Example:
    valid = True
    → "Claim passed validation with severity LOW"

    valid = False and issues = ["Missing amount", "Amount too high"]
    → "Claim failed validation: Missing amount, Amount too high. Severity: HIGH"
    """

    if validation["valid"]:
        return f"Claim passed validation with severity {severity}"
    else:
        issues = ", ".join(validation["issues"])
        return f"Claim failed validation: {issues}. Severity: {severity}"


def compute_confidence(validation, patterns):
    """
    Goal:
    Compute how confident the system is in the result (0% → 100%).

    Logic:
    - Start from 100%
    - Reduce confidence for each detected issue
    - Reduce confidence further if learned instability exists
    - Force the result to stay between 0% and 100%

    Formula:
    - each issue reduces confidence by 15%
    - unstable amount reduces confidence by 10%
    - unstable claim type reduces confidence by 10%

    Example:
    Start: 100%
    - 2 issues → -30%
    - unstable amount → -10%
    → final = 60%
    """

    confidence = 1.0

    confidence -= 0.15 * len(validation["issues"])

    if patterns.get("amount_corrections", 0) > 5:
        confidence -= 0.10

    if patterns.get("type_corrections", 0) > 5:
        confidence -= 0.10

    """
    Clamp logic:
    max(0.0, min(1.0, confidence))

    Meaning:
    - if confidence goes below 0 → force it to 0
    - if confidence goes above 1 → force it to 1

    Why important:
    Prevents impossible results like -15% or 120%
    """
    confidence = max(0.0, min(1.0, confidence))

    confidence_percent = round(confidence * 100, 1)

    return f"{confidence_percent}%"


def detect_instability(patterns):
    """
    Goal:
    Identify whether the system has learned that some fields are unstable.

    Logic:
    - Check how many times important fields were corrected in the past
    - If corrections exceed threshold → add warning flag

    Threshold used here:
    more than 5 corrections

    Example:
    amount_corrections = 8
    → "Amount instability detected"
    """

    flags = []

    if patterns.get("amount_corrections", 0) > 5:
        flags.append("Amount instability detected")

    if patterns.get("type_corrections", 0) > 5:
        flags.append("Type instability detected")

    return flags


# =========================
# ROOT ENDPOINT
# =========================

@app.get("/")
def root():
    """
    Goal:
    Provide a simple health check endpoint.

    Logic:
    - When the root URL is accessed, return a confirmation message

    Why useful:
    - Confirms that the API is running
    - Useful for quick testing in browser or Swagger

    Example:
    GET /
    → {"message": "AI Claims API is running 🚀"}
    """
    return {"message": "AI Claims API is running 🚀"}


# =========================
# PROCESS CLAIM
# =========================

@app.post("/process_claim")
def process_claim(claim: dict):
    """
    Goal:
    Process and evaluate a claim from start to finish.

    Logic:
    1. Extract data
    2. Validate required fields
    3. Apply business rules
    4. Apply learning-based checks
    5. Compute severity and confidence
    6. Save results
    7. Return structured response
    """

    # =========================
    # DATA EXTRACTION
    # =========================
    """
    Goal:
    Extract all necessary fields from the input claim.

    Logic:
    - Use .get() to avoid crashes if a field is missing
    - Use default domain "vehicle" if no domain is provided

    Important detail:
    claim.get("field") returns:
    - the field value if it exists
    - None if it does not exist

    claim.get("domain", "vehicle") returns:
    - the domain value if it exists
    - "vehicle" if it does not exist

    Example:
    If claim_id is missing but doc_id exists
    → fallback to doc_id
    """

    claim_id = claim.get("claim_id") or claim.get("doc_id")
    claim_type = claim.get("claim_type")
    amount = claim.get("amount")
    claim_date = claim.get("claim_date")
    customer_name = claim.get("customer_name")
    domain = claim.get("domain", "vehicle")

    """
    Important note:
    If both claim_id and doc_id are missing,
    claim_id will become None.

    That may still allow the function to continue,
    but database logging and traceability may become weaker.
    """

    # =========================
    # DOMAIN HANDLING
    # =========================
    """
    Goal:
    Apply correct business rules depending on claim domain.

    Logic:
    - If domain exists in CONFIGS → use its rules
    - If not → fallback to default domain ("vehicle")
    - Also mark the claim with a warning

    Example:
    domain = "health" but not defined in CONFIGS
    → use vehicle rules
    → add "Domain undefined in the system"
    """

    if domain not in CONFIGS:
        domain_config = CONFIGS["vehicle"]
        domain_warning = "Domain undefined in the system"
    else:
        domain_config = CONFIGS[domain]
        domain_warning = None

    rules = domain_config["rules"]

    # =========================
    # INITIAL VALIDATION
    # =========================
    """
    Goal:
    Initialize validation structure.

    Logic:
    - Start by assuming claim is valid
    - Add issues progressively if problems are found
    """

    validation = {
        "valid": True,
        "issues": []
    }

    if domain_warning:
        validation["issues"].append(domain_warning)
        validation["valid"] = False

    # =========================
    # BASIC FIELD CHECKS
    # =========================
    """
    Goal:
    Ensure required fields are present.

    Logic:
    - If a field is empty or missing → add issue
    - Mark claim as invalid

    Important detail:
    `if not amount:` treats values like None, "", and 0 as missing.

    In many claim systems, amount = 0 may be unrealistic anyway,
    but technically this check treats zero as missing too.

    Example:
    amount missing → "Missing amount"
    """

    if not claim_type:
        validation["issues"].append("Missing claim_type")
        validation["valid"] = False

    if not amount:
        validation["issues"].append("Missing amount")
        validation["valid"] = False

    if not customer_name:
        validation["issues"].append("Missing customer_name")
        validation["valid"] = False

    if not claim_date:
        validation["issues"].append("Missing claim_date")
        validation["valid"] = False

    # =========================
    # RANGE VALIDATION
    # =========================
    """
    Goal:
    Check if amount is within allowed range for claim type.

    Logic:
    - Loop through rules for this domain
    - Find the rule matching the current claim_type
    - Compare amount with minimum and maximum allowed values

    Example:
    min = 500, max = 20000

    amount = 100 → "Amount too low"
    amount = 50000 → "Amount too high"

    Important detail:
    This block runs only if both claim_type and amount are truthy.
    That means if amount is None, empty, or 0, this check is skipped.
    """

    if claim_type and amount:
        for rule in rules:
            if rule["claim_type"] == claim_type:

                if amount < rule["min_amount"]:
                    validation["issues"].append("Amount too low")
                    validation["valid"] = False

                if amount > rule["max_amount"]:
                    validation["issues"].append("Amount too high")
                    validation["valid"] = False

    # =========================
    # DATE VALIDATION
    # =========================
    """
    Goal:
    Ensure date is valid and realistic.

    Logic:
    - Parse date using YYYY-MM-DD format
    - Check if date is in the future
    - If parsing fails → mark format as invalid

    Example:
    "2030-01-01" → invalid (future)
    "10/01/2025" → invalid format
    """

    if claim_date:
        try:
            date_obj = datetime.strptime(claim_date, "%Y-%m-%d")

            if date_obj > datetime.now():
                validation["issues"].append("Future date")
                validation["valid"] = False

        except Exception:
            validation["issues"].append("Invalid date format")
            validation["valid"] = False

    # =========================
    # LEARNING-BASED VALIDATION
    # =========================
    """
    Goal:
    Adapt validation based on past system behavior.

    Logic:
    - If many corrections happened in the past
    - Mark the field as unstable
    - Treat that as an additional warning / risk signal

    Example:
    amount_corrections = 10
    → "Amount unstable (learned)"
    """

    if patterns.get("amount_corrections", 0) > 5:
        validation["issues"].append("Amount unstable (learned)")
        validation["valid"] = False

    if patterns.get("type_corrections", 0) > 5:
        validation["issues"].append("Type unstable (learned)")
        validation["valid"] = False

    # =========================
    # SEVERITY CALCULATION
    # =========================
    """
    Goal:
    Assign risk level to the claim.

    Exact rule:
    - 2 or more issues → HIGH
    - 0 or 1 issue → LOW

    Example:
    2 issues → HIGH
    1 issue → LOW
    """

    if len(validation["issues"]) >= 2:
        severity = "HIGH"
    else:
        severity = "LOW"

    # =========================
    # INTELLIGENCE LAYER
    # =========================
    """
    Goal:
    Enrich result with additional AI-style insights.

    Includes:
    - instability flags
    - readable explanation
    - confidence score
    """

    instability_flags = detect_instability(patterns)
    explanation = build_explanation(validation, severity)
    confidence = compute_confidence(validation, patterns)

    # =========================
    # SAVE TO DATABASE
    # =========================
    """
    Goal:
    Ensure full traceability and auditability.

    Logic:
    - Save claim summary
    - Log raw input
    - Save validation output
    - Log validation step

    Important:
    This creates a permanent record of:
    - what came in
    - what the system decided
    - why it decided that
    """

    insert_claim(
        claim_id=claim_id,
        status="processed",
        risk_level=severity
    )

    log_audit_event(
        claim_id=claim_id,
        actor="system",
        action="CLAIM_CREATED",
        details=json.dumps(claim)
    )

    save_ai_result(
        claim_id=claim_id,
        extracted_data=claim,
        consistency_score=confidence,
        issues=validation["issues"],
        explanation=explanation
    )

    log_audit_event(
        claim_id=claim_id,
        actor="AI",
        action="AI_VALIDATION",
        details=json.dumps(validation)
    )

    # =========================
    # RESPONSE
    # =========================
    """
    Goal:
    Return final structured result to the caller.

    Contains:
    - claim_id
    - validation result
    - severity
    - confidence
    - instability warnings
    - final explanation
    """

    return {
        "claim_id": claim_id,
        "validation": validation,
        "severity": severity,
        "confidence": confidence,
        "instability_flags": instability_flags,
        "explanation": explanation
    }


# =========================
# GET CLAIM
# =========================

@app.get("/claim/{claim_id}")
def fetch_claim(claim_id: str):
    """
    Goal:
    Retrieve a processed claim from the database.

    Logic:
    - If claim exists → return it
    - If not → return error message
    """

    claim = get_claim(claim_id)

    if not claim:
        return {"error": "Claim not found"}

    return claim


# =========================
# GET AUDIT LOGS
# =========================

@app.get("/audit/{claim_id}")
def audit(claim_id: str):
    """
    Goal:
    Retrieve full history of actions for a claim.

    Logic:
    - Fetch all logs related to this claim_id
    - Return them for transparency and debugging

    Example:
    - CLAIM_CREATED
    - AI_VALIDATION
    """

    logs = get_audit_logs(claim_id)

    return {
        "claim_id": claim_id,
        "audit_logs": logs
    }