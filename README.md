# Ajaia LLC — Technical Project Manager Assessment

Technical Project Manager assessment submission based on the **Corrigan Peak Logistics — Dispatch Exception Triage** case study.

**Candidate:** Janhavi Sahasrabudhe  
**Role:** Technical Project Manager  
**Case study target go-live:** September 8

## Project Overview

This assessment demonstrates technical project management, risk-based prioritization, stakeholder communication, data normalization, and practical use of AI tools.

The case study involves preparing a dispatch exception triage workflow for launch while managing engineering risks, client dependencies, operational readiness, and new feature requests.

## Assessment Deliverables

### Task 1 — Prioritization and Risk Management

Evaluates five incoming requests and prioritizes work according to business impact, technical risk, and launch readiness.

Key decisions:

- **P1:** Address duplicate routing risk through idempotency and concurrency safeguards.
- **P2:** Resolve the Terminal 3 EDI schema mismatch affecting urgency scores.
- **P3:** Schedule routing-rule reviews with terminal leads.
- **P4:** Defer automatic backup-carrier reassignment as a scope expansion.
- **P5:** Defer the cosmetic UI color change.

The proposed release approach uses explicit go/no-go criteria rather than assuming the target date guarantees readiness.

### Task 2 — Python Data Normalization

Implements a Python script to clean and validate a sample dispatch exception CSV.

Features include:

- Standardizing terminal names such as `T3` to `Terminal 3`
- Normalizing carrier codes to uppercase
- Converting supported timestamps to consistent ISO 8601 formatting
- Preserving timezone information without inventing missing offsets
- Counting exceptions by event type
- Flagging incomplete records for manual review
- Generating a cleaned CSV output

### Task 3 — Stakeholder Communication

Provides a stakeholder email explaining launch priorities, technical dependencies, scope decisions, and next steps.

### Task 4 — AI-Assisted Workflow

Documents how AI can support project management and coding tasks while retaining human review, validation, and accountability.

## Repository Structure

```text
ajaia-technical-pm-assessment/
├── README.md
├── submission.md
├── normalize_exceptions.py
├── test_normalize.py
├── exceptions_raw.csv
└── cleaned_exceptions.csv
```

| File | Description |
|---|---|
| `submission.md` | Written responses to the assessment tasks |
| `normalize_exceptions.py` | Python CSV normalization script |
| `test_normalize.py` | Automated unit test |
| `exceptions_raw.csv` | Original sample exception data |
| `cleaned_exceptions.csv` | Normalized output with review flags |

## How to Run

### Requirements

- Python 3.9 or later
- No external Python packages required

### Run the normalization script

```bash
python normalize_exceptions.py exceptions_raw.csv --output cleaned_exceptions.csv
```

### Run the automated test

```bash
python -m unittest -v test_normalize.py
```

## Sample Results

The sample dataset contains five exception records.

| Event Type | Count |
|---|---:|
| Missed pickup | 2 |
| Document mismatch | 2 |
| Carrier substitution | 1 |
| **Total** | **5** |

**Data-quality finding:** Exception `CPX-88216` has a missing carrier code and is flagged for manual review rather than assigned an assumed value.

Timestamps without explicit timezone information retain their original wall-clock time and are annotated accordingly.

## Project Management Approach

The assessment follows five principles:

1. **Protect operational reliability:** Prioritize duplicate-routing prevention and data integrity.
2. **Manage dependencies proactively:** Escalate blocked client inputs and identify accountable owners.
3. **Control scope:** Separate launch-critical work from enhancements.
4. **Validate readiness:** Require technical testing and operational sign-off before go-live.
5. **Communicate transparently:** Explain decisions, trade-offs, risks, and next steps to stakeholders.

## Important Assumptions and Limitations

- The dataset is a five-record sample, not a production export.
- The normalization script does not resolve the production EDI-to-urgency-score integration defect.
- Missing carrier codes are not inferred.
- Timezone offsets are not assumed for timestamps that lack them.
- Production launch readiness requires additional integration testing, routing safeguards, and stakeholder approval.

## Assessment Submission

The complete written assessment is available in [`submission.md`](submission.md).

This repository contains the supporting code, sample input, normalized output, and automated test.

---

*Prepared for the Ajaia LLC Technical Project Manager assessment.*
