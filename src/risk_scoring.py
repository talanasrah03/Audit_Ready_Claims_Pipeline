"""
Risk scoring system with:
- comparison vs ground truth
- explainable scoring
- learning-based risk boost 💣
"""

import json
from src.learning.correction_memory import get_pattern_summary


# =========================
# HELPER FUNCTIONS 💣
# =========================
def is_missing(value):
    """Check if a value is missing or invalid"""
    if value is None:
        return True
    if str(value).strip().lower() in ["", "none", "null"]:
        return True
    return False


def safe_int(value):
    """Safely convert to int"""
    try:
        return int(value)
    except:
        return None


# =========================
# LOAD DATA
# =========================
with open("data/processed/cleaned_claims.json", "r") as f:
    predictions = json.load(f)

with open("data/ground_truth/ground_truth.json", "r") as f:
    ground_truth = json.load(f)

gt_dict = {item["doc_id"]: item for item in ground_truth}

patterns = get_pattern_summary()

risk_results = []


# =========================
# MAIN LOOP
# =========================
for pred in predictions:

    doc_id = pred["doc_id"]
    gt = gt_dict.get(doc_id)

    if not gt:
        continue

    risk_score = 0
    reasons = []

    # =========================
    # MISSING FIELDS (FIXED 💣)
    # =========================
    if is_missing(pred.get("claim_type")):
        risk_score += 2
        reasons.append("Missing claim_type")

    if is_missing(pred.get("amount")):
        risk_score += 2
        reasons.append("Missing amount")

    # =========================
    # AMOUNT MISMATCH
    # =========================
    pred_amount = safe_int(pred.get("amount"))
    gt_amount = safe_int(gt.get("amount"))

    if pred_amount is not None and gt_amount is not None:
        if abs(pred_amount - gt_amount) > 5000:
            risk_score += 3
            reasons.append("Large amount mismatch")

    # =========================
    # TYPE MISMATCH
    # =========================
    if not is_missing(pred.get("claim_type")):
        if str(pred.get("claim_type")).lower() != str(gt.get("claim_type")).lower():
            risk_score += 2
            reasons.append("Claim type mismatch")

    # =========================
    # 💣 LEARNING EFFECT
    # =========================
    if patterns.get("amount_corrections", 0) > 5:
        risk_score += 2
        reasons.append("System learned amount is unreliable")

    if patterns.get("type_corrections", 0) > 5:
        risk_score += 2
        reasons.append("System learned claim type is unreliable")

    # =========================
    # FINAL LEVEL
    # =========================
    if risk_score >= 4:
        risk_level = "HIGH"
    elif risk_score >= 2:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    risk_results.append({
        "doc_id": doc_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "reasons": reasons
    })


# =========================
# SAVE
# =========================
with open("data/processed/risk_scores.json", "w") as f:
    json.dump(risk_results, f, indent=2)

print("Risk scoring complete!")