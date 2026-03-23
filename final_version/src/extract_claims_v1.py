"""
This script is responsible for extracting structured information from raw insurance claims
using an AI model (OpenAI).

Context in the project:
This is the FIRST step of the AI pipeline.

We start with messy, unstructured text (raw claims),
and we transform it into structured JSON data with defined fields.

What this script does:
1. Loads raw claim texts
2. Sends each claim to an AI model with a structured prompt
3. Receives structured JSON output
4. Cleans and validates the response
5. Stores all extracted results

Input:
- data/raw_claims/raw_claims.json (contains messy text)

Output:
- data/processed/extracted_claims.json (structured data)

Important concept:
We are using an LLM (Large Language Model) as a "data extractor".
"""


import os     # Used for file/folder operations
import json   # Used for reading/writing structured data
import re     # Used for text cleaning (regex)
from openai import OpenAI  # OpenAI client to call the model


# Initialize OpenAI client (uses API key from environment)
client = OpenAI()


# =========================
# LOAD CLAIMS
# =========================
# Load raw claims dataset
with open("data/raw_claims/raw_claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)

"""
Structure of each claim:
{
    "doc_id": "doc_1",
    "raw_text": "Customer John Doe reported..."
}
"""

# This will store all extracted results
results = []


# =========================
# MAIN LOOP
# =========================
"""
We process each claim one by one.

IMPORTANT:
claims[:20] means:
→ only process first 20 claims

This is used for:
- testing
- cost control (API usage)
- faster iteration
"""
for claim in claims[:20]:

    # Extract raw text of the claim
    raw_text = claim["raw_text"]


    # =========================
    # PROMPT DESIGN
    # =========================
    """
    This prompt tells the AI exactly what to extract.

    Key design choices:
    - Explicit field list → reduces ambiguity
    - Format constraints → ensures consistency
    - "Return ONLY JSON" → prevents extra text
    """

    prompt = f"""
Extract the following fields from this insurance claim:

- claim_id (or null)
- customer_name
- claim_date (YYYY-MM-DD)
- claim_type (Vehicle Theft, Single Vehicle Collision, Multi-vehicle Collision, Parked Car)
- amount (number only)

Return ONLY JSON.
No explanations.

Text:
{raw_text}
"""


    try:
        # =========================
        # API CALL TO OPENAI
        # =========================
        """
        We send the prompt to the AI model.

        Parameters explained:

        model="gpt-4o-mini"
        → lightweight model (faster + cheaper, good for extraction)

        messages:
        → system message defines behavior
        → user message contains the actual task

        temperature=0
        → makes output deterministic (same input → same output)

        response_format={"type": "json_object"}
        → forces the model to return valid JSON (VERY IMPORTANT)
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured insurance data and return only JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        # Extract content from API response
        content = response.choices[0].message.content


        # =========================
        # CLEAN RESPONSE
        # =========================
        """
        Sometimes the model wraps JSON in markdown like:

        ```json
        { ... }
        ```

        We remove those markers using regex.
        """

        content = re.sub(r"```json|```", "", content).strip()


        # Convert JSON string → Python dictionary
        data = json.loads(content)


    except:
        # =========================
        # FALLBACK (ERROR HANDLING)
        # =========================
        """
        If anything fails (API error, invalid JSON, etc.),
        we create a default empty structure.

        This ensures:
        - pipeline does NOT crash
        - output format stays consistent
        """

        data = {
            "claim_id": None,
            "customer_name": None,
            "claim_date": None,
            "claim_type": None,
            "amount": None
        }


    # =========================
    # ADD METADATA
    # =========================
    """
    We add doc_id manually because:
    - It is NOT extracted by the model
    - It is needed later for evaluation and matching
    """
    data["doc_id"] = claim["doc_id"]


    # Store result
    results.append(data)


# =========================
# SAVE RESULTS
# =========================

"""
We ensure the output folder exists.
exist_ok=True means:
→ do nothing if folder already exists
→ avoid errors
"""
os.makedirs("data/processed", exist_ok=True)


# Save extracted results to JSON file
with open("data/processed/extracted_claims.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

"""
indent=2 → makes JSON readable
ensure_ascii=False → keeps special characters (e.g., accents)
"""


# =========================
# FINAL OUTPUT
# =========================
print("V1 Extraction complete!")
print(f"Processed: {len(results)} claims")