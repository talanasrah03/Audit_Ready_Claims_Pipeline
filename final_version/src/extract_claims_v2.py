"""
This script is an improved version (V2) of the claims extraction pipeline.

Main goal:
Extract structured data from raw insurance claims using an AI model,
with stronger constraints, better error handling, and realistic simulation.

What is different from V1:
- Stronger prompt rules (no guessing, exact extraction)
- Better error handling with fallback recovery attempts
- Debug logging (token usage per request)
- Simulation of real-world AI imperfections (noise injection)

Why this matters:
In real production systems, AI outputs are NOT perfect.
This script intentionally introduces controlled imperfections to:
- test robustness of downstream steps
- simulate real-world messy outputs

Input:
- data/raw_claims/raw_claims.json

Output:
- data/processed/extracted_claims_v2.json
"""

import json
import re
import random  # Used to simulate randomness (AI imperfections)
from openai import OpenAI


# =========================
# INIT CLIENT
# =========================
# Initialize OpenAI client (uses API key from environment variables)
client = OpenAI()


# =========================
# LOAD CLAIMS
# =========================
# Load raw claims dataset
with open("data/raw_claims/raw_claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)

# Store extracted results
results = []

# Count how many errors were handled
error_count = 0


# =========================
# MAIN LOOP
# =========================
"""
We process up to 100 claims.

enumerate(claims[:100]) gives:
- i → index (0, 1, 2...)
- claim → actual claim object

We use i for debugging/logging.
"""
for i, claim in enumerate(claims[:100]):

    raw_text = claim["raw_text"]


    # =========================
    # PROMPT DESIGN (STRICT MODE)
    # =========================
    """
    This prompt is stricter than V1.

    Key improvements:
    - "Do NOT guess" → prevents hallucinations
    - "Copy EXACTLY" → preserves original values
    - Explicit allowed values for claim_type
    - Enforced JSON structure

    This reduces variability and increases reliability.
    """

    prompt = f"""
You are an expert system extracting structured insurance data.

Extract EXACT values from the text.

IMPORTANT RULES:
- Do NOT guess values
- Do NOT modify numbers
- Copy the amount EXACTLY as written
- If missing → return null
- claim_type MUST be exactly one of:
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


    # This will store raw AI response (used in error recovery)
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


        # =========================
        # DEBUG: TOKEN USAGE
        # =========================
        """
        response.usage contains:
        - prompt_tokens
        - completion_tokens
        - total_tokens

        This is important for:
        - cost monitoring
        - optimization
        """
        print(f"\n--- CLAIM {i} ---")
        print("TOKENS:", response.usage)


        # Extract content from response
        content = response.choices[0].message.content


        # =========================
        # CLEAN RESPONSE
        # =========================
        """
        Sometimes the model wraps JSON in markdown.
        We remove it using regex.
        """
        if isinstance(content, str):
            content = re.sub(r"```json|```", "", content).strip()


        # Convert JSON string → Python dictionary
        data = json.loads(content)


    except Exception as e:
        # =========================
        # PRIMARY ERROR HANDLING
        # =========================
        print(f"ERROR on claim {i}: {e}")


        # =========================
        # SECOND ATTEMPT (RECOVERY)
        # =========================
        """
        If parsing fails, we try to recover JSON manually.

        Strategy:
        - Search for anything that looks like {...}
        - Try to parse that part only
        """

        try:
            if content:
                match = re.search(r"\{.*\}", str(content), re.DOTALL)

                if match:
                    data = json.loads(match.group())
                else:
                    raise ValueError
            else:
                raise ValueError


        except:
            # =========================
            # FINAL FALLBACK
            # =========================
            """
            If everything fails:
            → return empty structured object

            This guarantees:
            - consistent output format
            - no pipeline crash
            """
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
    doc_id is added manually because:
    - it is not extracted by the model
    - it is needed later for evaluation
    """
    data["doc_id"] = claim["doc_id"]


    # =========================
    # SIMULATE AI NOISE
    # =========================
    """
    This section intentionally introduces small errors.

    Why?
    Real AI systems produce imperfect outputs:
    - inconsistent formatting
    - extra text
    - case variations

    We simulate this to test robustness of later steps.
    """

    # 20% chance to corrupt amount format
    if random.random() < 0.2 and data.get("amount"):
        """
        random.random() generates a number between 0 and 1

        If < 0.2 → 20% probability

        Example:
        "1200" → "1200 USD"
        """
        data["amount"] = str(data["amount"]) + " USD"


    # 20% chance to change claim_type format
    if random.random() < 0.2 and data.get("claim_type"):
        """
        Example:
        "Vehicle Theft" → "vehicle theft"
        """
        data["claim_type"] = data["claim_type"].lower()


    # Store result
    results.append(data)


# =========================
# SAVE RESULTS
# =========================
with open("data/processed/extracted_claims_v2.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)


# =========================
# FINAL OUTPUT
# =========================
print("\nV2 Extraction complete!")

"""
len(results):
= number of processed claims

Example:
If we processed 100 claims → len(results) = 100
"""
print(f"Processed: {len(results)}")

"""
error_count:
= number of claims where full fallback was needed

This is a measure of:
- robustness of extraction
- reliability of AI output
"""
print(f"Errors handled: {error_count}")