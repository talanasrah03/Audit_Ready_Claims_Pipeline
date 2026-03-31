"""
Risk scoring module.

Goal:
Assign a risk score to each claim based on:
- comparison with ground truth
- data quality issues (missing fields, mismatches)
- learned instability from past corrections

What this script does:
- Compares predicted vs correct values
- Adds risk points for each issue
- Generates an explainable list of reasons
- Outputs a final risk level (LOW, MEDIUM, HIGH)

Important concept:
Risk is cumulative:
→ more issues = higher risk

Example:
Missing amount (+2)
Wrong claim_type (+2)
→ total score = 4 → HIGH risk
"""

import json   # Used to read and write structured data in JSON format
from src.learning.correction_memory import get_pattern_summary   # Retrieves learned correction patterns to assess data reliability

# =========================
# HELPER FUNCTIONS 💣
# =========================

def is_missing(value):
    """
    Goal:
    Check if a value is missing or invalid.

    Logic:
    - None → missing
    - empty string → missing
    - "none", "null" → treated as missing

    Why important:
    AI outputs may contain:
    - None
    - empty strings
    - text like "null"

    Example:
    value = None → True
    value = "" → True
    value = "null" → True
    value = "5000" → False
    """

    if value is None:
        return True

    if str(value).strip().lower() in ["", "none", "null"]:
        return True

    return False


def safe_int(value):
    """
    Goal:
    Safely convert a value to integer.

    Logic:
    - Try to convert
    - If fails → return None instead of crashing

    Why important:
    AI outputs may contain:
    - "1200"
    - 1200
    - "1200 USD"
    - invalid values

    Example:
    "1200" → 1200
    "abc" → None
    """

    try:
        return int(value)
    except:
        return None


# =========================
# LOAD DATA
# =========================
"""
Goal:
Load predictions and ground truth.

predictions:
→ AI output (cleaned claims)

ground_truth:
→ correct reference values

gt_dict:
→ fast lookup using doc_id
"""

with open("data/processed/cleaned_claims.json", "r") as f:
    predictions = json.load(f)

with open("ground_truth/ground_truth.json", "r") as f:
    ground_truth = json.load(f)


# Convert ground truth list → dictionary for fast access
"""
Example:
gt_dict["claim_1"] → returns ground truth instantly

Without this:
→ would need nested loops (slow)
"""
gt_dict = {item["doc_id"]: item for item in ground_truth}


# =========================
# LOAD LEARNING PATTERNS
# =========================
"""
Goal:
Incorporate past human corrections.

Example:
{
    "amount_corrections": 8,
    "type_corrections": 3
}

Meaning:
- amount unreliable → increase risk
"""
patterns = get_pattern_summary()


# Store results
risk_results = []


# =========================
# MAIN LOOP
# =========================
"""
Goal:
Compute risk score for each claim.

Logic:
1. Compare prediction vs ground truth
2. Add points for each issue
3. Assign final risk level
"""

for pred in predictions:

    doc_id = pred["doc_id"]

    # Get corresponding ground truth
    gt = gt_dict.get(doc_id)

    # Skip if no ground truth exists
    if not gt:
        continue


    # =========================
    # INITIALIZE RISK
    # =========================
    """
    risk_score:
    → numeric score (starts at 0)

    reasons:
    → list explaining why risk increased
    """

    risk_score = 0
    reasons = []


    # =========================
    # MISSING FIELDS
    # =========================
    """
    Missing important fields increases risk.

    Logic:
    Each missing field adds +2

    Example:
    missing claim_type → +2
    missing amount → +2
    """

    if is_missing(pred.get("claim_type")):
        risk_score += 2
        reasons.append("Missing claim_type")

    if is_missing(pred.get("amount")):
        risk_score += 2
        reasons.append("Missing amount")


    # =========================
    # AMOUNT MISMATCH
    # =========================
    """
    Compare predicted amount with ground truth.

    Logic:
    - Convert both to integers
    - Check difference

    Threshold:
    > 5000 → considered large mismatch

    Example:
    pred = 10000, gt = 3000 → diff = 7000 → risk +3
    """

    pred_amount = safe_int(pred.get("amount"))
    gt_amount = safe_int(gt.get("amount"))

    if pred_amount is not None and gt_amount is not None:

        if abs(pred_amount - gt_amount) > 5000:
            risk_score += 3
            reasons.append("Large amount mismatch")


    # =========================
    # TYPE MISMATCH
    # =========================
    """
    Compare claim_type.

    Logic:
    - Convert both to lowercase
    - Compare strings

    Example:
    "Vehicle Theft" vs "vehicle theft" → same
    "Vehicle Theft" vs "Parked Car" → mismatch
    """

    if not is_missing(pred.get("claim_type")):

        if str(pred.get("claim_type")).lower() != str(gt.get("claim_type")).lower():
            risk_score += 2
            reasons.append("Claim type mismatch")


    # =========================
    # 💣 LEARNING EFFECT
    # =========================
    """
    Adjust risk based on past corrections.

    Logic:
    If a field was corrected many times:
    → system considers it unreliable
    → increases risk

    Example:
    amount corrected > 5 times → +2 risk
    """

    if patterns.get("amount_corrections", 0) > 5:
        risk_score += 2
        reasons.append("System learned amount is unreliable")

    if patterns.get("type_corrections", 0) > 5:
        risk_score += 2
        reasons.append("System learned claim type is unreliable")


    # =========================
    # FINAL RISK LEVEL
    # =========================
    """
    Convert numeric score → category.

    Rules:
    score ≥ 4 → HIGH
    score ≥ 2 → MEDIUM
    else → LOW

    Example:
    score = 5 → HIGH
    score = 3 → MEDIUM
    score = 1 → LOW
    """

    if risk_score >= 4:
        risk_level = "HIGH"
    elif risk_score >= 2:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"


    # =========================
    # STORE RESULT
    # =========================
    risk_results.append({
        "doc_id": doc_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "reasons": reasons
    })


# =========================
# SAVE RESULTS
# =========================
"""
Goal:
Save risk analysis to file.

indent=2:
→ improves readability
"""

with open("data/processed/risk_scores.json", "w") as f:
    json.dump(risk_results, f, indent=2)


print("Risk scoring complete!")