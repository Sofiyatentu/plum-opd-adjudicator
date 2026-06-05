# Assumptions

## Architecture
- The adjudication engine is a stateless Python class that can run without a database, tested standalone against test_cases.json.
- Policy terms are loaded from `policy_terms.json` at startup and cached in memory.
- The backend API supports both file upload (FormData) and structured JSON input; the test suite uses JSON input only.

## Adjudication Engine

### Step 1 — Basic Eligibility
- All members are assumed active unless `member_join_date` is provided, in which case waiting periods are checked.
- Specific ailment waiting periods (diabetes=90d, hypertension=90d, joint replacement=730d) are checked by keyword matching on diagnosis text.
- Submission date defaults to treatment date if not explicitly provided (tests verify eligibility only via join_date).

### Step 2 — Document Validation
- Doctor registration is validated against format `[StateCode]/[Number]/[Year]` (e.g. `KA/45678/2015`).
- Alternative medicine practitioners use format `AYUR/[StateCode]/[Number]/[Year]` (e.g. `AYUR/KL/2345/2019`).
- The prescription and bill documents are required; missing prescription triggers `MISSING_DOCUMENTS`.

### Step 3 — Coverage Verification
- Weight loss / bariatric / obesity diagnoses trigger `SERVICE_NOT_COVERED`.
- Dental procedures are split: covered procedures (Root canal, Filling, Extraction, Cleaning) vs cosmetic (Teeth whitening).
- MRI and CT scans require pre-authorization for claims above ₹10,000 (per TC007).
- Alternative medicine (Ayurveda, Homeopathy, Unani) is covered under the alternative_medicine sub-limit.

### Step 4 — Limit Validation
- Per-claim limit: ₹5,000 per the policy.
- Co-pay of 10% applies to consultation category claims.
- Network cashless claims at Apollo/Fortis/Max etc. get 20% network discount on top of co-pay.
- Dental sub-limit: ₹10,000. Alternative medicine sub-limit: ₹8,000.

### Step 5 — Medical Necessity
- Diagnosis must align with prescribed medicines/procedures/tests.
- Experimental treatments are rejected.
- Weight loss and cosmetic procedures are excluded.

### Step 6 — Fraud Detection
- Claims with `previous_claims_same_day >= 3` (total ≥4) trigger manual review with fraud flags.
- `previous_claims_same_day >= 2` also adds an "unusual pattern" flag.

### Decision Logic
- Fraud flags → MANUAL_REVIEW (regardless of other results, per priority rule: safety first).
- Partial coverage (e.g. dental with cosmetic items) → PARTIAL.
- Any hard failure in steps 1-4 → REJECTED.
- All steps pass → APPROVED.

## Test Cases
- TC001: Approved with 10% co-pay (₹1500 → ₹1350).
- TC002: Partial — root canal covered (₹8,000), teeth whitening excluded.
- TC003: Rejected — ₹7,500 exceeds ₹5,000 per-claim limit.
- TC004: Rejected — missing prescription document.
- TC005: Rejected — type 2 diabetes within 90-day waiting period (only 44 days elapsed).
- TC006: Approved — Ayurvedic panchakarma therapy within alt medicine sub-limit.
- TC007: Rejected — MRI without pre-authorization, claim above ₹10,000.
- TC008: Manual review — 4 claims on same day triggers fraud flags.
- TC009: Rejected — weight loss / bariatric excluded.
- TC010: Approved — Apollo Hospitals network, cashless, 10% co-pay + 20% discount (₹4,500 → ₹3,600).

## Omitted Features
- No actual OCR/image processing — expects structured JSON from frontend or test harness.
- No GPT-4o API integration in the current phase — the adjudication engine works on structured data.
- No annual limit tracking across claims — each claim is evaluated independently for now.
- No duplicate claim detection across database records — only same-day fraud detection via `previous_claims_same_day`.
- No RAG or few-shot prompting — the engine is purely rule-based.

## Technical
- PostgreSQL via asyncpg as the primary database.
- SQLAlchemy 2.0 async ORM with UUID primary keys.
- FastAPI with async endpoints.
- Frontend expects API at `/api` prefix with JSON responses.
