"""
This script evaluates the accuracy of the claims extraction pipeline.

Goal:
Compare the predicted (AI-extracted + cleaned) data with the ground truth (correct answers),
and compute accuracy metrics for each field.

What this script measures:
- How often each field is correct (customer_name, claim_date, claim_type, amount)
- Overall accuracy across all fields
- Detailed list of errors for debugging

Important concept:
Each claim has multiple fields → we evaluate each field independently.

Example:
If we have 100 claims and 4 fields per claim:
→ total comparisons = 100 × 4 = 400 comparisons
"""

import json


print("USING FILE: cleaned_claims.json")


# =========================
# LOAD DATA
# =========================
# Load predicted claims (output of your pipeline)
with open("data/processed/cleaned_claims.json", "r", encoding="utf-8") as f:
    predictions = json.load(f)

# Load ground truth (correct expected values)
with open("data/ground_truth/ground_truth.json", "r", encoding="utf-8") as f:
    ground_truth = json.load(f)


# =========================
# DEBUG SAMPLE
# =========================
# Print one example to verify structure manually
print("\n--- DEBUG SAMPLE ---")
print("PREDICTION SAMPLE:", predictions[0])
print("GROUND TRUTH SAMPLE:", ground_truth[0])
print("---------------------\n")


# =========================
# LOOKUP TABLE (IMPORTANT)
# =========================
# We convert ground_truth into a dictionary for FAST access

"""
Why do this?

Without this:
- We would need to loop through ALL ground_truth entries for each prediction
- That would be very slow (nested loops)

With this:
- We access ground truth instantly using doc_id

Structure:
gt_dict = {
    "doc_1": {...},
    "doc_2": {...},
}
"""
gt_dict = {item["doc_id"]: item for item in ground_truth}


# =========================
# METRIC VARIABLES
# =========================

"""
correct_counts keeps track of how many times each field was predicted correctly.

Example:
correct_counts["customer_name"] = 80
→ means 80 correct predictions for customer_name

valid_samples counts how many claims we successfully compared.
"""

correct_counts = {
    "customer_name": 0,
    "claim_date": 0,
    "claim_type": 0,
    "amount": 0
}

errors = []         # list of all mismatches (for debugging)
valid_samples = 0   # number of comparable claims


# =========================
# NORMALIZATION FUNCTIONS
# =========================

def normalize_text(value):
    """
    Normalize text to make comparison FAIR.

    Why needed?
    Because:
    "John Doe" != "john doe"
    " John Doe " != "John Doe"

    Steps:
    1. Convert to string
    2. Remove extra spaces (strip)
    3. Convert to lowercase

    Final result:
    All text is compared in a consistent format
    """
    if value is None:
        return None
    return str(value).strip().lower()


def normalize_amount(value):
    """
    Normalize numeric values.

    Why needed?
    Because sometimes numbers come as:
    - strings ("1200")
    - integers (1200)
    - or invalid values

    We try to convert everything into an integer.

    If it fails:
    → return None (invalid number)
    """
    try:
        return int(value)
    except:
        return None


# =========================
# MAIN COMPARISON LOOP
# =========================

"""
We now compare each predicted claim with its ground truth equivalent.

Step-by-step:
1. Take one predicted claim
2. Find its matching ground truth using doc_id
3. Compare each field separately
"""

for pred in predictions:

    doc_id = pred.get("doc_id")

    # Find corresponding ground truth entry
    gt = gt_dict.get(doc_id)

    # If no match → skip this claim
    if not gt:
        continue

    valid_samples += 1


    # =========================
    # TEXT FIELD COMPARISON
    # =========================
    """
    We compare 3 text fields:
    - customer_name
    - claim_date
    - claim_type

    For each field:
    - normalize both values
    - check if equal
    """

    for field in ["customer_name", "claim_date", "claim_type"]:

        pred_val = normalize_text(pred.get(field))
        gt_val = normalize_text(gt.get(field))

        if pred_val == gt_val:
            # Correct prediction → increment counter
            correct_counts[field] += 1
        else:
            # Incorrect → store full error details
            errors.append({
                "doc_id": doc_id,
                "field": field,
                "predicted": pred_val,
                "expected": gt_val
            })


    # =========================
    # AMOUNT COMPARISON (STRICT)
    # =========================
    """
    Amount is treated differently:
    - Must be EXACT match (no tolerance)
    - Compared as integers

    Example:
    1200 == 1200 → correct
    1200 != 1199 → incorrect
    """

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
# CALCULATE RESULTS
# =========================

print("\nEVALUATION RESULTS\n")

"""
Field accuracy formula:

accuracy = (number of correct predictions / total samples) × 100

Example:
customer_name:
= 80 correct / 100 samples × 100
= 80%
"""

for field, count in correct_counts.items():
    accuracy = (count / valid_samples) * 100 if valid_samples else 0
    print(f"{field}: {accuracy:.2f}%")


"""
Overall accuracy formula:

Step 1:
Sum all correct predictions across all fields

Step 2:
Total possible predictions = valid_samples × number_of_fields

Step 3:
overall_accuracy = (total_correct / total_possible) × 100

Example:
valid_samples = 100
fields = 4
→ total_possible = 100 × 4 = 400

if total_correct = 320
→ accuracy = 320 / 400 × 100 = 80%
"""

overall = (
    sum(correct_counts.values()) /
    (valid_samples * len(correct_counts))
    * 100
    if valid_samples else 0
)

print(f"\nOverall accuracy: {overall:.2f}%")

print(f"\nTotal errors: {len(errors)}")
print(f"\nTotal samples evaluated: {valid_samples}")


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
# Save all mismatches for deeper analysis later
with open("data/processed/errors.json", "w", encoding="utf-8") as f:
    json.dump(errors, f, indent=2, ensure_ascii=False)