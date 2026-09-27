import re
from datetime import date


ACCOUNT_NUMBER_PATTERN = re.compile(r"^VX\d{10}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def required(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} is required.")
    return cleaned


def validate_email(email: str) -> str:
    email = required(email, "Email")
    if not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("Enter a valid email address.")
    return email.lower()


def validate_phone(phone: str) -> str:
    phone = required(phone, "Phone")
    digits = re.sub(r"\D", "", phone)
    if not 7 <= len(digits) <= 15:
        raise ValueError("Enter a valid phone number with 7 to 15 digits.")
    if not re.fullmatch(r"[+\d\s().-]+", phone):
        raise ValueError("Phone may contain only digits and common phone symbols.")
    return phone


def validate_dob(dob: str) -> str:
    dob = required(dob, "Date of birth")
    try:
        parsed = date.fromisoformat(dob)
    except ValueError as error:
        raise ValueError("Date of birth must use YYYY-MM-DD format.") from error
    if parsed >= date.today():
        raise ValueError("Date of birth must be in the past.")
    return parsed.isoformat()


def validate_pin(pin: str) -> str:
    if not re.fullmatch(r"\d{4,6}", pin):
        raise ValueError("PIN must contain 4 to 6 digits.")
    return pin


def validate_account_number(account_number: str) -> str:
    account_number = required(account_number, "Account number").upper()
    if not ACCOUNT_NUMBER_PATTERN.fullmatch(account_number):
        raise ValueError("Account number must be in the format VX followed by 10 digits.")
    return account_number


def validate_account_type(account_type: str) -> str:
    if account_type not in {"Savings", "Current"}:
        raise ValueError("Choose Savings or Current account type.")
    return account_type
