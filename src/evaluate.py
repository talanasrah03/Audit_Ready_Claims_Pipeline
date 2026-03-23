import json

print("USING FILE: cleaned_claims.json")

# =========================
# LOAD DATA (✅ FIXED)
# =========================
with open("data/processed/cleaned_claims.json", "r", encoding="utf-8") as f:
    predictions = json.load(f)

with open("data/ground_truth/ground_truth.json", "r", encoding="utf-8") as f:
    ground_truth = json.load(f)

# =========================
# DEBUG SAMPLE
# =========================
print("\n--- DEBUG SAMPLE ---")
print("PREDICTION SAMPLE:", predictions[0])
print("GROUND TRUTH SAMPLE:", ground_truth[0])
print("---------------------\n")

# =========================
# LOOKUP
# =========================
gt_dict = {item["doc_id"]: item for item in ground_truth}

correct_counts = {
    "customer_name": 0,
    "claim_date": 0,
    "claim_type": 0,
    "amount": 0
}

errors = []
valid_samples = 0

# =========================
# NORMALIZATION
# =========================
def normalize_text(value):
    if value is None:
        return None
    return str(value).strip().lower()

def normalize_amount(value):
    try:
        return int(value)
    except:
        return None

# =========================
# COMPARE
# =========================
for pred in predictions:
    doc_id = pred.get("doc_id")
    gt = gt_dict.get(doc_id)

    if not gt:
        continue

    valid_samples += 1

    # TEXT FIELDS
    for field in ["customer_name", "claim_date", "claim_type"]:
        pred_val = normalize_text(pred.get(field))
        gt_val = normalize_text(gt.get(field))

        if pred_val == gt_val:
            correct_counts[field] += 1
        else:
            errors.append({
                "doc_id": doc_id,
                "field": field,
                "predicted": pred_val,
                "expected": gt_val
            })

    # AMOUNT (STRICT NUMERIC)
    pred_amount = normalize_amount(pred.get("amount"))
    gt_amount = normalize_amount(gt.get("amount"))

    if pred_amount == gt_amount:
        correct_counts["amount"] += 1
    else:
        errors.append({
            "doc_id": doc_id,
            "field": "amount",
            "predicted": pred_amount,
            "expected": gt_amount
        })

# =========================
# RESULTS
# =========================
print("\n📊 EVALUATION RESULTS\n")

for field, count in correct_counts.items():
    accuracy = (count / valid_samples) * 100 if valid_samples else 0
    print(f"{field}: {accuracy:.2f}%")

overall = sum(correct_counts.values()) / (valid_samples * len(correct_counts)) * 100 if valid_samples else 0
print(f"\n🔥 Overall accuracy: {overall:.2f}%")

print(f"\n❌ Total errors: {len(errors)}")
print(f"\n📦 Total samples evaluated: {valid_samples}")

# =========================
# SAMPLE ERRORS
# =========================
print("\n--- SAMPLE ERRORS ---")
for err in errors[:5]:
    print(err)
print("----------------------\n")

# =========================
# SAVE ERRORS
# =========================
with open("data/processed/errors.json", "w", encoding="utf-8") as f:
    json.dump(errors, f, indent=2, ensure_ascii=False)