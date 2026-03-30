"""
AI extraction module (V3).

Goal:
Process all raw insurance claims using an AI model and extract structured data
in a scalable, stable, and production-oriented way.

What this script does:
- Reads all raw claim texts
- Sends each claim to an AI model with a balanced prompt
- Parses structured JSON output
- Handles failures with a simple fallback
- Tracks progress during long runs
- Adds small delays to reduce API rate-limit issues
- Saves all extracted results

Important concept:
This is Version 3 of the extraction pipeline.

Comparison with earlier versions:

V1:
- Basic extraction
- Small batch only
- Minimal error handling

V2:
- Very strict prompt
- Recovery attempts for broken JSON
- Artificial noise injection for testing

V3:
- Processes the full dataset
- Uses a more balanced prompt
- Prioritizes stability and scalability
- Includes progress tracking and API safety delay

Design philosophy:
Instead of being too strict,
this version allows the model to make reasonable interpretations when needed.

Why this matters:
A very strict prompt may leave too many fields empty.
A balanced prompt can improve:
- completeness
- usability
- overall downstream value
"""

import json   # Used to read and write structured data in JSON format
import re     # Used to clean and extract patterns from text using regular expressions
import time   # Used to slow requests slightly to reduce API rate-limit risk
from openai import OpenAI   # Used to communicate with the OpenAI API for extraction


# =========================
# INIT CLIENT
# =========================
"""
Goal:
Initialize the OpenAI client.

Logic:
- Uses the API key from environment variables
- Creates a client object that can send requests to the AI model

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
Load all raw claims from file.

Logic:
- Open the JSON file in read mode
- Use utf-8 encoding to support special characters
- Convert JSON into a Python list of claim dictionaries

Example:
claims = [
    {"doc_id": "doc_1", "raw_text": "..."},
    {"doc_id": "doc_2", "raw_text": "..."}
]
"""

with open("data/raw_claims/raw_claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)


# =========================
# INITIALIZATION
# =========================
"""
Goal:
Prepare variables needed during processing.

Variables:
- results     → stores all extracted claims
- error_count → counts how many claims failed extraction
- TOTAL       → total number of claims in the dataset

Why TOTAL is useful:
→ helps show progress during long runs
"""

results = []
error_count = 0
TOTAL = len(claims)

print(f"\nStarting V3 extraction on {TOTAL} claims...\n")


# =========================
# MAIN LOOP (FULL DATASET)
# =========================
"""
Goal:
Process every claim in the dataset.

Logic:
- Loop through all claims
- Use enumerate(...) to get:
    i     → current position in the loop
    claim → the actual claim record

Why this matters:
Unlike V1 and V2, this version does not slice the dataset.
That makes it more realistic for larger-scale processing.
"""

for i, claim in enumerate(claims):

    raw_text = claim["raw_text"]


    # =========================
    # PROMPT DESIGN (BALANCED)
    # =========================
    """
    Goal:
    Give the AI model instructions that are strict enough to stay structured,
    but flexible enough to avoid too many missing fields.

    Logic:
    - "Extract as accurately as possible" → keeps focus on correctness
    - "DO NOT leave it empty if information exists" → improves completeness
    - "Use best reasonable interpretation" → helps when wording is unclear
    - "Amount must be numeric" → makes downstream processing easier

    Why this is called balanced:
    - V2 was very strict and could leave more fields empty
    - V3 allows limited interpretation when the signal is clear enough

    Example:
    "around 1000 euros" → 1000
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


    # Store raw response in case an error happens
    content = None


    try:
        # =========================
        # API CALL
        # =========================
        """
        Goal:
        Send the claim text to the AI model and receive structured output.

        Important parameters:

        model="gpt-4o-mini"
        → lightweight model
        → faster and more cost-efficient

        temperature=0
        → makes output more deterministic
        → the same input is more likely to produce the same result

        response_format={"type": "json_object"}
        → encourages JSON-only output
        → reduces parsing problems

        messages:
        → define the actual request sent to the model
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )

        """
        response.choices[0].message.content means:
        - the API may return one or more candidate outputs
        - choices[0] selects the first returned output
        - message.content gets the actual text produced by the model
        """
        content = response.choices[0].message.content


        # =========================
        # CLEAN RESPONSE
        # =========================
        """
        Goal:
        Ensure the response is clean and usable as JSON.

        Problem:
        Sometimes a model may still wrap JSON in markdown, for example:

        ```json
        { ... }
        ```

        Logic:
        - Remove markdown markers with regex
        - Remove extra spaces and line breaks with .strip()

        Without this:
        → json.loads() may fail
        """

        if isinstance(content, str):
            content = re.sub(r"```json|```", "", content).strip()


        # Convert JSON string into a Python dictionary
        data = json.loads(content)


    except Exception as e:
        # =========================
        # ERROR HANDLING
        # =========================
        """
        Goal:
        Prevent one failed claim from stopping the whole extraction run.

        Possible causes:
        - API request failure
        - invalid JSON
        - unexpected response format
        - network problem

        Logic:
        - Print the error for visibility
        - Return an empty structured object
        - Increase error_count

        Why this is simpler than V2:
        - V2 tries recovery from broken JSON
        - V3 prioritizes simplicity and stability for large-scale execution
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
    Goal:
    Attach the original document identifier.

    Logic:
    - doc_id is not extracted by the AI model
    - it must be added manually after extraction

    Why important:
    - used later for evaluation
    - used to track each claim through the pipeline
    """

    data["doc_id"] = claim["doc_id"]


    # Store result
    results.append(data)


    # =========================
    # PROGRESS DISPLAY
    # =========================
    """
    Goal:
    Show progress during long runs.

    Logic:
    i % 50 == 0 means:
    → print once every 50 loop positions

    Example:
    i = 0, 50, 100, 150, ...

    Why useful:
    - large datasets may take time
    - helps the user see that the script is still running

    Important note:
    At i = 0, the script prints immediately.
    That is normal because 0 is divisible by 50.
    """

    if i % 50 == 0:
        print(f"Processed {i}/{TOTAL}")


    # =========================
    # RATE LIMIT SAFETY
    # =========================
    """
    Goal:
    Reduce the risk of sending requests too quickly to the API.

    Logic:
    time.sleep(0.05)
    → pause for 0.05 seconds after each request

    Why important:
    APIs often have request limits.
    If requests are sent too fast,
    the API may reject them with errors such as:
    429 Too Many Requests

    Example:
    0.05 seconds delay
    → about 20 requests per second in theory

    In practice:
    real speed is usually slower,
    because API response time also adds delay.
    """

    time.sleep(0.05)


# =========================
# SAVE RESULTS
# =========================
"""
Goal:
Save extracted results into a JSON file.

Logic:
- Write the Python list into JSON format
- Keep the file readable for humans

Important parameters:

indent=2
→ adds spacing and line breaks
→ makes the file easier to read

ensure_ascii=False
→ keeps special characters readable

Example:
"José" stays "José"
instead of being converted into escape codes
"""

with open("data/processed/extracted_claims_v3.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)


# =========================
# FINAL OUTPUT
# =========================
"""
Goal:
Show a final execution summary.

len(results):
→ total number of processed claims

In a normal run:
len(results) should match TOTAL,
because every claim produces some output
even if fallback data is used.
"""

print("\nV3 Extraction Complete!")
print(f"Total processed: {len(results)}")


"""
error_count:
→ number of claims where extraction failed
→ those claims used the fallback empty structure

Useful metric:
error_rate = error_count / TOTAL

Example:
10 errors out of 1000 claims = 1%
"""

print(f"Errors: {error_count}")