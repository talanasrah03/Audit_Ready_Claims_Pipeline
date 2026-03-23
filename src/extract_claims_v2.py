import json
import re
import random
from openai import OpenAI

# =========================
# INIT CLIENT
# =========================
client = OpenAI()

# =========================
# LOAD CLAIMS
# =========================
with open("data/raw_claims/raw_claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)

results = []
error_count = 0

# =========================
# LOOP
# =========================
for i, claim in enumerate(claims[:100]):
    raw_text = claim["raw_text"]

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

    content = None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )

        # 🔥 DEBUG (IMPORTANT)
        print(f"\n--- CLAIM {i} ---")
        print("TOKENS:", response.usage)

        content = response.choices[0].message.content

        if isinstance(content, str):
            content = re.sub(r"```json|```", "", content).strip()

        data = json.loads(content)

    except Exception as e:
        print(f"❌ ERROR on claim {i}: {e}")

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
    data["doc_id"] = claim["doc_id"]

    # =========================
    # SIMULATE AI NOISE
    # =========================
    if random.random() < 0.2 and data.get("amount"):
        data["amount"] = str(data["amount"]) + " USD"

    if random.random() < 0.2 and data.get("claim_type"):
        data["claim_type"] = data["claim_type"].lower()

    results.append(data)

# =========================
# SAVE
# =========================
with open("data/processed/extracted_claims_v2.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# =========================
# FINAL OUTPUT
# =========================
print("\n✅ V2 Extraction complete!")
print(f"✔️ Processed: {len(results)}")
print(f"⚠️ Errors handled: {error_count}")