"""
Risk scoring module.

Goal:
Assign a risk score to each claim based on:
- comparison with ground truth
- data quality issues (missing fields, mismatches)
- learned instability from past corrections

What this script does:
- Compares predicted values with correct reference values
- Adds risk points for each detected issue
- Generates an explainable list of reasons
- Assigns a final risk level (LOW, MEDIUM, HIGH)

Important concept:
Risk is cumulative.

This means:
→ each problem adds points
→ more points = more risk

Example:
Missing amount (+2)
Wrong claim_type (+2)
→ total score = 4
→ final level = HIGH
"""

import json   # Used to read input files and save risk results as JSON
from src.learning.correction_memory import get_pattern_summary   # Retrieves learned correction patterns to estimate field reliability


# =========================
# HELPER FUNCTIONS
# =========================
def is_missing(value):
    """
    Goal:
    Check whether a value should be treated as missing.

    Logic:
    A value is treated as missing if it is:
    - None
    - an empty string
    - the text "none"
    - the text "null"

    Why important:
    AI outputs may represent missing data in different ways,
    not only as Python None.

    Example:
    value = None   → True
    value = ""     → True
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
    Convert a value to an integer safely.

    Logic:
    - Try to convert the value into an integer
    - If conversion fails, return None instead of crashing

    Why important:
    Predicted values may come in different formats,
    and some may not be valid numbers.

    Example:
    "1200"     → 1200
    1200       → 1200
    "1200 USD" → None
    "abc"      → None
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
→ cleaned AI outputs produced by the pipeline

ground_truth:
→ correct reference values used for evaluation and scoring

Why both are needed:
Risk scoring here is based on comparing:
- what the system predicted
- what the correct answer should be
"""

with open("data/processed/cleaned_claims.json", "r") as f:
    predictions = json.load(f)

with open("data/ground_truth/ground_truth.json", "r") as f:
    ground_truth = json.load(f)


# Convert ground truth list → dictionary for fast access
"""
Goal:
Create a lookup table for fast access to ground truth records.

Logic:
- Use doc_id as the key
- This avoids looping through the full ground_truth list every time

Example:
gt_dict["claim_1"]
→ instantly returns the matching ground truth record
"""

gt_dict = {item["doc_id"]: item for item in ground_truth}


# =========================
# LOAD LEARNING PATTERNS
# =========================
"""
Goal:
Load correction-based instability patterns from past human feedback.

Example:
{
    "amount_corrections": 8,
    "type_corrections": 3
}

Meaning:
- amount has often been corrected by humans
- claim_type has also been corrected, but less often

Why important:
If a field has been corrected many times in the past,
the system treats that field as less reliable.
"""

patterns = get_pattern_summary()


# Store final risk results
risk_results = []


# =========================
# MAIN LOOP
# =========================
"""
Goal:
Compute a risk score for each claim.

Logic:
1. Find the matching ground truth record
2. Add risk points for each issue
3. Convert numeric score into LOW / MEDIUM / HIGH
4. Save the result
"""

for pred in predictions:

    doc_id = pred["doc_id"]

    # Get corresponding ground truth
    gt = gt_dict.get(doc_id)

    """
    If no matching ground truth exists:
    → skip this claim

    Why:
    This version of risk scoring depends on comparison with the correct answer.
    Without ground truth, mismatch-based scoring cannot be computed safely.
    """
    if not gt:
        continue


    # =========================
    # INITIALIZE RISK
    # =========================
    """
    Goal:
    Start a fresh score for the current claim.

    risk_score:
    → numeric total that starts at 0

    reasons:
    → list of human-readable explanations
    """

    risk_score = 0
    reasons = []


    # =========================
    # MISSING FIELDS
    # =========================
    """
    Goal:
    Penalize important missing fields.

    Logic:
    Each missing field adds +2 points.

    Why important:
    Missing core information makes a claim less reliable.

    Example:
    missing claim_type → +2
    missing amount     → +2
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
    Goal:
    Detect large numeric difference between prediction and ground truth.

    Logic:
    - Convert both values to integers
    - Compare the absolute difference
    - If the difference is greater than 5000 → add risk

    Why absolute difference?
    Because only the size of the mismatch matters here,
    not whether the prediction is higher or lower.

    Example:
    predicted = 10000
    ground truth = 3000
    difference = 7000
    → add +3 risk points
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
    Goal:
    Detect mismatched claim types.

    Logic:
    - Compare predicted claim_type with ground truth claim_type
    - Convert both to lowercase first
      so simple capitalization differences do not count as errors

    Example:
    "Vehicle Theft" vs "vehicle theft"
    → treated as the same

    "Vehicle Theft" vs "Parked Car"
    → mismatch
    """

    if not is_missing(pred.get("claim_type")):

        if str(pred.get("claim_type")).lower() != str(gt.get("claim_type")).lower():
            risk_score += 2
            reasons.append("Claim type mismatch")


    # =========================
    # LEARNING EFFECT
    # =========================
    """
    Goal:
    Increase risk if past corrections show that a field is unstable.

    Logic:
    - If a field has been corrected many times before,
      the system assumes future values in that field are less reliable
    - Add additional risk points even if this specific claim looks okay

    Example:
    amount corrected > 5 times in the past
    → add +2 risk points
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
    Goal:
    Convert the numeric score into a category.

    Rules:
    - score ≥ 4 → HIGH
    - score ≥ 2 → MEDIUM
    - otherwise → LOW

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
    """
    Goal:
    Save the final risk result for this claim.

    Stored fields:
    - doc_id
    - risk_score
    - risk_level
    - reasons
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
"""
Goal:
Save the risk analysis results into a JSON file.

indent=2:
→ makes the file easier for humans to read
"""

with open("data/processed/risk_scores.json", "w") as f:
    json.dump(risk_results, f, indent=2)


print("Risk scoring complete!")