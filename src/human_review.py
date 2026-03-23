import json

# =========================
# LOAD VALIDATED CLAIMS
# =========================
with open("data/processed/validated_claims.json", "r") as f:
    claims = json.load(f)

# =========================
# HUMAN REVIEW QUEUE
# =========================
review_queue = []

# =========================
# HELPER: DETERMINE ACTION
# =========================
def suggest_action(issues):
    if not issues:
        return "APPROVE"

    if any("Missing" in issue for issue in issues):
        return "REQUEST_INFO"

    if any("too low" in issue or "too high" in issue for issue in issues):
        return "REVIEW_AMOUNT"

    if any("Invalid" in issue for issue in issues):
        return "CORRECT"

    return "REVIEW"

# =========================
# BUILD REVIEW QUEUE
# =========================
for claim in claims:
    validation = claim.get("validation", {})

    if not validation.get("valid"):
        issues = validation.get("issues", [])

        review_queue.append({
            "doc_id": claim["doc_id"],
            "issues": issues,
            "status": "PENDING_REVIEW",
            "recommended_action": suggest_action(issues),
            "possible_actions": [
                "APPROVE",
                "REJECT",
                "CORRECT",
                "REQUEST_INFO"
            ]
        })

# =========================
# SAVE FILE
# =========================
with open("data/processed/human_review_queue.json", "w") as f:
    json.dump(review_queue, f, indent=2)

# =========================
# OUTPUT
# =========================
print(f"👤 Human review queue created: {len(review_queue)} claims need review")