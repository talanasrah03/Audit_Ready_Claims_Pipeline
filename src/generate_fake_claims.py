"""
Synthetic data generation module for insurance claims.

Goal:
Create a realistic dataset for testing the AI pipeline.

What this script does:
- Generates messy, human-like claim text (raw_claims.json)
- Generates correct structured values (ground_truth.json)

Important concept:
We simulate real-world conditions:
→ messy input (like real users)
→ perfect reference (for evaluation)

This allows us to:
- test extraction accuracy
- debug errors
- improve the pipeline safely

Example:
Raw text:
"hey it's John, something happened around 2023..."

Ground truth:
{
    "customer_name": "John",
    "amount": 5000
}
"""

import json   # Used to write generated claims and ground truth into JSON files
import random   # Used to randomly generate domains, names, claim types, dates, and noisy values
import os   # Used to create folders before saving output files
from datetime import datetime, timedelta   # Used to generate random dates
from src.config.config import CONFIGS   # Contains domain definitions and valid claim types


# ---------------------------
# CONFIGURATION
# ---------------------------
"""
Goal:
Define how many synthetic claims to generate.

Example:
NUM_CLAIMS = 1000
→ generate 1000 fake claims

Why important:
- More claims → stronger testing dataset
- Fewer claims → faster execution
"""

NUM_CLAIMS = 1000


# ---------------------------
# STATIC DATA
# ---------------------------
"""
Goal:
Define reusable data pools used during generation.

names:
→ list of fake customer names

domains:
→ list of domain names taken from CONFIGS

Why use CONFIGS here:
→ ensures generated claim types stay consistent with the rest of the system
→ avoids generating domain/claim-type combinations that the validation system would never expect
"""

names = [
    "Emma Davis", "Michael Brown", "Alice Smith",
    "David Wilson", "Daniel Garcia", "Sara Johnson",
    "Sophia Martinez", "John Doe"
]

domains = list(CONFIGS.keys())


# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def random_date():
    """
    Goal:
    Generate a random date as a string.

    Logic:
    - Start from a fixed base date: 2015-01-01
    - Add a random number of days
    - Convert the result into YYYY-MM-DD format

    random.randint(0, 60):
    → generates an integer between 0 and 60 (inclusive)

    Example:
    base date = 2015-01-01
    random offset = 10 days
    → result = 2015-01-11

    Important limitation:
    This currently generates dates only within about 2 months of the base date.
    That is enough for testing,
    but not very realistic for a wide historical dataset.
    """

    start_date = datetime(2015, 1, 1)

    return (
        start_date +
        timedelta(days=random.randint(0, 60))
    ).strftime("%Y-%m-%d")

    """
    strftime("%Y-%m-%d"):
    → formats the date as text

    Example:
    datetime object → "2015-01-11"
    """


def generate_claim_id(i):
    """
    Goal:
    Create a unique and realistic-looking claim ID.

    Logic:
    - Add a fixed prefix: "CLM"
    - Add a growing numeric part based on loop index

    Example:
    i = 1 → CLM-1001
    i = 2 → CLM-1002

    Why +1000:
    → makes IDs look more realistic than very small numbers like CLM-1
    """

    return f"CLM-{1000 + i}"


# ---------------------------
# MESSY TEXT TEMPLATES
# ---------------------------
"""
Goal:
Simulate the kind of inconsistent text a real person might write.

Logic:
- Each template contains placeholders
- Later, placeholders are replaced with generated values

Why important:
Real claims are often not clean or formal.
Users may:
- write casually
- omit information
- use vague wording
- mix formats

Example:
"umm hi, John. incident happened..."
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
Goal:
Store generated results before writing them to files.

raw_claims:
→ messy input text used by the extraction system

ground_truth:
→ correct structured reference values used later for evaluation
"""

raw_claims = []
ground_truth = []


# ---------------------------
# MAIN GENERATION LOOP
# ---------------------------
"""
Goal:
Generate NUM_CLAIMS synthetic claims.

Logic per iteration:
1. Choose a random domain
2. Choose a random name
3. Choose a valid claim type for that domain
4. Generate date, claim ID, and amount
5. Build messy raw text
6. Save:
   - noisy raw version
   - clean ground truth version

Why this is useful:
This creates a controlled test environment:
- inputs are messy
- correct answers are still known exactly
"""

for i in range(1, NUM_CLAIMS + 1):

    # ---------------------------
    # RANDOM SELECTION
    # ---------------------------
    """
    Goal:
    Randomly choose core values for this claim.

    random.choice(list):
    → selects one random item from a list

    Example:
    ["A", "B", "C"] → could return "B"
    """

    domain = random.choice(domains)
    name = random.choice(names)
    claim_type = random.choice(CONFIGS[domain]["claim_types"])


    # ---------------------------
    # VALUE GENERATION
    # ---------------------------
    """
    Goal:
    Generate additional claim fields.

    random.randint(2000, 100000):
    → generates a random integer in this range

    Example:
    54321

    true_amount:
    → stored as string to stay consistent with many extraction outputs
    """

    date = random_date()
    claim_id = generate_claim_id(i)
    amount = random.randint(2000, 100000)

    true_amount = str(amount)


    # ---------------------------
    # ADD NOISE
    # ---------------------------
    """
    Goal:
    Introduce controlled inconsistency into the raw text.

    Logic:
    - Start with the true amount
    - With 30% probability, change it slightly

    random.random():
    → returns a number between 0 and 1

    If result < 0.3:
    → apply noise

    Example:
    true amount = 5000
    noisy amount = 7000 or 3000

    Why important:
    This makes the raw claim text less perfect and more realistic.

    Important distinction:
    - noisy_amount goes into raw text
    - true_amount goes into ground_truth
    """

    noisy_amount = amount

    if random.random() < 0.3:
        noisy_amount = amount + random.randint(-5000, 5000)


    # ---------------------------
    # BUILD RAW TEXT
    # ---------------------------
    """
    Goal:
    Create a messy human-like claim sentence.

    Logic:
    - Pick one template at random
    - Replace placeholders with generated values

    template.format(...):
    → inserts real values into the template

    Example:
    "{name}" → "John Doe"
    """

    template = random.choice(templates)

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
    Goal:
    Save the messy version used as model input.

    Important:
    This record contains:
    - doc_id
    - raw_text
    - domain

    doc_id:
    → unique identifier used later for tracking and evaluation
    """

    raw_claims.append({
        "doc_id": f"claim_{i}",
        "raw_text": raw_text,
        "domain": domain
    })


    # ---------------------------
    # SAVE GROUND TRUTH
    # ---------------------------
    """
    Goal:
    Save the correct structured reference values.

    Important:
    ground_truth uses the clean / true values,
    not the noisy values inserted into raw_text.

    Why important:
    This allows the evaluation step to measure
    how close the extracted result is to the intended correct answer.
    """

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
"""
Goal:
Ensure the destination folders exist before saving files.

os.makedirs(..., exist_ok=True):
- create the folder if it does not exist
- do nothing if it already exists

Why important:
Without exist_ok=True,
the script could fail when rerun on an existing folder.
"""

os.makedirs("raw_claims", exist_ok=True)
os.makedirs("ground_truth", exist_ok=True)


# ---------------------------
# SAVE JSON FILES
# ---------------------------
"""
Goal:
Write generated data into JSON files.

Important:
These files are saved in:
- raw_claims/raw_claims.json
- ground_truth/ground_truth.json

indent=2:
→ formats JSON to be easier for humans to read
"""

with open("raw_claims/raw_claims.json", "w", encoding="utf-8") as f:
    json.dump(raw_claims, f, indent=2)

with open("ground_truth/ground_truth.json", "w", encoding="utf-8") as f:
    json.dump(ground_truth, f, indent=2)


# ---------------------------
# FINAL MESSAGE
# ---------------------------
"""
Goal:
Confirm that data generation finished successfully.

Example:
"Generated 1000 messy realistic claims!"
"""

print(f"Generated {NUM_CLAIMS} messy realistic claims!")