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
- choose a random customer name
- choose a random claim type
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


# ---------------------------
# CONFIGURATION
# ---------------------------
"""
NUM_CLAIMS determines how many fake claims will be generated.

Example:
If NUM_CLAIMS = 1000
→ the loop will create 1000 raw claims
→ and 1000 matching ground truth records
"""
NUM_CLAIMS = 1000


# List of possible fake customer names.
# For each claim, one name will be selected randomly.
names = [
    "Emma Davis", "Michael Brown", "Alice Smith",
    "David Wilson", "Daniel Garcia", "Sara Johnson",
    "Sophia Martinez", "John Doe"
]


# List of allowed insurance claim categories.
# These are the same types the extraction model is expected to recognize later.
claim_types = [
    "Single Vehicle Collision",
    "Multi-vehicle Collision",
    "Vehicle Theft",
    "Parked Car"
]


# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def random_date():
    """
    Generate a random date starting from 2015-01-01.

    How it works:
    1. start_date is fixed as January 1, 2015
    2. random.randint(0, 60) chooses a random number of days
       between 0 and 60 inclusive
    3. timedelta(days=...) adds that many days to the start date
    4. strftime("%Y-%m-%d") formats the final date as text

    Example:
    datetime(2015, 1, 1) + 12 days
    → 2015-01-13

    Format explanation:
    %Y = 4-digit year
    %m = 2-digit month
    %d = 2-digit day

    So the final format looks like:
    2015-01-13
    """
    start_date = datetime(2015, 1, 1)
    return (start_date + timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d")


def generate_claim_id(i):
    """
    Create a claim ID based on the loop number.

    Example:
    if i = 1
    → claim ID becomes CLM-1001

    if i = 25
    → claim ID becomes CLM-1025

    Why use 1000 + i?
    It makes IDs look more realistic than starting at CLM-1.
    """
    return f"CLM-{1000 + i}"


# ---------------------------
# MESSY TEXT TEMPLATES
# ---------------------------
"""
These templates simulate how claim information may appear in real life:
- informal wording
- incomplete grammar
- uncertainty
- inconsistent phrasing

This is important because real documents are usually not perfectly structured.

Each template contains placeholders like:
{name}, {date}, {claim_id}, {amount}, {claim_type}

Later, those placeholders will be replaced with randomly generated values.
"""
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
"""
These two lists will collect all generated data before saving it to files.

raw_claims:
- messy text only
- used as input to the AI extraction pipeline

ground_truth:
- correct structured values
- used later for evaluation
"""
raw_claims = []
ground_truth = []


# ---------------------------
# MAIN GENERATION LOOP
# ---------------------------
"""
range(1, NUM_CLAIMS + 1) means:
- start at 1
- stop at NUM_CLAIMS
- include the final number

Example:
If NUM_CLAIMS = 3
→ i will be: 1, 2, 3

For each iteration, we create one full fake claim.
"""
for i in range(1, NUM_CLAIMS + 1):

    # Select one random name from the names list
    name = random.choice(names)

    # Select one random claim type from the claim_types list
    claim_type = random.choice(claim_types)

    # Generate one random date
    date = random_date()

    # Generate a unique claim ID based on the loop number
    claim_id = generate_claim_id(i)

    # Generate a random amount between 2000 and 100000
    """
    random.randint(2000, 100000) returns an integer between
    2000 and 100000 inclusive.

    Example possible values:
    2540
    17890
    99999
    """
    amount = random.randint(2000, 100000)


    # ---------------------------
    # TRUE VALUE FOR EVALUATION
    # ---------------------------
    """
    true_amount stores the correct amount as a string.

    Why store it as a string?
    Because JSON often stores extracted values as text,
    and later processing can decide whether to convert it to integer.

    This is the correct value that goes into ground truth.
    """
    true_amount = str(amount)


    # ---------------------------
    # INTRODUCE NOISE INTO RAW TEXT
    # ---------------------------
    """
    noisy_amount starts equal to the true amount,
    but sometimes we intentionally change it.

    Why do this?
    To make the raw text less perfect and more realistic.

    The model later has to deal with imperfect data,
    just like in a real-world claims system.
    """
    noisy_amount = amount

    if random.random() < 0.3:
        """
        random.random() returns a decimal number between 0 and 1.

        Example possible values:
        0.12
        0.87
        0.29

        Condition:
        random.random() < 0.3

        This means about 30% of the time,
        we modify the amount in the raw text.

        random.randint(-5000, 5000) adds or subtracts up to 5000.

        Example:
        true amount = 20000
        noise = -1200
        noisy amount = 18800

        This creates mismatch between:
        - what appears in raw text
        - what is stored as correct ground truth

        That makes the extraction/evaluation task more challenging.
        """
        noisy_amount = amount + random.randint(-5000, 5000)


    # Choose one messy text template randomly
    template = random.choice(templates)


    # ---------------------------
    # BUILD RAW TEXT
    # ---------------------------
    """
    template.format(...) replaces the placeholders in the chosen template
    with actual values for this claim.

    Example template:
    "report: {claim_type} involving {name}, date {date}, est loss {amount}, claim ref {claim_id}"

    After formatting:
    "report: Vehicle Theft involving Emma Davis, date 2015-01-13, est loss 4500, claim ref CLM-1001"
    """
    raw_text = template.format(
        name=name,
        date=date,
        claim_id=claim_id,
        amount=noisy_amount,
        claim_type=claim_type
    )


    # ---------------------------
    # SAVE RAW CLAIM
    # ---------------------------
    """
    This is the messy version that the AI system will read later.

    doc_id:
    - unique internal identifier for the document
    - used later to match predictions with ground truth

    raw_text:
    - the messy text version of the claim
    """
    raw_claims.append({
        "doc_id": f"claim_{i}",
        "raw_text": raw_text
    })


    # ---------------------------
    # SAVE GROUND TRUTH
    # ---------------------------
    """
    This is the correct structured version of the same claim.

    Important:
    The ground truth uses the TRUE amount, not the noisy one.

    This means:
    - raw input may be messy or partially misleading
    - evaluation still compares against the intended correct answer
    """
    ground_truth.append({
        "doc_id": f"claim_{i}",
        "claim_id": claim_id,
        "customer_name": name,
        "claim_date": date,
        "claim_type": claim_type,
        "amount": true_amount
    })


# ---------------------------
# CREATE OUTPUT FOLDERS
# ---------------------------
"""
os.makedirs(folder, exist_ok=True) creates folders if they do not exist.

exist_ok=True means:
- if folder already exists, do not raise an error
- this makes the script safe to rerun
"""
os.makedirs("raw_claims", exist_ok=True)
os.makedirs("ground_truth", exist_ok=True)


# ---------------------------
# SAVE JSON FILES
# ---------------------------
"""
json.dump writes Python data into a JSON file.

indent=2 makes the file easier to read manually.
"""

with open("raw_claims/raw_claims.json", "w", encoding="utf-8") as f:
    json.dump(raw_claims, f, indent=2)

with open("ground_truth/ground_truth.json", "w", encoding="utf-8") as f:
    json.dump(ground_truth, f, indent=2)


# ---------------------------
# FINAL MESSAGE
# ---------------------------
print(f"Generated {NUM_CLAIMS} messy realistic claims!")