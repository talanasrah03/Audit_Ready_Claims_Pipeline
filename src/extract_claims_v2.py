"""
AI extraction module (V2).

Goal:
Extract structured data from raw insurance claims using an AI model,
with stronger constraints, better error handling, and realistic simulation.

What this script does:
- Reads raw claim text
- Sends it to an AI model with a stricter prompt
- Parses structured JSON output
- Attempts recovery if parsing fails
- Simulates realistic AI imperfections
- Saves structured results

Important concept:
This version is stricter and more realistic than V1.

What is different from V1:
- Stronger prompt rules (no guessing, exact extraction)
- Better error handling with recovery attempts
- Debug logging of token usage
- Controlled simulation of imperfect AI outputs

Why this matters:
In real production systems, AI outputs are not always perfect.
This script intentionally introduces controlled imperfections to:
- test downstream robustness
- simulate messy real-world AI behavior
- prepare the rest of the pipeline for imperfect inputs
"""

import json   # Used to read and write structured data in JSON format
import re     # Used to clean and extract patterns from text using regular expressions
import random   # Used to simulate randomness (AI imperfections and noise)
from openai import OpenAI   # Used to interact with the OpenAI API for AI-based extraction


# =========================
# INIT CLIENT
# =========================
"""
Goal:
Initialize the OpenAI client.

Logic:
- Uses the API key stored in environment variables
- Creates a client object that can send requests to the model

Important:
If the API key is missing or invalid,
all API calls in this script will fail.
"""

client = OpenAI()


# =========================
# LOAD CLAIMS
# =========================
"""
Goal:
Load raw claims dataset from file.

Logic:
- Open the JSON file
- Convert its content into a Python list of dictionaries

Important:
encoding="utf-8" ensures that special characters
such as é, ü, and accented names are handled correctly.

Without it:
→ some characters may break or be displayed incorrectly
"""

with open("data/raw_claims/raw_claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)


# Store extracted results
results = []

# Count how many errors required full fallback
"""
Goal:
Track how many times the extraction failed completely.

Why important:
- Helps measure robustness of the extraction pipeline
- Shows how often the model + recovery logic were not enough
"""

error_count = 0


# =========================
# MAIN LOOP
# =========================
"""
Goal:
Process multiple claims using AI.

Logic:
- claims[:100] limits the script to the first 100 claims
- This reduces API cost and speeds up testing
- enumerate(...) gives:
    i     → current position in the loop
    claim → the actual claim record

Why use i:
→ useful for debugging
→ helps identify which claim caused an error
"""

for i, claim in enumerate(claims[:100]):

    raw_text = claim["raw_text"]


    # =========================
    # PROMPT DESIGN (STRICT MODE)
    # =========================
    """
    Goal:
    Force the AI model to extract data precisely and consistently.

    Logic:
    - "Do NOT guess" reduces hallucinations
    - "Copy EXACTLY" reduces value changes
    - Restricted claim_type values improve consistency
    - JSON-only output makes parsing easier

    Why important:
    Without strict instructions,
    the AI may:
    - invent values
    - rewrite values loosely
    - return explanations instead of structured output

    Example:
    Bad:
    "about 1000"

    Good:
    "1000"
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


    # Store raw AI response for possible recovery
    content = None


    try:
        # =========================
        # API CALL
        # =========================
        """
        Goal:
        Send the prompt to the AI model and receive structured output.

        Important parameters:

        model="gpt-4o-mini"
        → lightweight model
        → faster and cheaper
        → suitable for structured extraction

        temperature=0
        → makes output more deterministic
        → same input is more likely to produce the same result

        response_format={"type": "json_object"}
        → encourages JSON-only output
        → reduces parsing problems

        messages:
        → defines the interaction with the model
        """

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
        Goal:
        Monitor token usage for each request.

        response.usage contains:
        - prompt_tokens     → tokens used for the input
        - completion_tokens → tokens used for the model output
        - total_tokens      → total token usage

        Why important:
        - API cost depends on token usage
        - Helps optimize prompts and model usage
        """

        print(f"\n--- CLAIM {i} ---")
        print("TOKENS:", response.usage)

        """
        response.choices[0].message.content means:
        - the API may return one or more possible outputs
        - choices[0] selects the first one
        - message.content gets the actual text produced by the model
        """
        content = response.choices[0].message.content


        # =========================
        # CLEAN RESPONSE
        # =========================
        """
        Goal:
        Ensure the response is clean JSON.

        Problem:
        AI may sometimes wrap JSON in markdown, for example:

        ```json
        { ... }
        ```

        Logic:
        - Remove markdown markers using regex
        - Use .strip() to remove extra spaces and line breaks

        Without this:
        → json.loads() may fail
        """

        if isinstance(content, str):
            content = re.sub(r"```json|```", "", content).strip()


        # Convert JSON string → Python dictionary
        data = json.loads(content)


    except Exception as e:
        # =========================
        # PRIMARY ERROR HANDLING
        # =========================
        """
        Goal:
        Catch errors during the first extraction attempt.

        Possible error causes:
        - API request failure
        - invalid JSON
        - unexpected response structure
        - network issues

        Important:
        This does NOT stop the pipeline.
        Instead, it triggers a recovery attempt.
        """

        print(f"ERROR on claim {i}: {e}")


        # =========================
        # SECOND ATTEMPT (RECOVERY)
        # =========================
        """
        Goal:
        Try to recover usable JSON from a broken or partial response.

        Logic:
        - Search for a {...} block inside the response text
        - Extract only that part
        - Try to parse it as JSON

        Example:
        Response text:
        "some text before { valid_json } some text after"

        Recovery:
        → extract "{ valid_json }"
        → try json.loads(...) on that part only
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
            Goal:
            Ensure the pipeline never crashes completely.

            Logic:
            - If recovery also fails
            - Return an empty structured object
            - Increase the error counter

            Why important:
            Without this fallback,
            one broken claim could stop the full extraction run.
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
    Goal:
    Attach doc_id manually to the extracted data.

    Logic:
    - AI extracts structured fields from raw text
    - But doc_id is not part of the claim narrative itself
    - So it must be added manually after extraction

    Why important:
    - needed for evaluation
    - needed for later matching and tracking
    """

    data["doc_id"] = claim["doc_id"]


    # =========================
    # SIMULATE AI NOISE
    # =========================
    """
    Goal:
    Simulate real-world AI imperfections.

    Why important:
    Real AI systems are not perfectly consistent.
    They may produce:
    - slightly different formatting
    - extra text
    - inconsistent capitalization

    This section intentionally introduces small errors
    so downstream steps can be tested against imperfect outputs.

    This is called "noise injection":
    → adding controlled imperfections on purpose
    """


    # 20% chance to corrupt amount format
    """
    random.random() returns a number between 0 and 1.

    If the value is below 0.2:
    → apply the simulated noise
    → this means roughly 20% probability

    Example:
    amount = "1200"
    → becomes "1200 USD"
    """

    if random.random() < 0.2 and data.get("amount"):
        data["amount"] = str(data["amount"]) + " USD"


    # 20% chance to modify claim_type formatting
    """
    Example:
    "Vehicle Theft" → "vehicle theft"

    This tests whether later pipeline steps
    can handle differences in capitalization.
    """

    if random.random() < 0.2 and data.get("claim_type"):
        data["claim_type"] = data["claim_type"].lower()


    # Store final extracted record
    results.append(data)


# =========================
# SAVE RESULTS
# =========================
"""
Goal:
Save extracted results to file.

Logic:
- Write the extracted claims into JSON format
- Keep the file readable

Important:
indent=2
→ makes the JSON easier for humans to read

ensure_ascii=False
→ keeps special characters readable

Example:
"é" stays "é" instead of being converted into escape codes
"""

with open("data/processed/extracted_claims_v2.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)


# =========================
# FINAL OUTPUT
# =========================
"""
Goal:
Show execution summary.

len(results):
→ number of processed claims

Example:
100 claims processed → len(results) = 100
"""

print("\nV2 Extraction complete!")
print(f"Processed: {len(results)}")

"""
error_count:
→ number of claims where full fallback was needed

Meaning:
- higher value → more severe extraction/recovery failures
- lower value → more reliable extraction
"""

print(f"Errors handled: {error_count}")