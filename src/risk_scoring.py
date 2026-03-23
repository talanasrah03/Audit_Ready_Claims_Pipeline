import json

# =========================
# LOAD DATA
# =========================
with open("data/processed/cleaned_claims.json", "r", encoding="utf-8") as f:
    predictions = json.load(f)

with open("data/ground_truth/ground_truth.json", "r", encoding="utf-8") as f:
    ground_truth = json.load(f)

gt_dict = {item["doc_id"]: item for item in ground_truth}

risk_results = []

# =========================
# RISK RULES
# =========================
for pred in predictions:
    doc_id = pred["doc_id"]
    gt = gt_dict.get(doc_id)

    if not gt:
        continue

    risk_score = 0
    reasons = []

    # 🔴 Missing claim_type
    if pred.get("claim_type") is None:
        risk_score += 2
        reasons.append("Missing claim_type")

    # 🔴 Missing amount
    if pred.get("amount") is None:
        risk_score += 2
        reasons.append("Missing amount")

    # 🔴 Amount mismatch (big difference)
    try:
        pred_amount = int(pred.get("amount"))
        gt_amount = int(gt.get("amount"))

        if abs(pred_amount - gt_amount) > 5000:
            risk_score += 3
            reasons.append("Large amount mismatch")

    except:
        pass

    # 🔴 Claim type mismatch
    if str(pred.get("claim_type")).lower() != str(gt.get("claim_type")).lower():
        risk_score += 2
        reasons.append("Claim type mismatch")

    # =========================
    # CLASSIFICATION
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
# SAVE RESULTS
# =========================
with open("data/processed/risk_scores.json", "w", encoding="utf-8") as f:
    json.dump(risk_results, f, indent=2, ensure_ascii=False)

print("\n🚨 Risk scoring complete!")

# =========================
# SUMMARY
# =========================
high = sum(1 for r in risk_results if r["risk_level"] == "HIGH")
medium = sum(1 for r in risk_results if r["risk_level"] == "MEDIUM")
low = sum(1 for r in risk_results if r["risk_level"] == "LOW")


# =========================
# SHOW HIGH RISK CASES
# =========================

print("\n🚨 HIGH RISK CLAIMS:\n")

for r in risk_results:
    if r["risk_level"] == "HIGH":
        print(json.dumps(r, indent=2))
print(f"HIGH risk: {high}")
print(f"MEDIUM risk: {medium}")
print(f"LOW risk: {low}")