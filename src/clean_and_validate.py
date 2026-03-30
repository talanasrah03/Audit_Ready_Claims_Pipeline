"""
Data cleaning module (SAFE MODE).

Goal:
Prepare extracted claim data for validation while preserving original information.

What this script does:
- Reads extracted claims from AI output
- Keeps most fields unchanged (to avoid data loss)
- Cleans the "amount" field into a usable numeric format
- Preserves domain information
- Outputs a cleaned dataset for downstream processing

Important concept:
SAFE MODE cleaning:
→ Minimal transformation
→ Avoid aggressive modifications
→ Reduce risk of corrupting data

Example:
Input:
"amount": "€1,200 approx."

Output:
"amount": 1200
"""

import json   # Used to read and write structured data (JSON files)
import re     # Used to extract numeric values from messy text using regular expressions


# =========================
# LOAD EXTRACTED CLAIMS
# =========================
"""
Goal:
Load raw extracted data produced by the AI system.

Logic:
- Open the JSON file
- Convert it into Python objects (a list of dictionaries)

Example:
[
    {"amount": "€1200"},
    {"amount": "about 3000 euros"}
]
"""

with open("data/processed/extracted_claims_v3.json", "r") as f:
    claims = json.load(f)


# =========================
# INITIALIZE CLEANED LIST
# =========================
"""
Goal:
Prepare a new list to store cleaned claims.

Logic:
- Each processed claim will be added to this list
- At the end, this list will be saved as the cleaned output file

Example:
cleaned = [cleaned_claim_1, cleaned_claim_2]
"""

cleaned = []


# =========================
# PROCESS EACH CLAIM
# =========================
"""
Goal:
Iterate through each claim and clean it.

Logic:
- Copy important fields as they are
- Clean only the "amount" field
- Preserve domain (with fallback if missing)

Important:
We avoid modifying text fields to reduce the risk of losing useful information.
"""

for claim in claims:

    # =========================
    # CREATE CLEAN STRUCTURE
    # =========================
    """
    Goal:
    Build a cleaned version of the claim.

    Logic:
    - Copy fields safely using .get()
    - Set default values where needed

    Important:
    .get("field") means:
    - return the field value if it exists
    - return None if it does not exist

    This is safer than direct access with claim["field"],
    which would raise an error if the field is missing.

    Default domain:
    If domain is missing, fallback to "vehicle"
    so the cleaned data stays compatible with the rest of the system.

    Example:
    If domain is missing
    → use "vehicle"
    """

    cleaned_claim = {
        "doc_id": claim.get("doc_id"),
        "claim_id": claim.get("claim_id"),
        "customer_name": claim.get("customer_name"),
        "claim_date": claim.get("claim_date"),
        "claim_type": claim.get("claim_type"),
        "domain": claim.get("domain", "vehicle"),
        "amount": None
    }


    # =========================
    # CLEAN AMOUNT FIELD
    # =========================
    """
    Goal:
    Extract a usable numeric amount from messy text.

    Problem:
    AI outputs may contain values such as:
    - "€1200"
    - "1,200 euros"
    - "approx. 3000"
    - "around 500"

    These values are not directly usable as plain numbers.

    Logic:
    1. Convert the value to text
    2. Extract all digit sequences using regex
    3. Join them into one number
    4. Convert that result to integer

    Regex:
    r"\d+"
    → finds all groups of digits

    Example:
    "€1,200 approx." → ["1", "200"] → "1200" → 1200

    Limitation:
    - Does not handle decimals correctly
      Example: 1200.50 → becomes 120050
    - This is acceptable here because SAFE MODE uses simple cleaning only
    """

    value = claim.get("amount")

    """
    Important:
    This condition runs only if value is not empty-like.

    That means it skips values such as:
    - None
    - ""
    - 0

    In this project, amount = 0 is unlikely to be a valid real claim amount,
    so this behavior is acceptable.
    """
    if value:

        # Extract all numeric parts from the text
        numbers = re.findall(r"\d+", str(value))

        if numbers:
            """
            Join all extracted number parts and convert the result to an integer.

            Example:
            ["1", "200"] → "1200" → 1200
            """

            cleaned_claim["amount"] = int("".join(numbers))


    # Add cleaned claim to the final list
    cleaned.append(cleaned_claim)


# =========================
# SAVE CLEANED DATA
# =========================
"""
Goal:
Save the cleaned dataset for the next steps of the pipeline.

Logic:
- Convert the Python list into JSON
- Write it into a new file

indent=2:
→ formats the file with spacing
→ makes it easier for humans to read

Example output file:
data/processed/cleaned_claims.json
"""

with open("data/processed/cleaned_claims.json", "w") as f:
    json.dump(cleaned, f, indent=2)


# =========================
# FINAL CONFIRMATION
# =========================
"""
Goal:
Confirm that the cleaning process finished successfully.

Example:
Console output:
"Cleaning complete (SAFE MODE)"
"""

print("Cleaning complete (SAFE MODE)")