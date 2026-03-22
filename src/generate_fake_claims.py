import pandas as pd
import random
import json
import os

# Load dataset
df = pd.read_csv("data/insurance_claims.csv")

# Create output folders
os.makedirs("raw_claims", exist_ok=True)
os.makedirs("ground_truth", exist_ok=True)

# Fake names
fake_names = [
    "John Doe", "Alice Smith", "Michael Brown", "Sara Johnson",
    "David Wilson", "Emma Davis", "Daniel Garcia", "Sophia Martinez"
]

def generate_messy_text(row, claim_id, customer_name):
    claim_date = str(row.get("incident_date", "unknown"))
    amount = str(row.get("total_claim_amount", "unknown"))
    description = str(row.get("incident_type", "unknown"))

    include_claim_id = random.random() < 0.5  # 50% chance

    if include_claim_id:
        templates = [
            f"Hello, my name is {customer_name}. I want to report a claim. Claim ID is {claim_id}. The incident happened on {claim_date}. The amount is about {amount}. It was related to {description}.",
            
            f"hi this is {customer_name}, I had an issue on {claim_date}. claim number {claim_id}. expected damage around {amount}. type: {description}",
            
            f"Customer {customer_name} reported an incident on {claim_date}. Claim ref: {claim_id}. Estimated amount: {amount}. Description: {description}.",
            
            f"hey, {customer_name} here. My claim {claim_id}. happened on {claim_date}. cost is around {amount}. problem type was {description}"
        ]
    else:
        templates = [
            f"Hello, my name is {customer_name}. I want to report a claim. The incident happened on {claim_date}. The amount is about {amount}. It was related to {description}.",
            
            f"hi this is {customer_name}, I had an issue on {claim_date}. expected damage around {amount}. type: {description}",
            
            f"Customer {customer_name} reported an incident on {claim_date}. Estimated amount: {amount}. Description: {description}.",
            
            f"hey, {customer_name} here. happened on {claim_date}. cost is around {amount}. problem type was {description}"
        ]

    return random.choice(templates)

messy_claims = []
ground_truth = []

# 🔥 USE FULL DATASET
for i, (_, row) in enumerate(df.iterrows(), start=1):
    claim_id = f"CLM-{1000 + i}"
    customer_name = random.choice(fake_names)

    raw_text = generate_messy_text(row, claim_id, customer_name)

    claim_date = str(row.get("incident_date", "unknown"))
    amount = str(row.get("total_claim_amount", "unknown"))
    claim_type = str(row.get("incident_type", "unknown"))

    messy_claims.append({
        "doc_id": f"claim_{i}",
        "raw_text": raw_text
    })

    ground_truth.append({
        "doc_id": f"claim_{i}",
        "claim_id": claim_id,
        "customer_name": customer_name,
        "claim_date": claim_date,
        "claim_type": claim_type,
        "amount": amount
    })

# Save files
with open("raw_claims/messy_claims.json", "w", encoding="utf-8") as f:
    json.dump(messy_claims, f, indent=2, ensure_ascii=False)

with open("ground_truth/ground_truth.json", "w", encoding="utf-8") as f:
    json.dump(ground_truth, f, indent=2, ensure_ascii=False)

print(f"✅ Generated {len(messy_claims)} messy claims!")