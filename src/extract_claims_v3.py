"""
This script is Version 3 (V3) of the claims extraction pipeline.

Main objective:
Process ALL claims using an AI model and extract structured data
in a scalable, stable, and production-like way.

Key improvements compared to previous versions:

V1:
- Basic extraction
- Small batch (testing only)

V2:
- Strict extraction rules
- Error recovery + noise simulation

V3 (this version):
- Full dataset processing (no slicing)
- Balanced prompt (not too strict, not too loose)
- Progress tracking (for long runs)
- Rate limiting protection (API safety)
- Simpler but stable error handling

Design philosophy:
Instead of being too strict (like V2),
we allow the model to make reasonable interpretations when needed.

This improves:
- completeness (fewer missing fields)
- usability of extracted data

Input:
- data/raw_claims/raw_claims.json

Output:
- data/processed/extracted_claims_v3.json
"""

import json
import re
import time  # Used to control execution speed (rate limiting)
from openai import OpenAI


# Initialize OpenAI client
client = OpenAI()


# =========================
# LOAD CLAIMS
# =========================
# Load all raw claims from file
with open("data/raw_claims/raw_claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)

# Store results
results = []

# Count how many errors occur
error_count = 0

# Total number of claims (used for progress tracking)
TOTAL = len(claims)

print(f"\nStarting V3 extraction on {TOTAL} claims...\n")


# =========================
# MAIN LOOP (FULL DATASET)
# =========================
"""
Unlike V1/V2, we process ALL claims (no slicing like [:20] or [:100]).

enumerate(claims) gives:
- i → current index (0, 1, 2, ...)
- claim → actual claim data
"""
for i, claim in enumerate(claims):

    raw_text = claim["raw_text"]


    # =========================
    # PROMPT DESIGN (BALANCED)
    # =========================
    """
    This prompt is a compromise between V1 and V2:

    V2 problem:
    → Too strict (may return null too often)

    V3 solution:
    → Allow "reasonable interpretation"

    Key rules:
    - Extract as accurately as possible
    - Do NOT leave fields empty if information exists
    - Allow slight interpretation if unclear
    - Normalize amount (numeric only)
    """

    prompt = f"""
Extract structured data from this insurance claim.

Rules:
- Extract values as accurately as possible from the text
- If information exists, DO NOT leave it empty
- Use best reasonable interpretation if slightly unclear
- Amount must be numeric (no currency symbols)
- claim_type must be one of:
  Vehicle Theft, Single Vehicle Collision, Multi-vehicle Collision, Parked Car

Return ONLY valid JSON.

Format:
{{
  "claim_id": null,
  "customer_name": "",
  "claim_date": "",
  "claim_type": "",
  "amount": ""
}}

Text:
{raw_text}
"""


    # Store raw response (used in case of failure)
    content = None


    try:
        # =========================
        # API CALL
        # =========================
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )


        # Extract response content
        content = response.choices[0].message.content


        # =========================
        # CLEAN RESPONSE
        # =========================
        """
        Remove markdown formatting if present.

        Example:
        ```json {...} ``` → {...}
        """
        if isinstance(content, str):
            content = re.sub(r"```json|```", "", content).strip()


        # Convert JSON string → Python dictionary
        data = json.loads(content)


    except Exception as e:
        # =========================
        # ERROR HANDLING
        # =========================
        """
        If something fails (API issue, invalid JSON, etc.),
        we fallback to a default empty structure.

        Compared to V2:
        - Simpler (no recovery attempt)
        - More stable for large-scale processing
        """

        print(f"Error at claim {i}: {e}")

        data = {
            "claim_id": None,
            "customer_name": None,
            "claim_date": None,
            "claim_type": None,
            "amount": None
        }

        error_count += 1


    # =========================
    # ADD DOC ID
    # =========================
    """
    doc_id is required for:
    - tracking each claim
    - evaluation later
    """
    data["doc_id"] = claim["doc_id"]


    # Store result
    results.append(data)


    # =========================
    # PROGRESS DISPLAY
    # =========================
    """
    This prints progress every 50 claims.

    Example:
    if i = 0, 50, 100, 150...
    → print progress

    Why?
    - Long runs can take time
    - Helps monitor execution in real-time
    """
    if i % 50 == 0:
        print(f"Processed {i}/{TOTAL}")


    # =========================
    # RATE LIMIT SAFETY
    # =========================
    """
    time.sleep(0.05) means:
    → wait 0.05 seconds between API calls

    Why?
    - Prevent hitting API rate limits
    - Avoid request throttling or failures

    Approximate throughput:
    1 / 0.05 = 20 requests per second (max theoretical)
    """
    time.sleep(0.05)


# =========================
# SAVE RESULTS
# =========================
with open("data/processed/extracted_claims_v3.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)


# =========================
# FINAL OUTPUT
# =========================
print("\nV3 Extraction Complete!")

"""
len(results):
= total number of processed claims

Should equal TOTAL unless something critical failed
"""
print(f"Total processed: {len(results)}")


"""
error_count:
= number of failed extractions

Useful metric:
error_rate = error_count / TOTAL

Example:
10 errors / 1000 claims = 1% error rate
"""
print(f"Errors: {error_count}")