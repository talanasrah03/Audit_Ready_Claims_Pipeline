"""
Risk scoring system with:
- comparison vs ground truth
- explainable scoring
- learning-based risk boost 💣
"""

import json
from src.learning.correction_memory import get_pattern_summary


# =========================
# LOAD DATA
# =========================
with open("data/processed/cleaned_claims.json", "r") as f:
    predictions = json.load(f)

with open("data/ground_truth/ground_truth.json", "r") as f:
    ground_truth = json.load(f)

gt_dict = {item["doc_id"]: item for item in ground_truth}

# Load learning patterns
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

    # -------------------------
    # MISSING FIELDS
    # -------------------------
    if pred.get("claim_type") is None:
        risk_score += 2
        reasons.append("Missing claim_type")

    if pred.get("amount") is None:
        risk_score += 2
        reasons.append("Missing amount")

    # -------------------------
    # AMOUNT MISMATCH
    # -------------------------
    try:
        pred_amount = int(pred.get("amount"))
        gt_amount = int(gt.get("amount"))

        if abs(pred_amount - gt_amount) > 5000:
            risk_score += 3
            reasons.append("Large amount mismatch")

    except:
        pass

    # -------------------------
    # TYPE MISMATCH
    # -------------------------
    if str(pred.get("claim_type")).lower() != str(gt.get("claim_type")).lower():
        risk_score += 2
        reasons.append("Claim type mismatch")

    # =========================
    # 💣 LEARNING EFFECT
    # =========================
    if patterns["amount_corrections"] > 5:
        risk_score += 2
        reasons.append("System learned amount is unreliable")

    if patterns["type_corrections"] > 5:
        risk_score += 2
        reasons.append("System learned claim type is unreliable")

    # -------------------------
    # FINAL LEVEL
    # -------------------------
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