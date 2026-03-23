import json
import random
import os
from datetime import datetime, timedelta

# ---------------------------
# CONFIG
# ---------------------------
NUM_CLAIMS = 1000

names = [
    "Emma Davis", "Michael Brown", "Alice Smith",
    "David Wilson", "Daniel Garcia", "Sara Johnson",
    "Sophia Martinez", "John Doe"
]

claim_types = [
    "Single Vehicle Collision",
    "Multi-vehicle Collision",
    "Vehicle Theft",
    "Parked Car"
]

# ---------------------------
# HELPERS
# ---------------------------
def random_date():
    start_date = datetime(2015, 1, 1)
    return (start_date + timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d")


def generate_claim_id(i):
    return f"CLM-{1000 + i}"


# ---------------------------
# MESSY TEXT TEMPLATES (REALISTIC)
# ---------------------------
templates = [
    "hey it's {name}, something happened around {date}, not sure claim id maybe {claim_id}, damage like {amount}, was a {claim_type}",
    
    "customer {name} reported issue... date?? {date}, cost approx {amount}, type {claim_type}, ref maybe {claim_id}",
    
    "{name} here. accident few days back ({date}), not sure claim number but maybe {claim_id}, cost ~{amount}, {claim_type}",
    
    "umm hi, {name}. incident happened {date}, no idea about claim id, maybe {claim_id}, damage like {amount}",
    
    "report: {claim_type} involving {name}, date {date}, est loss {amount}, claim ref {claim_id}",
    
    "{name} had some issue, think it was {claim_type}, date {date}, amount around {amount}, id lost",
    
    "accident?? {claim_type} maybe. person: {name}. happened {date}. cost like {amount}. claim unknown",
    
    "{name} reported something messy... date {date}, approx cost {amount}, type unclear maybe {claim_type}"
]

# ---------------------------
# GENERATION
# ---------------------------
raw_claims = []
ground_truth = []

for i in range(1, NUM_CLAIMS + 1):
    name = random.choice(names)
    claim_type = random.choice(claim_types)
    date = random_date()
    claim_id = generate_claim_id(i)
    amount = random.randint(2000, 100000)

    # ✅ TRUE VALUE (ground truth)
    true_amount = str(amount)

    # ❗ Introduce noise in raw text sometimes
    noisy_amount = amount
    if random.random() < 0.3:
        noisy_amount = amount + random.randint(-5000, 5000)

    template = random.choice(templates)

    raw_text = template.format(
        name=name,
        date=date,
        claim_id=claim_id,
        amount=noisy_amount,
        claim_type=claim_type
    )

    # Raw claim (messy)
    raw_claims.append({
        "doc_id": f"claim_{i}",
        "raw_text": raw_text
    })

    # Ground truth (correct)
    ground_truth.append({
        "doc_id": f"claim_{i}",
        "claim_id": claim_id,
        "customer_name": name,
        "claim_date": date,
        "claim_type": claim_type,
        "amount": true_amount
    })

# ---------------------------
# SAVE FILES
# ---------------------------
os.makedirs("raw_claims", exist_ok=True)
os.makedirs("ground_truth", exist_ok=True)

with open("raw_claims/raw_claims.json", "w", encoding="utf-8") as f:
    json.dump(raw_claims, f, indent=2)

with open("ground_truth/ground_truth.json", "w", encoding="utf-8") as f:
    json.dump(ground_truth, f, indent=2)

print(f"✅ Generated {NUM_CLAIMS} messy realistic claims!")
