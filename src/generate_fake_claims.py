"""
This script generates a synthetic insurance claims dataset for the project.

Main purpose:
Create two JSON files:

1. raw_claims.json
   - contains messy, human-like insurance claim text
   - simulates how real users might write claims in an inconsistent way

2. ground_truth.json
   - contains the correct structured values for each claim
   - used later to evaluate how accurate the AI extraction pipeline is

Why this file is important:
The project needs realistic input data, but also needs a trusted reference
to compare predictions against. This script creates both at the same time.

General idea:
For each fake claim:
- choose a random domain
- choose a random customer name
- choose a random claim type from that domain
- generate a date
- generate a claim ID
- generate an amount
- place all of that into a messy text template
- save the clean values separately as the ground truth

This creates a controlled testing environment:
- the raw text is messy and imperfect
- the correct answer is still known exactly
"""

import json
import random
import os
from datetime import datetime, timedelta
from src.config.config import CONFIGS


# ---------------------------
# CONFIGURATION
# ---------------------------
NUM_CLAIMS = 1000


# List of possible fake customer names.
names = [
    "Emma Davis", "Michael Brown", "Alice Smith",
    "David Wilson", "Daniel Garcia", "Sara Johnson",
    "Sophia Martinez", "John Doe"
]

# Available domains in the system.
domains = list(CONFIGS.keys())


# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def random_date():
    """
    Generate a random date starting from 2015-01-01.
    """
    start_date = datetime(2015, 1, 1)
    return (start_date + timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d")


def generate_claim_id(i):
    """
    Create a realistic claim ID based on the loop number.
    """
    return f"CLM-{1000 + i}"


# ---------------------------
# MESSY TEXT TEMPLATES
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
# OUTPUT CONTAINERS
# ---------------------------
raw_claims = []
ground_truth = []


# ---------------------------
# MAIN GENERATION LOOP
# ---------------------------
for i in range(1, NUM_CLAIMS + 1):
    # Select one random domain
    domain = random.choice(domains)

    # Select one random name
    name = random.choice(names)

    # Select one random claim type from the selected domain
    claim_type = random.choice(CONFIGS[domain]["claim_types"])

    # Generate other values
    date = random_date()
    claim_id = generate_claim_id(i)
    amount = random.randint(2000, 100000)
    true_amount = str(amount)

    # Add some noise to raw text amount
    noisy_amount = amount
    if random.random() < 0.3:
        noisy_amount = amount + random.randint(-5000, 5000)

    # Choose one template
    template = random.choice(templates)

    # Build messy raw text
    raw_text = template.format(
        name=name,
        date=date,
        claim_id=claim_id,
        amount=noisy_amount,
        claim_type=claim_type
    )

    # Save raw claim
    raw_claims.append({
        "doc_id": f"claim_{i}",
        "raw_text": raw_text,
        "domain": domain
    })

    # Save ground truth
    ground_truth.append({
        "doc_id": f"claim_{i}",
        "claim_id": claim_id,
        "customer_name": name,
        "claim_date": date,
        "claim_type": claim_type,
        "amount": true_amount,
        "domain": domain
    })


# ---------------------------
# CREATE OUTPUT FOLDERS
# ---------------------------
os.makedirs("raw_claims", exist_ok=True)
os.makedirs("ground_truth", exist_ok=True)


# ---------------------------
# SAVE JSON FILES
# ---------------------------
with open("raw_claims/raw_claims.json", "w", encoding="utf-8") as f:
    json.dump(raw_claims, f, indent=2)

with open("ground_truth/ground_truth.json", "w", encoding="utf-8") as f:
    json.dump(ground_truth, f, indent=2)


# ---------------------------
# FINAL MESSAGE
# ---------------------------
print(f"Generated {NUM_CLAIMS} messy realistic claims!")