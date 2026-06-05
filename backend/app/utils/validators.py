"""Validation utilities — doctor registration, dates, document checks."""
import re
from datetime import date, timedelta
from thefuzz import fuzz


# Doctor registration format: [StateCode]/[Number]/[Year] e.g. KA/45678/2015
DOCTOR_REG_PATTERN = re.compile(
    r"^(?:[A-Z]{2,4}|AYUR/[A-Z]{2,4})/\d{4,6}/\d{4}$"
)


def validate_doctor_reg(reg_number: str) -> bool:
    """Check if doctor registration number matches the required format."""
    if not reg_number:
        return False
    return bool(DOCTOR_REG_PATTERN.match(str(reg_number).strip()))


def validate_doctor_reg_alt_medicine(reg_number: str) -> bool:
    """Check alternative medicine practitioner registration (e.g. AYUR/KL/2345/2019)."""
    if not reg_number:
        return False
    alt_pattern = re.compile(r"^[A-Z]{2,4}/[A-Z]{2,4}/\d{4,6}/\d{4}$")
    return bool(alt_pattern.match(str(reg_number).strip()))


def dates_match(date1: date, date2: date, tolerance_days: int = 3) -> bool:
    """Check if two dates are close enough to be considered matching."""
    diff = abs((date1 - date2).days)
    return diff <= tolerance_days


def fuzzy_name_match(name1: str, name2: str, threshold: int = 80) -> bool:
    """Fuzzy match two names (allows minor variations)."""
    if not name1 or not name2:
        return False
    n1 = name1.lower().strip()
    n2 = name2.lower().strip()
    if n1 == n2:
        return True
    ratio = fuzz.ratio(n1, n2)
    partial = fuzz.partial_ratio(n1, n2)
    return ratio >= threshold or partial >= 90


def calculate_waiting_days(join_date: date, treatment_date: date) -> int:
    """Calculate how many days have elapsed since join date."""
    return (treatment_date - join_date).days


def is_within_submission_window(treatment_date: date, submission_date: date, window_days: int = 30) -> bool:
    """Check if claim was submitted within the allowed window."""
    return (submission_date - treatment_date).days <= window_days


def is_network_hospital(hospital_name: str | None, network_list: list[str]) -> bool:
    """Fuzzy-check if the hospital is in the network list."""
    if not hospital_name:
        return False
    h = hospital_name.lower().strip()
    for net in network_list:
        if net.lower() in h or h in net.lower():
            return True
        if fuzz.ratio(h, net.lower()) >= 85:
            return True
    return False
