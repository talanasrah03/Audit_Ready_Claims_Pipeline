from fastapi import FastAPI
from datetime import datetime

from src.config.config import CONFIGS
from src.learning.correction_memory import get_pattern_summary
from src.database.db import (
    insert_claim,
    save_ai_result,
    get_claim,
    log_action,
    get_audit_logs,
    create_audit_table
)

# Ensure audit table exists
create_audit_table()

app = FastAPI()

patterns = get_pattern_summary()


# =========================
# HELPER FUNCTIONS
# =========================
def build_explanation(validation, severity):
    if validation["valid"]:
        return f"Claim passed validation with severity {severity}."
    else:
        issues = ", ".join(validation["issues"])
        return f"Claim failed validation: {issues}. Severity: {severity}."


def compute_confidence(validation, patterns):
    confidence = 1.0

    # Penalize issues
    confidence -= 0.15 * len(validation["issues"])

    # Penalize instability
    if patterns.get("amount_corrections", 0) > 5:
        confidence -= 0.10

    if patterns.get("type_corrections", 0) > 5:
        confidence -= 0.10

    # Clamp
    confidence = max(0.0, min(1.0, confidence))

    # Convert to percentage
    confidence_percent = round(confidence * 100, 1)
    return f"{confidence_percent}%"


def detect_instability(patterns):
    flags = []

    if patterns.get("amount_corrections", 0) > 5:
        flags.append("Amount instability detected")

    if patterns.get("type_corrections", 0) > 5:
        flags.append("Type instability detected")

    return flags


# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"message": "AI Claims API is running 🚀"}


# =========================
# PROCESS CLAIM
# =========================
@app.post("/process_claim")
def process_claim(claim: dict):

    claim_id = claim.get("claim_id") or claim.get("doc_id")

    claim_type = claim.get("claim_type")
    amount = claim.get("amount")
    claim_date = claim.get("claim_date")
    customer_name = claim.get("customer_name")
    domain = claim.get("domain", "vehicle")

    # -------------------------
    # DOMAIN HANDLING
    # -------------------------
    if domain not in CONFIGS:
        domain_config = CONFIGS["vehicle"]
        domain_warning = "Domain undefined in the system"
    else:
        domain_config = CONFIGS[domain]
        domain_warning = None

    rules = domain_config["rules"]

    validation = {
        "valid": True,
        "issues": []
    }

    if domain_warning:
        validation["issues"].append(domain_warning)
        validation["valid"] = False

    # -------------------------
    # BASIC RULES
    # -------------------------
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

    # -------------------------
    # RANGE CHECK
    # -------------------------
    if claim_type and amount:
        for rule in rules:
            if rule["claim_type"] == claim_type:
                if amount < rule["min_amount"]:
                    validation["issues"].append("Amount too low")
                    validation["valid"] = False
                if amount > rule["max_amount"]:
                    validation["issues"].append("Amount too high")
                    validation["valid"] = False

    # -------------------------
    # DATE VALIDATION
    # -------------------------
    if claim_date:
        try:
            date_obj = datetime.strptime(claim_date, "%Y-%m-%d")
            if date_obj > datetime.now():
                validation["issues"].append("Future date")
                validation["valid"] = False
        except Exception:
            validation["issues"].append("Invalid date format")
            validation["valid"] = False

    # -------------------------
    # LEARNING (Adaptive Layer)
    # -------------------------
    if patterns.get("amount_corrections", 0) > 5:
        validation["issues"].append("Amount unstable (learned)")
        validation["valid"] = False

    if patterns.get("type_corrections", 0) > 5:
        validation["issues"].append("Type unstable (learned)")
        validation["valid"] = False

    # -------------------------
    # SEVERITY
    # -------------------------
    if len(validation["issues"]) >= 2:
        severity = "HIGH"
    else:
        severity = "LOW"

    # =========================
    # 💣 INTELLIGENCE LAYER
    # =========================
    instability_flags = detect_instability(patterns)
    explanation = build_explanation(validation, severity)
    confidence = compute_confidence(validation, patterns)

    # =========================
    # 💣 SAVE TO DATABASE
    # =========================
    insert_claim(
        claim_id=claim_id,
        status="processed",
        risk_level=severity
    )

    log_action(claim_id, "CLAIM_CREATED", claim)

    save_ai_result(
        claim_id=claim_id,
        extracted_data=claim,
        consistency_score=confidence,
        issues=validation["issues"],
        explanation=explanation
    )

    log_action(claim_id, "AI_VALIDATION", validation)

    # =========================
    # RESPONSE
    # =========================
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

    claim = get_claim(claim_id)

    if not claim:
        return {"error": "Claim not found"}

    return claim


# =========================
# GET AUDIT LOGS
# =========================
@app.get("/audit/{claim_id}")
def audit(claim_id: str):
    logs = get_audit_logs(claim_id)
    return {
        "claim_id": claim_id,
        "audit_logs": logs
    }