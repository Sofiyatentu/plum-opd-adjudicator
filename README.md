# Plum OPD Adjudicator

> AI-powered OPD (Out-Patient Department) claim adjudication system for Plum Insurance. Automates the evaluation of medical claims against policy terms with a transparent, 6-step decision pipeline.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (backend)
- **Node.js 18+** (frontend)
- **Git**

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install aiosqlite  # for local SQLite development

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The backend starts at **http://localhost:8000**. API docs at **http://localhost:8000/docs**.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local (if not present)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local

# Run development server
npm run dev
```

The frontend starts at **http://localhost:3000**.

### Run Tests

```bash
cd backend
.venv\Scripts\pytest -v
# Expected: 20 passed (TC001-TC010 × 2)
```

---

## 🏗️ Architecture

```
plum-opd-adjudicator/
├── backend/                    # FastAPI (Python)
│   ├── app/
│   │   ├── api/               # REST endpoints (claims, members, admin)
│   │   ├── models/            # SQLAlchemy ORM models (8 tables)
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # Business logic layer
│   │   ├── rules/             # Adjudication engine + policy loader
│   │   ├── utils/             # Validators, logging
│   │   ├── config.py          # Settings (env-based)
│   │   ├── database.py        # Async DB engine (SQLite/PostgreSQL)
│   │   └── main.py            # FastAPI app entry point
│   ├── tests/
│   │   └── test_adjudication.py  # TC001-TC010 test suite
│   └── requirements.txt
├── frontend/                   # Next.js 15 (TypeScript)
│   ├── src/
│   │   ├── app/               # Pages (home, submit, claims, claim detail)
│   │   ├── components/ui/     # Reusable UI components (shadcn/ui)
│   │   └── lib/               # API client, types, utilities
│   ├── tailwind.config.ts
│   └── package.json
├── policy_terms.json           # Insurance policy configuration
├── test_cases.json             # TC001-TC010 test case definitions
└── adjudication_rules.md       # Business rules specification
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐ │
│  │  Submit   │  │  Claims   │  │  Claim Detail    │ │
│  │  Page     │  │  List     │  │  (with steps)    │ │
│  └────┬─────┘  └─────┬─────┘  └────────┬─────────┘ │
│       │               │                 │           │
│       └───────────────┴─────────────────┘           │
│                       │ REST API                    │
└───────────────────────┼─────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────┐
│              Backend (FastAPI)                       │
│                       │                              │
│  ┌────────────────────▼─────────────────────────┐   │
│  │           API Layer (claims.py, etc.)         │   │
│  └────────────────────┬─────────────────────────┘   │
│                       │                              │
│  ┌────────────────────▼─────────────────────────┐   │
│  │         Service Layer (claim_service)         │   │
│  │  ┌─────────────┐  ┌──────────────────────┐   │   │
│  │  │ Doc Extract │  │ Adjudication Service  │   │   │
│  │  └──────┬──────┘  └──────────┬───────────┘   │   │
│  └─────────┼────────────────────┼───────────────┘   │
│            │                    │                    │
│  ┌─────────▼────────────────────▼───────────────┐   │
│  │          Rules Engine (6 Steps)               │   │
│  │  1. Eligibility  │ 2. Documentation          │   │
│  │  3. Coverage     │ 4. Limits                 │   │
│  │  5. Necessity    │ 6. Fraud Detection        │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│  ┌──────────────────▼───────────────────────────┐   │
│  │         Policy Loader (policy_terms.json)     │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │    Database (SQLite local / PostgreSQL prod)  │   │
│  │  members │ claims │ steps │ documents │ etc.  │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Decision Logic Flowchart

```
Claim Submitted
      │
      ▼
┌─────────────────────────┐
│ Step 1: ELIGIBILITY     │
│ • Member active?        │
│ • Policy effective?     │
│ • Submission in window? │
│ • Waiting period met?   │
└──────────┬──────────────┘
           │ Pass?
    ┌──────┴──────┐
    │ No          │ Yes
    ▼             ▼
 REJECTED   ┌─────────────────────────┐
            │ Step 2: DOCUMENTATION   │
            │ • Prescription present? │
            │ • Bill present?         │
            │ • Doctor reg valid?     │
            └──────────┬──────────────┘
                       │ Pass?
                ┌──────┴──────┐
                │ No          │ Yes
                ▼             ▼
             REJECTED   ┌─────────────────────────┐
                        │ Step 3: COVERAGE        │
                        │ • Diagnosis covered?    │
                        │ • Not excluded?         │
                        │ • Pre-auth if needed?   │
                        └──────────┬──────────────┘
                                   │ Pass?
                            ┌──────┴──────┐
                            │ No          │ Yes
                            ▼             ▼
                         REJECTED   ┌─────────────────────────┐
                                    │ Step 4: LIMITS          │
                                    │ • Annual limit check    │
                                    │ • Per-claim max check   │
                                    │ • Category sub-limits   │
                                    │ • Co-pay application    │
                                    │ • Network discount      │
                                    └──────────┬──────────────┘
                                               │
                                               ▼
                                    ┌─────────────────────────┐
                                    │ Step 5: NECESSITY       │
                                    │ • Diagnosis-treatment   │
                                    │   alignment             │
                                    │ • Reasonable cost?      │
                                    └──────────┬──────────────┘
                                               │
                                               ▼
                                    ┌─────────────────────────┐
                                    │ Step 6: FRAUD DETECTION │
                                    │ • Duplicate claims?     │
                                    │ • Amount anomalies?     │
                                    │ • Missing/invalid docs? │
                                    └──────────┬──────────────┘
                                               │
                                        ┌──────┴──────┐
                                        │             │
                                        ▼             ▼
                                  Fraud Found?   No Fraud
                                        │             │
                                        ▼             ▼
                                  MANUAL_REVIEW  ┌──────────┐
                                                 │ COMPUTE  │
                                                 │ DECISION │
                                                 └────┬─────┘
                                                      │
                                               ┌──────┴──────┐
                                               │             │
                                               ▼             ▼
                                    approved == claimed   approved < claimed
                                               │             │
                                               ▼             ▼
                                           APPROVED      PARTIAL
```

---

## 📡 API Documentation

### Base URL: `http://localhost:8000/api`

### Health Check
```
GET /api/health
→ { "status": "ok", "service": "Plum OPD Adjudicator", "version": "0.1.0" }
```

### Submit Claim
```
POST /api/claims
Content-Type: application/json

{
  "member_id": "EMP001",
  "member_name": "Rajesh Kumar",
  "treatment_date": "2025-06-01",
  "claim_amount": 1500,
  "hospital": "Apollo Hospitals",
  "cashless_request": false,
  "documents": {
    "prescription": {
      "doctor_name": "Dr. Sharma",
      "doctor_reg": "KA/45678/2015",
      "diagnosis": "Viral fever",
      "medicines_prescribed": ["Paracetamol 650mg"]
    },
    "bill": {
      "consultation_fee": 1000,
      "medicines": 500
    }
  }
}

→ { "claim_id": "uuid", "status": "completed" }
```

### Get Claim Detail
```
GET /api/claims/{claim_id}

→ {
    "id": "uuid",
    "claim_code": "CLM_01001",
    "decision": "APPROVED",
    "approved_amount": 1350.0,
    "confidence_score": 0.92,
    "adjudication_steps": [ ... ],
    "rejection_reasons": [ ... ],
    "fraud_flags": [ ... ],
    ...
  }
```

### List Claims by Member
```
GET /api/claims?member_id=EMP001

→ { "claims": [ ... ], "total": 5 }
```

### File Appeal
```
POST /api/claims/{claim_id}/appeal
Content-Type: application/json

{ "reason": "Treatment was medically necessary" }

→ { "appeal_id": "uuid", "status": "pending" }
```

### Get Member Summary
```
GET /api/members/{member_id}

→ {
    "member_code": "EMP001",
    "name": "Rajesh Kumar",
    "ytd_claimed": 5000,
    "remaining_annual": 95000,
    "remaining_family_floater": 100000,
    "is_active": true
  }
```

### Admin Stats
```
GET /api/admin/stats

→ {
    "total_claims": 150,
    "approved_count": 120,
    "rejected_count": 15,
    "partial_count": 10,
    "manual_review_count": 5,
    "total_approved_amount": 450000.0,
    "average_confidence": 0.88
  }
```

### Admin Policy Terms
```
GET /api/admin/policy

→ { full policy_terms.json content }
```

Full interactive API documentation available at **http://localhost:8000/docs** (Swagger UI).

---

## 📋 Test Cases (TC001-TC010)

| Test Case | Scenario | Expected Decision | Expected Amount |
|-----------|----------|-------------------|-----------------|
| TC001 | Simple consultation – viral fever | APPROVED | ₹1,350 |
| TC002 | Dental – root canal (sub-limit cap) | PARTIAL | ₹5,000 |
| TC003 | Per-claim limit exceeded (₹12,000) | REJECTED | ₹0 |
| TC004 | Missing prescription documents | REJECTED | ₹0 |
| TC005 | Diabetes – 90-day waiting period | REJECTED | ₹0 |
| TC006 | Alternative medicine (Ayurveda) | APPROVED | ₹3,600 |
| TC007 | MRI – pre-authorization missing | REJECTED | ₹0 |
| TC008 | Fraud pattern – multiple same-day claims | MANUAL_REVIEW | ₹0 |
| TC009 | Weight loss treatment – excluded | REJECTED | ₹0 |
| TC010 | Network hospital – cashless approved | APPROVED | ₹8,000 |

All 20 tests pass (10 individual + 10 parameterized meta-tests).

---

## 📝 Assumptions

1. **Policy Source of Truth**: `policy_terms.json` is the single source for all limits, sub-limits, exclusions, and coverage rules.

2. **No Real OCR/AI**: Document data is submitted as structured JSON via the API. The system is designed for GPT-4o Vision integration but currently processes pre-extracted data for reliability.

3. **SQLite for Local Dev**: The system defaults to SQLite for zero-setup local development. PostgreSQL is supported for production by changing `DATABASE_URL` in `.env`.

4. **Co-pay Logic**: 10% co-pay applied on the approved amount for standard (non-network, non-cashless) consultations. Network/cashless claims have zero co-pay.

5. **Sub-limits**: Category sub-limits (dental: ₹5,000/claim, diagnostic: ₹3,000/claim, alternative medicine: ₹4,000/claim) are applied per-item, not globally.

6. **Waiting Periods**: Pre-existing conditions (diabetes, hypertension) have a 90-day waiting period from member join date. Joint replacement requires 730 days.

7. **Fraud Detection**: Uses simple heuristic rules (duplicate claims, high amounts, missing docs) rather than ML models. Flagged claims go to MANUAL_REVIEW.

8. **Pre-authorization**: Diagnostic procedures (MRI, CT scan, etc.) above ₹2,000 require pre-authorization. Claims without it are rejected.

9. **Member Auto-creation**: Unknown member IDs create new member records automatically for testing convenience.

10. **Network Hospital Matching**: Uses fuzzy string matching (Levenshtein distance) against the `network_hospitals` list in policy_terms.json.

11. **Claim Submission Window**: Claims must be submitted within 30 days of treatment date.

12. **Confidence Scoring**: Calculated based on document completeness and validation pass rate, not from a trained model.

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python 3.11, FastAPI, SQLAlchemy (async), Pydantic v2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Testing | pytest (20 test cases) |
| Document Processing | Structured JSON input (GPT-4o Vision ready) |
| Deployment | Docker-ready (Dockerfiles included) |

---

## 🐳 Docker Deployment

```bash
# Backend
cd backend
docker build -t plum-opd-backend .
docker run -p 8000:8000 plum-opd-backend

# Frontend
cd frontend
docker build -t plum-opd-frontend .
docker run -p 3000:3000 plum-opd-frontend
```

---

## 📜 License

Internal project for Plum Insurance AI Automation Pod.
