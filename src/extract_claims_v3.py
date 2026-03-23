import json
import re
import time
from openai import OpenAI

client = OpenAI()

# =========================
# LOAD CLAIMS
# =========================
with open("data/raw_claims/raw_claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)

results = []
error_count = 0

TOTAL = len(claims)

print(f"\n🚀 Starting V3 extraction on {TOTAL} claims...\n")

# =========================
# LOOP THROUGH ALL CLAIMS
# =========================
for i, claim in enumerate(claims):
    raw_text = claim["raw_text"]

    # 🔥 FIXED PROMPT (CRITICAL)
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

    content = None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        if isinstance(content, str):
            content = re.sub(r"```json|```", "", content).strip()

        data = json.loads(content)

    except Exception as e:
        print(f"❌ Error at claim {i}: {e}")

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

    results.append(data)

    # =========================
    # PROGRESS DISPLAY
    # =========================
    if i % 50 == 0:
        print(f"✅ Processed {i}/{TOTAL}")

    # =========================
    # RATE LIMIT SAFETY
    # =========================
    time.sleep(0.05)

# =========================
# SAVE RESULTS
# =========================
with open("data/processed/extracted_claims_v3.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# =========================
# FINAL OUTPUT
# =========================
print("\n🎉 V3 Extraction Complete!")
print(f"✔️ Total processed: {len(results)}")
print(f"⚠️ Errors: {error_count}")