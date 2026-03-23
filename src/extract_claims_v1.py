import os
import json
import re
from openai import OpenAI

client = OpenAI()

# =========================
# LOAD CLAIMS
# =========================
with open("data/raw_claims/raw_claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)

results = []

# =========================
# LOOP
# =========================
for claim in claims[:20]:  # V1 small batch
    raw_text = claim["raw_text"]

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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You extract structured insurance data and return only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}  # 🔥 IMPORTANT
        )

        content = response.choices[0].message.content

        # Clean markdown if exists
        content = re.sub(r"```json|```", "", content).strip()

        data = json.loads(content)

    except:
        # fallback
        data = {
            "claim_id": None,
            "customer_name": None,
            "claim_date": None,
            "claim_type": None,
            "amount": None
        }

    # Add doc_id
    data["doc_id"] = claim["doc_id"]

    results.append(data)

# =========================
# SAVE
# =========================
os.makedirs("data/processed", exist_ok=True)

with open("data/processed/extracted_claims.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("✅ V1 Extraction complete!")
print(f"Processed: {len(results)} claims")