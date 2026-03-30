"""
AI extraction module (V1).

Goal:
Transform raw, unstructured insurance claims into structured JSON data using an AI model.

What this script does:
- Reads raw claim text
- Sends it to an AI model with a structured prompt
- Extracts key fields
- Cleans and validates the response
- Saves structured results

Important concept:
We use an LLM (Large Language Model) as a data extraction engine.

Why this is called V1:
This is the first version of the extraction pipeline.
It focuses on:
- basic structured extraction
- simple prompt design
- basic fallback handling

Later versions can become stricter, more robust, or more scalable.

Example:
Input:
"John Doe reported a theft of his car worth 5000€ on Jan 10"

Output:
{
    "customer_name": "John Doe",
    "claim_type": "Vehicle Theft",
    "amount": 5000
}
"""

import os   # Used for file and folder operations such as creating output directories
import json   # Used to read and write structured data in JSON format
import re   # Used to clean text using regular expressions
from openai import OpenAI   # Used to communicate with the OpenAI API


# =========================
# INITIALIZATION
# =========================
"""
Goal:
Initialize the OpenAI client to send requests to the AI model.

Logic:
- The API key is automatically loaded from environment variables
- This allows secure communication with the model

Important:
If the API key is missing or invalid,
the script will fail when trying to call the model.
"""

client = OpenAI()


# =========================
# LOAD CLAIMS
# =========================
"""
Goal:
Load raw claims data from a JSON file.

Logic:
- Open the file in read mode
- Use utf-8 encoding to support special characters
- Convert JSON content into Python objects

Expected structure:
A list of claim dictionaries, for example:
[
    {
        "doc_id": "doc_1",
        "raw_text": "Customer John Doe reported..."
    }
]
"""

with open("data/raw_claims/raw_claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)


# =========================
# INITIALIZE RESULT STORAGE
# =========================
"""
Goal:
Store all extracted results.

Logic:
- Each processed claim is appended to this list
- At the end, the full list is saved into a new JSON file

Example:
results = [
    {claim_1_data},
    {claim_2_data}
]
"""

results = []


# =========================
# MAIN PROCESSING LOOP
# =========================
"""
Goal:
Process claims one by one using the AI model.

Logic:
- Loop through the raw claims
- Extract raw text
- Send it to the model
- Parse the result
- Save the structured output

Important:
claims[:20] means:
→ only process the first 20 claims

Why useful:
- reduces API cost
- speeds up testing
- makes debugging easier

Example:
If there are 1000 claims,
this version processes only the first 20.
"""

for claim in claims[:20]:

    # Extract raw claim text
    raw_text = claim["raw_text"]


    # =========================
    # PROMPT DESIGN
    # =========================
    """
    Goal:
    Tell the AI model exactly what information to extract.

    Logic:
    - List all required fields
    - Define format rules
    - Ask for JSON only

    Why important:
    Without a precise prompt,
    the model may:
    - add explanations
    - return inconsistent formatting
    - miss required fields

    Example:
    Bad output:
    "The claim appears to describe a vehicle theft."

    Good output:
    {
        "claim_type": "Vehicle Theft"
    }
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
        Goal:
        Send the prompt to the AI model and receive a structured response.

        Important parameters:

        model="gpt-4o-mini"
        → lightweight model
        → faster and cheaper than larger models
        → suitable for structured extraction tasks

        temperature=0
        → makes output more deterministic
        → same input is more likely to produce the same output

        response_format={"type": "json_object"}
        → asks the API to return JSON format
        → reduces formatting problems

        messages:
        - system message defines the role/behavior of the model
        - user message contains the actual extraction task
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

        """
        response.choices[0].message.content means:
        - response may contain one or more candidate outputs
        - choices[0] takes the first returned output
        - message.content gets the actual text returned by the model
        """

        content = response.choices[0].message.content


        # =========================
        # CLEAN RESPONSE
        # =========================
        """
        Goal:
        Ensure the response is clean and usable as JSON.

        Problem:
        Sometimes a model may wrap JSON inside markdown markers like:

        ```json
        { ... }
        ```

        Logic:
        - Remove markdown markers using regex
        - Remove extra spaces with .strip()

        Example:
        Before:
        ```json
        { "amount": 1000 }
        ```

        After:
        { "amount": 1000 }
        """

        content = re.sub(r"```json|```", "", content).strip()


        # Convert JSON text into a Python dictionary
        data = json.loads(content)


    except:
        # =========================
        # ERROR HANDLING
        # =========================
        """
        Goal:
        Prevent the full pipeline from crashing if one claim fails.

        Possible causes:
        - API request failure
        - invalid JSON
        - unexpected response format
        - network problem

        Logic:
        - If anything fails inside the try block
        - create a default empty structure instead

        Why important:
        Without this,
        a single failed claim could stop the whole extraction run.
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
    Goal:
    Attach the original document ID to the extracted result.

    Logic:
    - The AI model extracts claim information from text
    - But doc_id is not part of the natural text
    - So we add it manually after extraction

    Why important:
    - needed for evaluation
    - needed to match predictions with ground truth
    - useful for tracking a claim through the pipeline

    Example:
    doc_id = "doc_1"
    """

    data["doc_id"] = claim["doc_id"]


    # Store final extracted record
    results.append(data)


# =========================
# SAVE RESULTS
# =========================
"""
Goal:
Save extracted data to an output file.

Logic:
- Ensure the output folder exists
- Save the list of results as JSON

Important detail:
os.makedirs("data/processed", exist_ok=True)

exist_ok=True means:
→ if the folder already exists, do nothing
→ do not raise an error

Without exist_ok=True:
→ Python may fail if the folder already exists

Example:
First run:
- folder is created

Second run:
- folder already exists
- script continues safely
"""

os.makedirs("data/processed", exist_ok=True)


with open("data/processed/extracted_claims.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

"""
Important details:

indent=2
→ formats the JSON nicely with spacing
→ easier for humans to read

ensure_ascii=False
→ keeps special characters readable

Example:
"José" stays "José"
instead of being converted into escaped text
"""


# =========================
# FINAL OUTPUT
# =========================
"""
Goal:
Confirm that the script finished successfully.

Logic:
- Print a success message
- Print how many claims were processed

Example:
Processed: 20 claims
"""

print("V1 Extraction complete!")
print(f"Processed: {len(results)} claims")