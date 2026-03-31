# Audit-Ready AI Claims Processing Pipeline

## Overview

This project simulates a real-world, production-oriented insurance claims processing system powered by AI, with a strong focus on auditability, human-in-the-loop decision making, and structured data extraction.

The system takes messy, unstructured insurance claim inputs and transforms them into validated, risk-scored, and reviewable outputs through a multi-stage pipeline. It is designed to reflect how modern AI systems should be built in business environments: not as black boxes, but as controlled systems with validation, explainability, traceability, and escalation paths for uncertain cases.

The project reflects key principles of AI-driven claims automation systems:

- Structured and reliable data extraction
- Transparent validation and scoring
- Human oversight for uncertain cases
- End-to-end traceability
- Continuous improvement through human feedback

This approach aligns closely with the type of system design used by companies such as Lynxia, where automation is combined with control, explainability, and flexibility.

## Objectives

This project demonstrates how AI can be used to:

- Extract structured data from unstructured claim text
- Validate outputs using domain-specific rules
- Detect inconsistencies and assign risk levels
- Learn from past human corrections through a rule-based memory layer
- Route uncertain cases to human review
- Provide interfaces for both internal teams and customers
- Ensure auditability of important actions and outcomes

## Why This Project

This system simulates a production-oriented AI claims pipeline.

Instead of trusting AI outputs blindly, it introduces multiple control layers:

- Multi-layer validation
- Explainable risk scoring
- Human-in-the-loop workflows
- Audit logging and traceability
- Learning from human corrections

This reflects how real AI systems are deployed in operational environments, where accuracy, explainability, control, and accountability matter as much as automation.

## Core Features

- Synthetic data generation to create realistic messy claim inputs and exact ground truth labels
- Three extraction versions (V1, V2, V3) showing the evolution of prompt design and pipeline maturity
- Safe-mode cleaning to standardize critical fields without corrupting the original meaning
- Evaluation module to compare predictions against ground truth and compute accuracy
- RAG-style validation using business rules and learned correction patterns
- Consistency analysis to measure AI output stability across repeated runs
- Explainable risk scoring with numeric scores, levels, and reasons
- Human review queue with recommended reviewer actions
- Internal dashboard for inspection, correction, and audit tracking
- Customer portal for claim lookup, status checking, and feedback
- SQLite persistence layer for claims, AI results, reviews, customer feedback, and audit logs
- FastAPI service for claim processing and structured responses
- Dockerized backend for reproducible setup

## System Architecture

The pipeline consists of the following stages:

### 1. Data Generation

This stage creates synthetic but realistic claim data for the rest of the pipeline.

Outputs:
- Messy, human-like raw claim text
- Clean ground truth values for evaluation

### 2. AI Extraction (V1 -> V3)

The extraction layer uses an LLM to convert raw claim text into structured JSON.

Versions:
- V1: basic extraction with simple prompting
- V2: stricter prompt, recovery logic, and controlled noise simulation
- V3: balanced extraction for full-dataset processing, progress tracking, and rate-limit safety

Extracted fields:
- `claim_id`
- `customer_name`
- `claim_date`
- `claim_type`
- `amount`

### 3. Data Cleaning (SAFE MODE)

This stage lightly standardizes extracted data, mainly the `amount` field, while preserving the rest of the information as-is.

Goals:
- Minimize transformation
- Preserve original meaning
- Avoid aggressive normalization

### 4. Evaluation

This stage compares cleaned predictions against ground truth.

It provides:
- Field-level accuracy
- Overall accuracy
- Detailed mismatch logs for debugging

### 5. Validation (RAG-Style + Learning)

This layer validates claims using a combination of:
- Domain-based rules
- Logical checks
- Learned correction patterns from past human feedback

Checks include:
- Missing fields
- Amount ranges
- Date format and future dates
- Domain consistency
- Learned instability signals

Outputs:
- Valid / invalid status
- Issues list
- Severity level

### 6. Consistency Analysis (AI Stability)

This module measures how stable AI outputs are across repeated runs on the same claim.

Outputs:
- Consistency score
- Most stable output

### 7. Risk Scoring

This stage assigns a numeric risk score and a categorical risk level.

Risk is based on:
- Missing data
- Value mismatches
- Type mismatches
- Learned instability patterns

Outputs:
- Risk score
- Risk level (`LOW`, `MEDIUM`, `HIGH`)
- Explainable reasons

### 8. Human Review Queue

Invalid or uncertain claims are routed into a review queue for manual handling.

Each review item contains:
- Validation issues
- Recommended action
- Available reviewer actions

### 9. Database and Audit System

The SQLite database stores:
- Claims
- AI results
- Human reviews
- Customer feedback
- Audit logs

This ensures that important decisions and actions are traceable.

### 10. Interfaces

**Internal Dashboard**
- Claim inspection
- Risk analysis
- Stability analysis
- Human review actions
- Audit trail display

**Customer Portal**
- Claim lookup
- Status tracking
- Confirmation / dispute / additional info submission

### 11. API Layer (FastAPI)

The API exposes claim-processing functionality and returns:
- Validation results
- Severity
- Confidence
- Instability flags
- Explanations

### 12. Containerization (Docker)

The backend API is dockerized for:
- Reproducible setup
- Easier deployment
- Environment consistency

## Project Structure

```text
Audit_Ready_Claims_Pipeline/
|
|-- data/
|   |-- insurance_claims.csv
|   `-- processed/
|       |-- extracted_claims.json
|       |-- extracted_claims_v2.json
|       |-- extracted_claims_v3.json
|       |-- cleaned_claims.json
|       |-- validated_claims.json
|       |-- risk_scores.json
|       |-- human_review_queue.json
|       `-- errors.json
|
|-- raw_claims/
|   `-- raw_claims.json
|
|-- ground_truth/
|   `-- ground_truth.json
|
|-- src/
|   |-- api/
|   |   `-- main.py
|   |-- config/
|   |   `-- config.py
|   |-- database/
|   |   `-- db.py
|   |-- learning/
|   |   |-- consistency.py
|   |   `-- correction_memory.py
|   |-- generate_fake_claims.py
|   |-- extract_claims_v1.py
|   |-- extract_claims_v2.py
|   |-- extract_claims_v3.py
|   |-- clean_and_validate.py
|   |-- evaluate.py
|   |-- rag_validation.py
|   |-- risk_scoring.py
|   `-- human_review.py
|
|-- app.py
|-- customer_app.py
|-- claims.db
|-- docker-compose.yml
|-- Dockerfile
|-- requirements.txt
`-- README.md
```

## File Responsibilities

### `src/generate_fake_claims.py`
Generates synthetic claim data and saves both messy raw text and clean ground truth values.

### `src/extract_claims_v1.py`
Runs the first extraction version with a basic prompt and a limited batch for testing.

### `src/extract_claims_v2.py`
Adds stricter prompt instructions, stronger fallback handling, token logging, and noise simulation.

### `src/extract_claims_v3.py`
Processes the full dataset with a balanced prompt, progress tracking, and light rate-limit protection.

### `src/clean_and_validate.py`
Cleans extracted data in safe mode, mainly standardizing the `amount` field while preserving other fields.

### `src/evaluate.py`
Compares cleaned claims against ground truth and computes per-field and overall accuracy.

### `src/rag_validation.py`
Applies domain rules, date checks, missing-field checks, and learned correction patterns to validate claims.

### `src/risk_scoring.py`
Assigns explainable risk scores and risk levels based on mismatches, missing fields, and learned instability.

### `src/human_review.py`
Builds a queue of invalid or uncertain claims and suggests reviewer actions.

### `src/config/config.py`
Centralizes domain-specific claim types and amount thresholds.

### `src/database/db.py`
Defines database creation, saving, retrieval, review updates, customer feedback storage, and audit logging.

### `src/learning/consistency.py`
Measures how stable repeated AI outputs are and returns a consistency score.

### `src/learning/correction_memory.py`
Tracks which fields are frequently corrected by humans and summarizes those patterns.

### `src/api/main.py`
Exposes the claim-processing API and combines validation, confidence, instability detection, and persistence.

### `app.py`
Internal Streamlit dashboard for reviewers, risk inspection, stability inspection, human actions, and audit trail display.

### `customer_app.py`
Customer-facing portal to search a claim, view status, and send feedback.

## Running the Project

### Recommended execution flow

The project is best understood and tested in this order:

1. Start the backend service
2. Open a shell inside the running container
3. Set environment variables
4. Generate synthetic claims
5. Run extraction
6. Clean outputs
7. Evaluate accuracy
8. Validate claims
9. Score risks
10. Build the human review queue
11. Open the interfaces

## Running the Project (Dockerized Backend)

### 1. Build and start the backend service

```bash
docker-compose up --build
```

What it does:
Builds the Docker image and starts the FastAPI backend service.

### 2. Access the API

- API root: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

What it does:
Lets you verify that the backend is running and test endpoints directly in the browser.

### 3. Open a shell inside the running container

```bash
docker-compose exec api bash
```

If that does not work, use:

```bash
docker exec -it claims_api bash
```

What it does:
Opens an interactive shell inside the backend container so pipeline commands run in the same Docker environment as the API.

## Run the Full Pipeline (inside the container)

### 4. Set the Python path

```bash
export PYTHONPATH=/app
```

What it does:
Ensures Python can correctly resolve imports from the `src` package.

### 5. Set the OpenAI API key

```bash
export OPENAI_API_KEY="your_actual_openai_key_here"
```

What it does:
Allows the extraction scripts to call the OpenAI API.

### 6. Generate synthetic claims

```bash
python src/generate_fake_claims.py
```

What it does:
Creates raw messy claims and matching ground truth labels.

### 7. Run extraction (recommended version)

```bash
python src/extract_claims_v3.py
```

What it does:
Processes the raw claims using the V3 extraction prompt and writes structured outputs.

### 8. Clean extracted data

```bash
python src/clean_and_validate.py
```

What it does:
Standardizes the `amount` field in safe mode and produces cleaned claims for downstream steps.

### 9. Evaluate extraction accuracy

```bash
python src/evaluate.py
```

What it does:
Compares cleaned claims to ground truth and saves detailed mismatch information.

### 10. Run validation

```bash
python src/rag_validation.py
```

What it does:
Applies rule-based and learning-based validation checks and stores the validation results.

### 11. Compute risk scores

```bash
python src/risk_scoring.py
```

What it does:
Assigns risk scores, risk levels, and explanations for each claim.

### 12. Generate human review queue

```bash
python src/human_review.py
```

What it does:
Creates a review queue for invalid, risky, or uncertain claims and recommends reviewer actions.

## Full Docker Pipeline Commands

```bash
docker-compose up --build
```

In a second terminal:

```bash
docker-compose exec api bash
export PYTHONPATH=/app
export OPENAI_API_KEY="your_actual_openai_key_here"

python src/generate_fake_claims.py
python src/extract_claims_v3.py
python src/clean_and_validate.py
python src/evaluate.py
python src/rag_validation.py
python src/risk_scoring.py
python src/human_review.py
```

Then open:

- `http://localhost:8000/docs`

## Running the Interfaces

These Streamlit apps are usually run outside Docker unless they are explicitly containerized too.

### Internal Dashboard

```bash
streamlit run app.py
```

What it does:
Opens the internal dashboard for reviewers to inspect claims, risk, validation, review actions, and audit-related information.

### Customer Portal

```bash
streamlit run customer_app.py
```

What it does:
Opens the customer-facing portal for claim lookup, status tracking, and feedback submission.

## How to Test the System

After running the pipeline, verify the following:

1. `raw_claims/raw_claims.json` exists and contains messy claim text
2. `ground_truth/ground_truth.json` exists and contains clean reference labels
3. `data/processed/extracted_claims_v3.json` is created after extraction
4. `data/processed/cleaned_claims.json` is created after cleaning
5. `data/processed/errors.json` is created after evaluation
6. `data/processed/validated_claims.json` is created after validation
7. `data/processed/risk_scores.json` is created after risk scoring
8. `data/processed/human_review_queue.json` is created after review queue generation
9. `claims.db` contains records for claims, AI results, reviews, customer feedback, and audit logs
10. `http://localhost:8000/docs` opens successfully
11. The internal dashboard loads claims and system components
12. The customer portal allows claim lookup and feedback submission

## Example Test Scenarios

### API test

Open `http://localhost:8000/docs` and test the available endpoints with sample payloads.

### Dashboard test

Open the internal dashboard and verify that:
- claim selection works
- risk information appears
- validation information appears
- human review actions are available
- audit-related information is visible where implemented

### Customer portal test

Open the customer portal and verify that:
- a valid claim ID can be searched
- claim details appear
- status is shown
- feedback actions store customer responses

## Expected Output Files

The most important files to verify after a full run are:

- `raw_claims/raw_claims.json`
- `ground_truth/ground_truth.json`
- `data/processed/extracted_claims_v3.json`
- `data/processed/cleaned_claims.json`
- `data/processed/errors.json`
- `data/processed/validated_claims.json`
- `data/processed/risk_scores.json`
- `data/processed/human_review_queue.json`
- `claims.db`

## Key Design Decisions

### Human-in-the-Loop

AI outputs are not fully trusted. Uncertain or invalid cases are escalated to humans.

### Auditability

Important decisions are traceable through validation issues, explanations, stored results, and audit logs.

### Learning from Feedback

The system adapts based on past human corrections through a rule-based memory layer.

### Controlled Cleaning

Data cleaning is intentionally conservative to avoid information loss.

### Hybrid Validation

Validation combines static business rules with dynamic correction patterns learned from reviewers.

### Risk-Based Prioritization

Claims are prioritized using explainable risk scoring so critical cases can be reviewed first.

### Dockerized Backend

The backend is containerized for reproducibility and easier setup across environments.

## Technologies Used

- Python
- FastAPI
- Streamlit
- SQLite
- Docker / Docker Compose
- OpenAI API

## Limitations

- Simplified amount normalization
- Fixed thresholds for some validation and risk rules
- Rule-based learning instead of machine learning
- No authentication or role-based access control
- Synthetic data instead of real claim documents
- No OCR or PDF ingestion in the current version
- Streamlit apps are not containerized in the current setup

## Possible Improvements

- Add OCR and PDF ingestion
- Improve numeric parsing for currencies and decimals
- Add authentication and role management
- Containerize the Streamlit interfaces as well
- Replace some rule-based logic with learned models
- Add automated tests
- Deploy the system to a cloud environment

## License

This project is for educational and portfolio purposes.

© 2026 Tala Nasarah. All rights reserved.
