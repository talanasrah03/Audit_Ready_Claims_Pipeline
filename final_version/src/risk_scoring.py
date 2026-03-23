"""
This script assigns a risk score to each claim based on discrepancies
between predicted data (AI output) and ground truth (expected correct data).

Context in the project:
After extraction and validation, we want to quantify how "risky" or "suspicious"
each claim is.

This simulates a real-world fraud / risk detection system.

Main idea:
- Each issue adds points to a risk score
- Higher score → higher risk
- Each risk is explained with reasons (for transparency)

Input:
- cleaned_claims.json (AI predictions)
- ground_truth.json (correct reference)

Output:
- risk_scores.json (risk analysis per claim)
"""


import json


# =========================
# LOAD DATA
# =========================
"""
predictions:
→ extracted + cleaned claims from AI pipeline

ground_truth:
→ correct reference values

We will compare both to detect inconsistencies.
"""
with open("data/processed/cleaned_claims.json", "r", encoding="utf-8") as f:
    predictions = json.load(f)

with open("data/ground_truth/ground_truth.json", "r", encoding="utf-8") as f:
    ground_truth = json.load(f)


# Convert ground truth into dictionary for fast lookup
"""
Structure:
gt_dict = {
    "claim_1": {...},
    "claim_2": {...}
}
"""
gt_dict = {item["doc_id"]: item for item in ground_truth}


# Store final results
risk_results = []


# =========================
# MAIN LOOP (RISK RULES)
# =========================
"""
We evaluate each predicted claim against its ground truth.

For each claim:
- initialize risk_score = 0
- add points based on detected issues
- classify risk level
"""
for pred in predictions:

    doc_id = pred["doc_id"]

    # Find corresponding ground truth
    gt = gt_dict.get(doc_id)

    # Skip if no reference exists
    if not gt:
        continue


    # Initialize score and explanation list
    risk_score = 0
    reasons = []


    # =========================
    # RULE 1 — Missing claim_type
    # =========================
    """
    If claim_type is missing:
    → add +2 risk points

    Why?
    Missing category makes claim harder to interpret and validate.
    """
    if pred.get("claim_type") is None:
        risk_score += 2
        reasons.append("Missing claim_type")


    # =========================
    # RULE 2 — Missing amount
    # =========================
    """
    Missing financial value is critical.
    → add +2 risk points
    """
    if pred.get("amount") is None:
        risk_score += 2
        reasons.append("Missing amount")


    # =========================
    # RULE 3 — Amount mismatch
    # =========================
    """
    Compare predicted amount vs ground truth.

    Formula:
    difference = abs(pred_amount - gt_amount)

    abs(...) ensures the result is always positive.

    Example:
    pred = 12000, gt = 8000
    difference = |12000 - 8000| = 4000

    If difference > 5000:
    → considered a large mismatch
    → add +3 risk points
    """
    try:
        pred_amount = int(pred.get("amount"))
        gt_amount = int(gt.get("amount"))

        if abs(pred_amount - gt_amount) > 5000:
            risk_score += 3
            reasons.append("Large amount mismatch")

    except:
        """
        If conversion fails (e.g. None or invalid string),
        we ignore this rule safely.
        """
        pass


    # =========================
    # RULE 4 — Claim type mismatch
    # =========================
    """
    Compare predicted vs ground truth claim type.

    We normalize using:
    .lower() → makes comparison case-insensitive

    Example:
    "Vehicle Theft" vs "vehicle theft" → equal
    """
    if str(pred.get("claim_type")).lower() != str(gt.get("claim_type")).lower():
        risk_score += 2
        reasons.append("Claim type mismatch")


    # =========================
    # CLASSIFICATION
    # =========================
    """
    Convert numeric score into risk level.

    Rules:
    risk_score ≥ 4 → HIGH
    risk_score ≥ 2 → MEDIUM
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
    # SAVE RESULT
    # =========================
    """
    Each result includes:
    - doc_id → identifies claim
    - risk_score → numeric value
    - risk_level → category
    - reasons → explanation list
    """
    risk_results.append({
        "doc_id": doc_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "reasons": reasons
    })


# =========================
# SAVE RESULTS
# =========================
with open("data/processed/risk_scores.json", "w", encoding="utf-8") as f:
    json.dump(risk_results, f, indent=2, ensure_ascii=False)


print("\nRisk scoring complete!")


# =========================
# SUMMARY STATISTICS
# =========================
"""
We count how many claims fall into each risk category.

Generator expression:
sum(1 for r in risk_results if condition)

This means:
→ loop through all results
→ count how many satisfy the condition
"""

high = sum(1 for r in risk_results if r["risk_level"] == "HIGH")
medium = sum(1 for r in risk_results if r["risk_level"] == "MEDIUM")
low = sum(1 for r in risk_results if r["risk_level"] == "LOW")


# =========================
# DISPLAY HIGH RISK CASES
# =========================
print("\nHIGH RISK CLAIMS:\n")

"""
We print only HIGH risk cases for quick inspection.

json.dumps(..., indent=2):
→ pretty-print dictionary as JSON
"""
for r in risk_results:
    if r["risk_level"] == "HIGH":
        print(json.dumps(r, indent=2))


# Print summary counts
print(f"HIGH risk: {high}")
print(f"MEDIUM risk: {medium}")
print(f"LOW risk: {low}")