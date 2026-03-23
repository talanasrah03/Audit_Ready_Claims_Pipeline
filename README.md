# Audit-Ready AI Claims Processing Pipeline

## Overview

This project simulates a real-world insurance claims processing system powered by AI, with a strong focus on **auditability**, **human-in-the-loop decision making**, and **structured data extraction**.

The system processes messy, unstructured insurance claim inputs and transforms them into validated, risk-scored, and reviewable outputs through a multi-stage pipeline.

It reflects key principles of modern AI-driven claims automation systems:

- Structured and reliable data extraction  
- Transparent validation and scoring  
- Human oversight for uncertain cases  
- End-to-end traceability  

This approach aligns closely with companies like **Lynxia**, where automation is combined with control, explainability, and flexibility.

---

## Objectives

This project demonstrates how AI can be used to:

- Extract structured data from unstructured documents  
- Validate outputs using domain-specific rules (audit-grade logic)  
- Detect inconsistencies and assign risk levels  
- Route uncertain cases to human review  
- Provide interfaces for both internal teams and customers  

---

## Why This Project

This system is designed to simulate a **production-ready AI claims pipeline**.

Instead of relying solely on AI outputs, it introduces:

- Validation layers  
- Risk scoring mechanisms  
- Human review workflows  

This reflects how real AI systems are deployed in business environments, where **accuracy, traceability, and control are critical**.

---

## System Architecture

The pipeline consists of the following stages:

### 1. Data Generation
- Synthetic but realistic insurance claims  
- Messy, human-like input text  
- Clean ground truth for evaluation  

### 2. AI Extraction
Extracted fields:
- `claim_id`  
- `customer_name`  
- `claim_date`  
- `claim_type`  
- `amount`  

### 3. Data Cleaning
- Minimal transformation  
- Preserves original meaning  
- Ensures usability  

### 4. Evaluation
- Field-level accuracy  
- Error tracking  

### 5. Validation (Rule-Based)
Checks include:
- Missing fields  
- Amount ranges  
- Logical consistency  
- Date validation  

Outputs:
- Valid / invalid status  
- List of issues  
- Severity level  

### 6. Risk Scoring
Based on:
- Missing or inconsistent data  
- Large value deviations  
- Classification mismatches  

Outputs:
- Risk score (numeric)  
- Risk level (LOW / MEDIUM / HIGH)  
- Explanation (reasons)  

### 7. Human Review Queue
- Identified issues  
- Recommended actions  
- Possible decisions  

### 8. Interfaces

#### Internal Dashboard (Insurance Team)
- Claim inspection  
- Risk analysis  
- Decision making (approve / reject / correct / request info)  

#### Customer Portal
- Claim status tracking  
- Feedback submission  
- Additional information input  

---

## Project Structure


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


---
## Running the Project

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Data
```bash
python src/generate_fake_claims.py
```

### 3. Run Extraction (Recommended)
```bash
python src/extract_claims_v3.py
```

### 4. Clean Data
```bash
python src/clean_and_validate.py
```

### 5. Evaluate Accuracy
```bash
python src/evaluate.py
```

### 6. Run Validation
```bash
python src/rag_validation.py
```

### 7. Compute Risk Scores
```bash
python src/risk_scoring.py
```

### 8. Generate Review Queue
```bash
python src/human_review.py
```

---

## Running the Interfaces

### Internal Dashboard
```bash
streamlit run app.py
```

### Customer Portal
```bash
streamlit run customer_app.py
```
 

---

## Key Design Decisions

### Human-in-the-Loop
The system does not fully trust AI outputs.  
Uncertain cases are escalated to human reviewers.

### Auditability
Every decision is traceable:
- Explicit validation issues  
- Explainable risk scores  
- No black-box decisions  

### Controlled Data Cleaning
Avoids aggressive normalization to preserve meaning.

### Rule-Based Validation
Domain rules ensure consistency beyond AI predictions.

### Risk-Based Prioritization
Claims are ranked by risk to prioritize critical cases.

---

## Limitations

- Simplified amount normalization  
- Fixed risk thresholds  
- No persistence (UI actions are simulated)  
- No real document ingestion (text-only)  

---

## Possible Improvements

- Add PDF / OCR document ingestion  
- Persist decisions in a database  
- Implement user authentication  
- Replace rule thresholds with learned models  
- Deploy as a full web service  

---

## License

This project is for educational and portfolio purposes.  

© 2026 Tala Nasarah. All rights reserved.

---
