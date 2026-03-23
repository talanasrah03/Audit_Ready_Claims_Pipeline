"""
This script creates a human review queue based on validation results.

Context in the project:
After extracting and validating claims, not all claims can be trusted automatically.
Some claims contain issues (missing data, invalid values, suspicious amounts).

This file identifies those problematic claims and prepares them for human review.

Main idea:
- If a claim is valid → it is NOT included here
- If a claim is invalid → it is added to a review queue
- Each claim gets:
  - a list of issues
  - a suggested action
  - a list of possible actions for the reviewer

This simulates a real-world workflow:
AI does initial processing → humans handle uncertain cases.

Input:
- data/processed/validated_claims.json

Output:
- data/processed/human_review_queue.json
"""


import json


# =========================
# LOAD VALIDATED CLAIMS
# =========================
"""
Each claim already contains a "validation" field like:

"validation": {
    "valid": False,
    "issues": ["Missing customer_name", "Amount too high"]
}

We use this information to decide which claims need human review.
"""
with open("data/processed/validated_claims.json", "r") as f:
    claims = json.load(f)


# =========================
# HUMAN REVIEW QUEUE
# =========================
"""
This list will store only the claims that need human intervention.

Each item in this list represents a "task" for a human reviewer.
"""
review_queue = []


# =========================
# HELPER FUNCTION: SUGGEST ACTION
# =========================
def suggest_action(issues):
    """
    This function determines what action should be suggested to the human reviewer,
    based on the type of issues detected during validation.

    Input:
    issues = list of strings describing problems

    Example:
    ["Missing customer_name", "Amount too high"]

    Output:
    A recommended action string

    Possible actions:
    - APPROVE        → data looks fine
    - REJECT         → claim is invalid
    - CORRECT        → fix incorrect values
    - REQUEST_INFO   → ask user for missing info
    - REVIEW         → unclear case, manual decision needed
    """

    # If there are no issues → everything is valid
    if not issues:
        return "APPROVE"


    # Check if ANY issue contains the word "Missing"
    """
    any(...) returns True if at least one element satisfies the condition.

    Example:
    issues = ["Missing customer_name", "Amount too high"]

    any("Missing" in issue for issue in issues)
    → True (because at least one issue contains "Missing")
    """
    if any("Missing" in issue for issue in issues):
        return "REQUEST_INFO"


    # Check for abnormal amounts
    """
    This detects financial anomalies.

    Example issues:
    "Amount too low"
    "Amount too high"
    """
    if any("too low" in issue or "too high" in issue for issue in issues):
        return "REVIEW_AMOUNT"


    # Check for invalid fields
    """
    Example:
    "Invalid claim_type"
    "Invalid date format"
    """
    if any("Invalid" in issue for issue in issues):
        return "CORRECT"


    # Default fallback
    """
    If none of the above rules match,
    we send the claim for general review.
    """
    return "REVIEW"


# =========================
# BUILD REVIEW QUEUE
# =========================
"""
We iterate through all claims and select only those that failed validation.

Process:
1. Get validation info
2. Check if claim is valid
3. If NOT valid → add to review queue
"""
for claim in claims:

    # Get validation object safely (default empty dict if missing)
    validation = claim.get("validation", {})

    # Only process claims that are NOT valid
    if not validation.get("valid"):

        # Extract issues list
        issues = validation.get("issues", [])

        # Create a review task
        review_queue.append({

            # Unique identifier of the claim
            "doc_id": claim["doc_id"],

            # List of issues found during validation
            "issues": issues,

            # Initial status of the review task
            "status": "PENDING_REVIEW",

            # Automatically suggested action based on rules
            "recommended_action": suggest_action(issues),

            # List of all possible actions the human can take
            """
            These options will later be used in the UI (app.py).

            Meaning:
            APPROVE        → accept claim as is
            REJECT         → discard claim
            CORRECT        → manually edit fields
            REQUEST_INFO   → ask customer for more data
            """
            "possible_actions": [
                "APPROVE",
                "REJECT",
                "CORRECT",
                "REQUEST_INFO"
            ]
        })


# =========================
# SAVE REVIEW QUEUE
# =========================
"""
We store the review queue as a JSON file.

Each entry represents one claim requiring human decision.
"""
with open("data/processed/human_review_queue.json", "w") as f:
    json.dump(review_queue, f, indent=2)


# =========================
# FINAL OUTPUT
# =========================
"""
len(review_queue):
= number of claims requiring human intervention

Example:
If 1000 claims total and 150 invalid
→ review_queue size = 150
"""
print(f"Human review queue created: {len(review_queue)} claims need review")