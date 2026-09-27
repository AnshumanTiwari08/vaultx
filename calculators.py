import math


def simple_interest(principal: float, annual_rate: float, years: float) -> tuple[float, float]:
    try:
        principal, annual_rate, years = map(float, (principal, annual_rate, years))
    except (TypeError, ValueError) as error:
        raise ValueError("Enter valid numbers for principal, rate and time.") from error
    if not all(math.isfinite(value) for value in (principal, annual_rate, years)):
        raise ValueError("Calculator values must be finite numbers.")
    if principal <= 0 or annual_rate < 0 or years <= 0:
        raise ValueError("Principal and time must be positive; rate cannot be negative.")
    interest = principal * annual_rate * years / 100
    return interest, principal + interest


def loan_emi(principal: float, annual_rate: float, months: int) -> float:
    try:
        principal, annual_rate, months_value = float(principal), float(annual_rate), float(months)
    except (TypeError, ValueError) as error:
        raise ValueError("Enter valid numbers for loan amount, rate and duration.") from error
    if not all(math.isfinite(value) for value in (principal, annual_rate, months_value)):
        raise ValueError("Calculator values must be finite numbers.")
    if not months_value.is_integer():
        raise ValueError("Loan duration must be a whole number of months.")
    months = int(months_value)
    if principal <= 0 or annual_rate < 0 or months <= 0:
        raise ValueError("Loan amount and duration must be positive; rate cannot be negative.")
    monthly_rate = annual_rate / 1200
    if monthly_rate == 0:
        return principal / months
    factor = (1 + monthly_rate) ** months
    return principal * monthly_rate * factor / (factor - 1)
