import os
import json
from openai import OpenAI

client = OpenAI()

# Load messy claims
with open("raw_claims/messy_claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)

results = []

for claim in claims[:20]:
    raw_text = claim["raw_text"]

    prompt = f"""
Extract the following fields from this insurance claim text:

- claim_id (if present, otherwise null)
- customer_name
- claim_date
- claim_type
- amount

Return ONLY valid JSON in this exact format:
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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You extract structured data from messy insurance claims and return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    try:
        extracted = json.loads(content)
    except json.JSONDecodeError:
        extracted = {
            "claim_id": None,
            "customer_name": None,
            "claim_date": None,
            "claim_type": None,
            "amount": None,
            "raw_model_output": content
        }

    extracted["doc_id"] = claim["doc_id"]
    results.append(extracted)

# Create output folder
os.makedirs("data/processed", exist_ok=True)

# Save results
with open("data/processed/extracted_claims.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("✅ Extraction complete!")