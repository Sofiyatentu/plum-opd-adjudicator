"""Test adjudication engine against all 10 test cases from test_cases.json."""
import pytest
from datetime import date


def _build_claim_data(tc):
    """Convert test case input_data to the format expected by the engine."""
    input_data = tc["input_data"]
    documents = input_data.get("documents", {})

    claim_data = {
        "member_id": input_data.get("member_id", ""),
        "member_name": input_data.get("member_name", ""),
        "member_join_date": input_data.get("member_join_date"),
        "treatment_date": input_data.get("treatment_date"),
        "claim_amount": float(input_data.get("claim_amount", 0)),
        "hospital": input_data.get("hospital", ""),
        "cashless_request": input_data.get("cashless_request", False),
        "previous_claims_same_day": int(input_data.get("previous_claims_same_day", 0)),
        "documents": documents,
    }

    # Extract diagnosis from prescription
    prescription = documents.get("prescription", {})
    if prescription:
        claim_data["diagnosis"] = prescription.get("diagnosis", "")

    return claim_data


# ── TC001: Simple Consultation - Approved ─────────────────────────────────

def test_tc001_simple_consultation_approved(engine):
    tc = {
        "case_id": "TC001",
        "input_data": {
            "member_id": "EMP001",
            "member_name": "Rajesh Kumar",
            "treatment_date": "2024-11-01",
            "claim_amount": 1500,
            "documents": {
                "prescription": {
                    "doctor_name": "Dr. Sharma",
                    "doctor_reg": "KA/45678/2015",
                    "diagnosis": "Viral fever",
                    "medicines_prescribed": ["Paracetamol 650mg", "Vitamin C"],
                },
                "bill": {
                    "consultation_fee": 1000,
                    "diagnostic_tests": 500,
                    "test_names": ["CBC", "Dengue test"],
                },
            },
        },
        "expected_output": {
            "decision": "APPROVED",
            "approved_amount": 1350,
            "deductions": {"copay": 150},
            "confidence_score": 0.95,
        },
    }
    data = _build_claim_data(tc)
    result = engine.adjudicate(data)

    expected = tc["expected_output"]
    assert result.decision == expected["decision"], f"Expected {expected['decision']}, got {result.decision}"
    assert result.approved_amount == pytest.approx(expected["approved_amount"], rel=0.01), \
        f"Expected ~{expected['approved_amount']}, got {result.approved_amount}"
    assert result.confidence_score >= 0.80, f"Confidence too low: {result.confidence_score}"
    print(f"  TC001 PASS: {result.decision} ₹{result.approved_amount:,.0f} (confidence: {result.confidence_score})")


# ── TC002: Dental Treatment - Partial Approval ───────────────────────────

def test_tc002_dental_partial_approval(engine):
    tc = {
        "case_id": "TC002",
        "input_data": {
            "member_id": "EMP002",
            "member_name": "Priya Singh",
            "treatment_date": "2024-10-15",
            "claim_amount": 12000,
            "documents": {
                "prescription": {
                    "doctor_name": "Dr. Patel",
                    "doctor_reg": "MH/23456/2018",
                    "diagnosis": "Tooth decay requiring root canal",
                    "procedures": ["Root canal treatment", "Teeth whitening"],
                },
                "bill": {
                    "root_canal": 8000,
                    "teeth_whitening": 4000,
                },
            },
        },
        "expected_output": {
            "decision": "PARTIAL",
            "approved_amount": 8000,
            "rejected_items": ["Teeth whitening - cosmetic procedure"],
        },
    }
    data = _build_claim_data(tc)
    result = engine.adjudicate(data)

    expected = tc["expected_output"]
    assert result.decision == expected["decision"], f"Expected {expected['decision']}, got {result.decision}"
    assert result.approved_amount == pytest.approx(expected["approved_amount"], rel=0.01), \
        f"Expected ~{expected['approved_amount']}, got {result.approved_amount}"
    print(f"  TC002 PASS: {result.decision} ₹{result.approved_amount:,.0f}")


# ── TC003: Limit Exceeded - Rejected ─────────────────────────────────────

def test_tc003_per_claim_limit_rejected(engine):
    tc = {
        "case_id": "TC003",
        "input_data": {
            "member_id": "EMP003",
            "member_name": "Amit Verma",
            "treatment_date": "2024-10-20",
            "claim_amount": 7500,
            "documents": {
                "prescription": {
                    "doctor_name": "Dr. Gupta",
                    "doctor_reg": "DL/34567/2016",
                    "diagnosis": "Gastroenteritis",
                    "medicines_prescribed": ["Antibiotics", "Probiotics"],
                },
                "bill": {
                    "consultation_fee": 2000,
                    "medicines": 5500,
                },
            },
        },
        "expected_output": {
            "decision": "REJECTED",
            "rejection_reasons": ["PER_CLAIM_EXCEEDED"],
            "confidence_score": 0.98,
        },
    }
    data = _build_claim_data(tc)
    result = engine.adjudicate(data)

    expected = tc["expected_output"]
    assert result.decision == expected["decision"], f"Expected {expected['decision']}, got {result.decision}"
    rejection_codes = [r["reason_code"] for r in result.rejection_reasons]
    assert any(code in rejection_codes for code in expected["rejection_reasons"]), \
        f"Missing expected rejection: {expected['rejection_reasons']} in {rejection_codes}"
    print(f"  TC003 PASS: {result.decision} — {rejection_codes}")


# ── TC004: Missing Documents - Rejected ──────────────────────────────────

def test_tc004_missing_documents_rejected(engine):
    tc = {
        "case_id": "TC004",
        "input_data": {
            "member_id": "EMP004",
            "member_name": "Sneha Reddy",
            "treatment_date": "2024-10-25",
            "claim_amount": 2000,
            "documents": {
                "bill": {
                    "consultation_fee": 1500,
                    "medicines": 500,
                },
            },
        },
        "expected_output": {
            "decision": "REJECTED",
            "rejection_reasons": ["MISSING_DOCUMENTS"],
            "confidence_score": 1.0,
        },
    }
    data = _build_claim_data(tc)
    result = engine.adjudicate(data)

    expected = tc["expected_output"]
    assert result.decision == expected["decision"], f"Expected {expected['decision']}, got {result.decision}"
    rejection_codes = [r["reason_code"] for r in result.rejection_reasons]
    assert "MISSING_DOCUMENTS" in rejection_codes, f"Expected MISSING_DOCUMENTS, got {rejection_codes}"
    print(f"  TC004 PASS: {result.decision} — {rejection_codes}")


# ── TC005: Pre-existing Condition - Waiting Period ───────────────────────

def test_tc005_diabetes_waiting_period(engine):
    tc = {
        "case_id": "TC005",
        "input_data": {
            "member_id": "EMP005",
            "member_name": "Vikram Joshi",
            "member_join_date": "2024-09-01",
            "treatment_date": "2024-10-15",
            "claim_amount": 3000,
            "documents": {
                "prescription": {
                    "doctor_name": "Dr. Mehta",
                    "doctor_reg": "GJ/56789/2014",
                    "diagnosis": "Type 2 Diabetes",
                    "medicines_prescribed": ["Metformin", "Glimepiride"],
                },
                "bill": {
                    "consultation_fee": 1000,
                    "medicines": 2000,
                },
            },
        },
        "expected_output": {
            "decision": "REJECTED",
            "rejection_reasons": ["WAITING_PERIOD"],
            "confidence_score": 0.96,
        },
    }
    data = _build_claim_data(tc)
    result = engine.adjudicate(data)

    expected = tc["expected_output"]
    assert result.decision == expected["decision"], f"Expected {expected['decision']}, got {result.decision}"
    rejection_codes = [r["reason_code"] for r in result.rejection_reasons]
    assert "WAITING_PERIOD" in rejection_codes, f"Expected WAITING_PERIOD, got {rejection_codes}"
    # Check the specific note about eligible date
    assert "90-day" in result.notes.lower() or "eligible from" in result.notes.lower(), \
        f"Notes should mention waiting period: {result.notes}"
    print(f"  TC005 PASS: {result.decision} — {rejection_codes}")


# ── TC006: Alternative Medicine - Approved ───────────────────────────────

def test_tc006_alternative_medicine_approved(engine):
    tc = {
        "case_id": "TC006",
        "input_data": {
            "member_id": "EMP006",
            "member_name": "Kavita Nair",
            "treatment_date": "2024-10-28",
            "claim_amount": 4000,
            "documents": {
                "prescription": {
                    "doctor_name": "Vaidya Krishnan",
                    "doctor_reg": "AYUR/KL/2345/2019",
                    "diagnosis": "Chronic joint pain",
                    "treatment": "Panchakarma therapy",
                },
                "bill": {
                    "consultation_fee": 1000,
                    "therapy_charges": 3000,
                },
            },
        },
        "expected_output": {
            "decision": "APPROVED",
            "approved_amount": 4000,
        },
    }
    data = _build_claim_data(tc)
    result = engine.adjudicate(data)

    expected = tc["expected_output"]
    assert result.decision == expected["decision"], f"Expected {expected['decision']}, got {result.decision}"
    assert result.approved_amount == pytest.approx(expected["approved_amount"], rel=0.01), \
        f"Expected ~{expected['approved_amount']}, got {result.approved_amount}"
    print(f"  TC006 PASS: {result.decision} ₹{result.approved_amount:,.0f} (confidence: {result.confidence_score})")


# ── TC007: MRI without Pre-auth - Rejected ───────────────────────────────

def test_tc007_mri_preauth_missing(engine):
    tc = {
        "case_id": "TC007",
        "input_data": {
            "member_id": "EMP007",
            "member_name": "Suresh Patil",
            "treatment_date": "2024-11-02",
            "claim_amount": 15000,
            "documents": {
                "prescription": {
                    "doctor_name": "Dr. Rao",
                    "doctor_reg": "AP/67890/2017",
                    "diagnosis": "Suspected lumbar disc herniation",
                    "tests_prescribed": ["MRI Lumbar Spine"],
                },
                "bill": {
                    "mri_scan": 15000,
                },
            },
        },
        "expected_output": {
            "decision": "REJECTED",
            "rejection_reasons": ["PRE_AUTH_MISSING"],
        },
    }
    data = _build_claim_data(tc)
    result = engine.adjudicate(data)

    expected = tc["expected_output"]
    assert result.decision == expected["decision"], f"Expected {expected['decision']}, got {result.decision}"
    rejection_codes = [r["reason_code"] for r in result.rejection_reasons]
    assert "PRE_AUTH_MISSING" in rejection_codes, f"Expected PRE_AUTH_MISSING, got {rejection_codes}"
    print(f"  TC007 PASS: {result.decision} — {rejection_codes}")


# ── TC008: Fraud Detection - Manual Review ───────────────────────────────

def test_tc008_fraud_manual_review(engine):
    tc = {
        "case_id": "TC008",
        "input_data": {
            "member_id": "EMP008",
            "member_name": "Ravi Menon",
            "treatment_date": "2024-10-30",
            "claim_amount": 4800,
            "previous_claims_same_day": 3,
            "documents": {
                "prescription": {
                    "doctor_name": "Dr. Khan",
                    "doctor_reg": "UP/45678/2016",
                    "diagnosis": "Migraine",
                    "medicines_prescribed": ["Sumatriptan", "Propranolol"],
                },
                "bill": {
                    "consultation_fee": 2000,
                    "medicines": 2800,
                },
            },
        },
        "expected_output": {
            "decision": "MANUAL_REVIEW",
            "flags": ["Multiple claims same day", "Unusual pattern detected"],
            "confidence_score": 0.65,
        },
    }
    data = _build_claim_data(tc)
    result = engine.adjudicate(data)

    expected = tc["expected_output"]
    assert result.decision == expected["decision"], f"Expected {expected['decision']}, got {result.decision}"
    assert len(result.fraud_flags) >= 2, f"Expected at least 2 fraud flags, got {len(result.fraud_flags)}"
    assert result.confidence_score < 0.80, f"Confidence should be low for manual review: {result.confidence_score}"
    print(f"  TC008 PASS: {result.decision} (confidence: {result.confidence_score})")


# ── TC009: Excluded Treatment - Rejected ─────────────────────────────────

def test_tc009_weight_loss_excluded(engine):
    tc = {
        "case_id": "TC009",
        "input_data": {
            "member_id": "EMP009",
            "member_name": "Anita Desai",
            "treatment_date": "2024-10-18",
            "claim_amount": 8000,
            "documents": {
                "prescription": {
                    "doctor_name": "Dr. Banerjee",
                    "doctor_reg": "WB/34567/2015",
                    "diagnosis": "Obesity - BMI 35",
                    "treatment": "Bariatric consultation and diet plan",
                },
                "bill": {
                    "consultation_fee": 3000,
                    "diet_plan": 5000,
                },
            },
        },
        "expected_output": {
            "decision": "REJECTED",
            "rejection_reasons": ["SERVICE_NOT_COVERED"],
            "confidence_score": 0.97,
        },
    }
    data = _build_claim_data(tc)
    result = engine.adjudicate(data)

    expected = tc["expected_output"]
    assert result.decision == expected["decision"], f"Expected {expected['decision']}, got {result.decision}"
    rejection_codes = [r["reason_code"] for r in result.rejection_reasons]
    assert "SERVICE_NOT_COVERED" in rejection_codes, f"Expected SERVICE_NOT_COVERED, got {rejection_codes}"
    print(f"  TC009 PASS: {result.decision} — {rejection_codes}")


# ── TC010: Network Hospital - Cashless Approved ──────────────────────────

def test_tc010_network_cashless_approved(engine):
    tc = {
        "case_id": "TC010",
        "input_data": {
            "member_id": "EMP010",
            "member_name": "Deepak Shah",
            "treatment_date": "2024-11-03",
            "claim_amount": 4500,
            "hospital": "Apollo Hospitals",
            "cashless_request": True,
            "documents": {
                "prescription": {
                    "doctor_name": "Dr. Iyer",
                    "doctor_reg": "TN/56789/2013",
                    "diagnosis": "Acute bronchitis",
                    "medicines_prescribed": ["Antibiotics", "Bronchodilators"],
                },
                "bill": {
                    "consultation_fee": 1500,
                    "medicines": 3000,
                },
            },
        },
        "expected_output": {
            "decision": "APPROVED",
            "approved_amount": 3600,
            "network_discount": 900,
        },
    }
    data = _build_claim_data(tc)
    result = engine.adjudicate(data)

    expected = tc["expected_output"]
    assert result.decision == expected["decision"], f"Expected {expected['decision']}, got {result.decision}"
    assert result.approved_amount == pytest.approx(expected["approved_amount"], rel=0.01), \
        f"Expected ~{expected['approved_amount']}, got {result.approved_amount}"
    print(f"  TC010 PASS: {result.decision} ₹{result.approved_amount:,.0f}")


# ── Parameterized run for reporting ──────────────────────────────────────

@pytest.mark.parametrize("tc_id", [
    "test_tc001_simple_consultation_approved",
    "test_tc002_dental_partial_approval",
    "test_tc003_per_claim_limit_rejected",
    "test_tc004_missing_documents_rejected",
    "test_tc005_diabetes_waiting_period",
    "test_tc006_alternative_medicine_approved",
    "test_tc007_mri_preauth_missing",
    "test_tc008_fraud_manual_review",
    "test_tc009_weight_loss_excluded",
    "test_tc010_network_cashless_approved",
])
def test_run_all_cases(tc_id, engine):
    """Run all test cases via parametrize for a single summary view."""
    # Run the corresponding test function from globals
    test_func = globals()[tc_id]
    test_func(engine)
