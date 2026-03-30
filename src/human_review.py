"""
Human review queue module.

Goal:
Create a list of claims that need manual review after validation.

Context in the project:
After extraction and validation, not all claims can be trusted automatically.
Some claims contain issues such as:
- missing fields
- invalid values
- suspicious amounts

This file identifies those problematic claims and prepares them for human review.

Main idea:
- If a claim is valid → it is NOT included here
- If a claim is invalid → it is added to the review queue
- Each review item contains:
  - a list of issues
  - a suggested action
  - a list of actions the reviewer can choose from

This simulates a real-world workflow:
AI does the first screening
→ humans handle uncertain or problematic cases

Input:
- data/processed/validated_claims.json

Output:
- data/processed/human_review_queue.json
"""

import json   # Used to load validated claims and save the final review queue


# =========================
# LOAD VALIDATED CLAIMS
# =========================
"""
Goal:
Load claims that have already been validated by the system.

Each claim contains a structure like:

"validation": {
    "valid": False,
    "issues": ["Missing customer_name", "Amount too high"]
}

We use this validation data to decide:
→ which claims need human intervention
"""

with open("data/processed/validated_claims.json", "r") as f:
    claims = json.load(f)


# =========================
# HUMAN REVIEW QUEUE
# =========================
"""
Goal:
Store only claims that require human review.

Logic:
- Each item added to this list becomes one review task
- Later, this list can be shown in the internal dashboard

Example:
One entry in review_queue = one claim waiting for human decision
"""

review_queue = []


# =========================
# HELPER FUNCTION: SUGGEST ACTION
# =========================
def suggest_action(issues):
    """
    Goal:
    Recommend an action for the human reviewer based on detected issues.

    Logic:
    - Look at the type of issues found during validation
    - Return the most suitable suggested action

    Example:
    ["Missing customer_name", "Amount too high"]
    → REQUEST_INFO

    Why?
    Because missing required information usually means
    the reviewer or customer must provide more data first.

    Possible outputs:
    - APPROVE
    - REJECT
    - CORRECT
    - REQUEST_INFO
    - REVIEW
    - REVIEW_AMOUNT

    Important:
    Some outputs are internal recommendations only.
    For example:
    REVIEW_AMOUNT means "this looks suspicious and needs financial review",
    but the final UI may still present only standard actions such as:
    APPROVE / REJECT / CORRECT / REQUEST_INFO
    """

    # =========================
    # NO ISSUES
    # =========================
    """
    If there are no issues:
    → the claim looks valid
    → recommended action = APPROVE
    """

    if not issues:
        return "APPROVE"


    # =========================
    # MISSING DATA
    # =========================
    """
    Goal:
    Detect missing required information.

    any(...) explanation:
    any(condition for element in list)
    → returns True if at least one element matches the condition

    Example:
    issues = ["Missing customer_name", "Amount too high"]

    any("Missing" in issue for issue in issues)
    → True
    """

    if any("Missing" in issue for issue in issues):
        return "REQUEST_INFO"


    # =========================
    # AMOUNT ANOMALIES
    # =========================
    """
    Goal:
    Detect suspicious amount-related issues.

    Example:
    "Amount too low"
    "Amount too high"

    Why a separate action?
    Because financial anomalies often deserve special attention.

    Important:
    REVIEW_AMOUNT is an internal recommendation.
    It signals that the issue is specifically financial,
    even if the final UI actions remain more general.
    """

    if any("too low" in issue or "too high" in issue for issue in issues):
        return "REVIEW_AMOUNT"


    # =========================
    # INVALID FIELDS
    # =========================
    """
    Goal:
    Detect fields that exist but contain invalid values.

    Example:
    "Invalid claim_type"
    "Invalid date format"

    In such cases, the most reasonable next step is often:
    → CORRECT
    """

    if any("Invalid" in issue for issue in issues):
        return "CORRECT"


    # =========================
    # DEFAULT CASE
    # =========================
    """
    If no specific rule matches:
    → use a general manual review recommendation
    """

    return "REVIEW"


# =========================
# BUILD REVIEW QUEUE
# =========================
"""
Goal:
Select only invalid claims and prepare them for human review.

Process:
1. Access validation data
2. Check whether claim is valid
3. If invalid → create review task
"""

for claim in claims:

    # =========================
    # SAFE ACCESS TO VALIDATION
    # =========================
    """
    claim.get("validation", {})

    Logic:
    - If "validation" exists → return it
    - If not → return empty dictionary {}

    Why important:
    This prevents the script from crashing if a claim has no validation field.

    Example:
    claim = {}
    → validation = {}
    """

    validation = claim.get("validation", {})


    # =========================
    # FILTER INVALID CLAIMS
    # =========================
    """
    validation.get("valid")

    Logic:
    - True  → claim is valid
    - False → claim is invalid
    - None  → treated as invalid in this condition

    Important:
    Missing "valid" field is treated as unsafe,
    so the claim is sent to review.
    """

    if not validation.get("valid"):


        # =========================
        # EXTRACT ISSUES
        # =========================
        """
        validation.get("issues", [])

        Logic:
        - If issues exist → use them
        - If not → use an empty list

        Why important:
        This avoids errors if the issues field is missing.
        """

        issues = validation.get("issues", [])


        # =========================
        # CREATE REVIEW TASK
        # =========================
        """
        Goal:
        Build one review item for the current invalid claim.

        Fields:
        - doc_id → identifies which claim to review
        - issues → explains what went wrong
        - status → initial workflow state
        - recommended_action → system suggestion
        - possible_actions → choices available to human reviewer

        Important:
        recommended_action is guidance from the system.
        possible_actions are the final actions the reviewer can choose from.
        These two are related, but not always identical.
        """

        review_queue.append({

            # Unique identifier of the claim
            "doc_id": claim["doc_id"],

            # Issues detected during validation
            "issues": issues,

            # Initial review state
            "status": "PENDING_REVIEW",

            # Suggested action based on validation issues
            "recommended_action": suggest_action(issues),

            # Actions available to the human reviewer
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
Goal:
Save the review queue to a JSON file.

Why important:
This file becomes the bridge between:
- automated validation
- human decision-making

indent=2:
→ makes the JSON easier for humans to read

Example:
{
  "doc_id": "claim_1"
}
"""

with open("data/processed/human_review_queue.json", "w") as f:
    json.dump(review_queue, f, indent=2)


# =========================
# FINAL OUTPUT
# =========================
"""
Goal:
Show how many claims require human review.

Example:
1000 total claims
150 invalid
→ 150 review tasks created
"""

print(f"Human review queue created: {len(review_queue)} claims need review")