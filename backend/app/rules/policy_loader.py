"""Loads and provides typed access to policy_terms.json."""
import json
import os
from dataclasses import dataclass, field
from typing import Any
from app.config import get_settings


@dataclass
class PolicyTerms:
    policy_id: str
    policy_name: str
    effective_date: str
    annual_limit: float
    per_claim_limit: float
    family_floater_limit: float
    consultation_sub_limit: float
    consultation_copay_pct: float
    network_discount_pct: float
    diagnostic_sub_limit: float
    pharmacy_sub_limit: float
    generic_mandatory: bool
    branded_copay_pct: float
    dental_sub_limit: float
    dental_routine_limit: float
    dental_procedures: list[str]
    dental_cosmetic: bool
    vision_sub_limit: float
    vision_lasik: bool
    alt_medicine_sub_limit: float
    alt_medicine_therapy_limit: int
    covered_treatments: list[str]
    covered_tests: list[str]
    waiting_initial: int
    waiting_pre_existing: int
    waiting_maternity: int
    waiting_specific: dict
    exclusions: list[str]
    required_docs: list[str]
    submission_window_days: int
    minimum_claim_amount: float
    network_hospitals: list[str]
    cashless_available: bool
    instant_approval_limit: float

    raw: dict[str, Any] = field(default_factory=dict)


def _load_policy_terms() -> PolicyTerms:
    settings = get_settings()
    path = settings.policy_terms_path

    # Search multiple locations
    candidates = [
        path,
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "policy_terms.json"),  # backend/
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "policy_terms.json"),  # project root
        os.path.join(os.getcwd(), "policy_terms.json"),
    ]

    resolved = None
    for candidate in candidates:
        abs_path = os.path.abspath(candidate) if not os.path.isabs(candidate) else candidate
        if os.path.exists(abs_path):
            resolved = abs_path
            break

    if not resolved:
        raise FileNotFoundError(
            f"policy_terms.json not found. Searched: {[os.path.abspath(c) for c in candidates]}"
        )

    with open(resolved, "r") as f:
        raw = json.load(f)

    coverage = raw["coverage_details"]
    waiting = raw["waiting_periods"]

    return PolicyTerms(
        policy_id=raw["policy_id"],
        policy_name=raw["policy_name"],
        effective_date=raw["effective_date"],
        annual_limit=float(coverage["annual_limit"]),
        per_claim_limit=float(coverage["per_claim_limit"]),
        family_floater_limit=float(coverage["family_floater_limit"]),
        consultation_sub_limit=float(coverage["consultation_fees"]["sub_limit"]),
        consultation_copay_pct=float(coverage["consultation_fees"]["copay_percentage"]),
        network_discount_pct=float(coverage["consultation_fees"]["network_discount"]),
        diagnostic_sub_limit=float(coverage["diagnostic_tests"]["sub_limit"]),
        pharmacy_sub_limit=float(coverage["pharmacy"]["sub_limit"]),
        generic_mandatory=coverage["pharmacy"]["generic_drugs_mandatory"],
        branded_copay_pct=float(coverage["pharmacy"]["branded_drugs_copay"]),
        dental_sub_limit=float(coverage["dental"]["sub_limit"]),
        dental_routine_limit=float(coverage["dental"]["routine_checkup_limit"]),
        dental_procedures=coverage["dental"]["procedures_covered"],
        dental_cosmetic=coverage["dental"]["cosmetic_procedures"],
        vision_sub_limit=float(coverage["vision"]["sub_limit"]),
        vision_lasik=coverage["vision"]["lasik_surgery"],
        alt_medicine_sub_limit=float(coverage["alternative_medicine"]["sub_limit"]),
        alt_medicine_therapy_limit=int(coverage["alternative_medicine"]["therapy_sessions_limit"]),
        covered_treatments=coverage["alternative_medicine"]["covered_treatments"],
        covered_tests=coverage["diagnostic_tests"]["covered_tests"],
        waiting_initial=int(waiting["initial_waiting"]),
        waiting_pre_existing=int(waiting["pre_existing_diseases"]),
        waiting_maternity=int(waiting["maternity"]),
        waiting_specific={
            k: int(v) for k, v in waiting["specific_ailments"].items()
        },
        exclusions=[e.lower() for e in raw["exclusions"]],
        required_docs=raw["claim_requirements"]["documents_required"],
        submission_window_days=int(raw["claim_requirements"]["submission_timeline_days"]),
        minimum_claim_amount=float(raw["claim_requirements"]["minimum_claim_amount"]),
        network_hospitals=raw["network_hospitals"],
        cashless_available=raw["cashless_facilities"]["available"],
        instant_approval_limit=float(raw["cashless_facilities"]["instant_approval_limit"]),
        raw=raw,
    )


_policy_cache: PolicyTerms | None = None


def get_policy() -> PolicyTerms:
    global _policy_cache
    if _policy_cache is None:
        _policy_cache = _load_policy_terms()
    return _policy_cache
