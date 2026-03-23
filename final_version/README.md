Audit-Ready AI Claims Processing Pipeline
Overview

This project simulates a real-world insurance claims processing system powered by AI, with a strong focus on auditability, human-in-the-loop decision making, and structured data extraction.

The system processes messy, unstructured insurance claim inputs and transforms them into validated, risk-scored, and reviewable outputs through a multi-stage pipeline.

It is designed to reflect the core principles of modern AI-driven claims automation systems:

Reliable structured extraction
Transparent validation and scoring
Human oversight for uncertain cases
End-to-end traceability

This aligns closely with the approach taken by companies  where automation is combined with control, explainability, and flexibility.

Objectives

The goal of this project is to demonstrate how AI can be used to:

Automate the extraction of structured data from unstructured documents
Validate outputs using domain-specific rules (audit-grade logic)
Detect inconsistencies and assign risk levels
Route uncertain cases to human review
Provide interfaces for both internal teams and customers
Why This Project

This project was designed to simulate a production-ready AI claims pipeline, with a strong focus on reliability, transparency, and human oversight.

Instead of relying solely on AI outputs, the system introduces:

validation layers
risk scoring
human review workflows

This reflects how modern AI systems are deployed in real business environments, where accuracy, traceability, and control are critical.

System Architecture

The pipeline is composed of the following stages:

1. Data Generation

Synthetic but realistic insurance claims are generated:

Messy, human-like input text
Clean ground truth for evaluation
2. AI Extraction

A language model extracts structured fields:

claim_id
customer_name
claim_date
claim_type
amount
3. Data Cleaning

Minimal transformation is applied to preserve original meaning while ensuring usability.

4. Evaluation

Predictions are compared with ground truth:

Field-level accuracy
Error tracking
5. Validation (Rule-Based)

Claims are validated using domain rules:

Missing fields detection
Amount range validation
Logical consistency checks
Date validation

Each claim receives:

Valid / invalid status
Detailed list of issues
Severity level
6. Risk Scoring

Each claim is assigned a risk score based on:

Missing or inconsistent data
Large deviations from expected values
Classification mismatches

Output includes:

Risk score (numeric)
Risk level (LOW / MEDIUM / HIGH)
Explanation (reasons)
7. Human Review Queue

Invalid or uncertain claims are routed to a review queue with:

Identified issues
Recommended actions
Possible decisions
8. Interfaces
Internal Dashboard (Insurance Team)

Allows:

Claim inspection
Risk analysis review
Decision making (approve / reject / correct / request info)
Customer Portal

Allows:

Claim status tracking
Feedback submission
Additional information input
Project Structure

data/
  raw_claims/
  processed/
  ground_truth/

src/
  extract_claims_v1.py
  extract_claims_v2.py
  extract_claims_v3.py
  clean_and_validate.py
  evaluate.py
  rag_validation.py
  risk_scoring.py
  human_review.py
  generate_fake_claims.py

app.py
customer_app.py
requirements.txt
README.md

Running the Project
1. Install Dependencies

pip install -r requirements.txt

2. Generate Data

python src/generate_fake_claims.py

3. Run Extraction (Recommended: V3)

python src/extract_claims_v3.py

4. Clean Data

python src/clean_and_validate.py

5. Evaluate Extraction Accuracy

python src/evaluate.py

6. Run Validation (RAG-style rules)

python src/rag_validation.py

7. Compute Risk Scores

python src/risk_scoring.py

8. Generate Human Review Queue

python src/human_review.py

Running the Interfaces
Internal Dashboard

streamlit run app.py

Customer Portal

streamlit run customer_app.py


Key Design Decisions
1. Human-in-the-Loop

The system does not fully trust AI outputs.
Instead, it routes uncertain cases to human reviewers.

2. Auditability

Every decision is traceable:

Validation issues are explicit
Risk scores are explainable
No black-box decisions
3. Controlled Data Cleaning

The system avoids aggressive normalization to prevent loss of information.

4. Rule-Based Validation (RAG-inspired)

Instead of relying solely on AI, domain rules ensure consistency and reliability.

5. Risk-Based Prioritization

Claims are ranked by risk, allowing teams to focus on critical cases first.

Limitations
Amount normalization is simplified and may merge decimals
Risk scoring uses fixed thresholds (not learned)
UI actions are simulated (no database persistence)
No real document ingestion (text-only simulation)
Possible Improvements
Integrate real document parsing (PDF, OCR)
Persist decisions in a database
Add authentication for user roles
Replace rule thresholds with learned models
Deploy as a full web service
License

This project is for educational and portfolio purposes.

© 2026 Tala Nasarah. All rights reserved.