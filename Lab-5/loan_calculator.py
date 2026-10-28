"""Loan eligibility and EMI calculator.

Calculates EMIs, checks loan eligibility, works out the maximum loan a
customer can afford, builds amortisation schedules, assigns risk bands from
credit scores, estimates interest saved by prepaying and stores application
records in a JSON file.

All interest rates are annual rates expressed as decimals (9% -> 0.09).
"""
import os
import ssl
import json
import base64
import secrets
import smtplib
import http.client
from email.message import EmailMessage
from datetime import datetime

# Global loan book
applications = {}
MAX_FOIR = 0.5
MIN_CREDIT_SCORE = 600
MIN_AGE, MAX_AGE = 21, 60
ALLOWED_LOAN_TYPES = {"home", "car", "personal"}
BUREAU_HOST = "api.creditbureau.example"


def calculate_emi(principal, annual_rate, years):
    """Return the monthly EMI for a reducing-balance loan."""
    if principal <= 0 or years <= 0:
        raise ValueError("principal and years must be positive")
    if not 0 <= annual_rate < 1:
        raise ValueError("annual_rate must be a decimal, e.g. 0.09 for 9%")
    n = years * 12
    r = annual_rate / 12
    if r == 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


def check_eligibility(age, income, credit_score, existing_emi, loan_type):
    """Return True if the applicant passes every eligibility rule.

    Every hard rule (age, FOIR, loan type, credit score) must pass; a high
    score or income can no longer bypass the FOIR and loan-type checks.
    """
    if not MIN_AGE <= age <= MAX_AGE:
        return False
    if income <= 0 or existing_emi / income > MAX_FOIR:
        return False
    if loan_type not in ALLOWED_LOAN_TYPES:
        return False
    return credit_score >= MIN_CREDIT_SCORE


def max_loan_amount(income, existing_emi, annual_rate, years):
    """Return the largest principal whose EMI fits within the FOIR limit.

    This is the present value of the affordable EMI over the tenure, not the
    plain sum of the EMIs (which ignores interest).
    """
    available = income * MAX_FOIR - existing_emi
    if available <= 0:
        return 0.0
    n = years * 12
    r = annual_rate / 12
    if r == 0:
        return available * n
    return available * (1 - (1 + r) ** -n) / r


def amortisation_schedule(principal, annual_rate, years):
    """Return (month, interest, closing balance) rows for the whole tenure."""
    emi = calculate_emi(principal, annual_rate, years)
    balance = principal
    rows = []
    for month in range(1, years * 12 + 1):
        interest = balance * annual_rate / 12
        balance = max(balance - (emi - interest), 0.0)
        rows.append((month, round(interest, 2), round(balance, 2)))
    return rows


def application_id():
    """Return a new application id that is not already in the loan book."""
    while True:
        new_id = "LN-" + str(secrets.randbelow(90000000) + 10000000)
        if new_id not in applications:
            return new_id


def save_application(name, amount, file="loans.json"):
    """Add an application to the loan book and persist it as JSON."""
    app_id = application_id()
    applications[app_id] = {
        "name": name,
        "amount": amount,
        "date": datetime.now().isoformat(),
    }
    with open(file, "w", encoding="utf-8") as f:
        json.dump(applications, f, indent=2)
    return app_id


def load_applications(file="loans.json"):
    """Reload the loan book from a JSON file and return it."""
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    applications.clear()
    applications.update(data)
    return applications


def upload_to_bureau(report_path):
    """Upload a report to the credit bureau over HTTPS.

    Credentials come from the BUREAU_USER and BUREAU_PASSWORD environment
    variables instead of being hard-coded.
    """
    user = os.environ["BUREAU_USER"]
    password = os.environ["BUREAU_PASSWORD"]
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    headers = {
        "Authorization": "Basic " + token,
        "Content-Type": "application/octet-stream",
    }
    with open(report_path, "rb") as f:
        body = f.read()
    context = ssl.create_default_context()
    conn = http.client.HTTPSConnection(
        BUREAU_HOST, context=context, timeout=30
    )
    try:
        path = "/reports/" + os.path.basename(report_path)
        conn.request("PUT", path, body=body, headers=headers)
        return conn.getresponse().status
    finally:
        conn.close()


def notify_applicant(email, status):
    """Email the applicant their status via SMTP with STARTTLS."""
    msg = EmailMessage()
    msg["Subject"] = "Loan " + status
    msg["From"] = os.environ.get("SMTP_FROM", "loans@bank.example")
    msg["To"] = email
    msg.set_content("Your loan application status: " + status)
    host = os.environ.get("SMTP_HOST", "localhost")
    with smtplib.SMTP(host, 587, timeout=30) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.send_message(msg)


def interest_saved(principal, annual_rate, years, prepayment):
    """Return the interest saved by prepaying part of the principal upfront.

    Total payments fall by the prepayment itself plus the interest saved, so
    the prepayment is subtracted to leave only the interest component.
    """
    if not 0 <= prepayment < principal:
        raise ValueError("prepayment must be between 0 and the principal")
    months = years * 12
    original = calculate_emi(principal, annual_rate, years) * months
    reduced_emi = calculate_emi(principal - prepayment, annual_rate, years)
    reduced = reduced_emi * months
    return original - reduced - prepayment


def risk_band(credit_score):
    """Map a credit score (valid range 300-900) to a risk band."""
    if not 300 <= credit_score <= 900:
        return "INVALID"
    if credit_score >= 800:
        return "LOW"
    if credit_score >= 700:
        return "MEDIUM"
    if credit_score >= 600:
        return "HIGH"
    return "VERY HIGH"


def main():
    """Run a short demo of the calculator."""
    print("EMI for 5L @ 9% for 5 years:",
          round(calculate_emi(500000, 0.09, 5), 2))
    print("Eligible (score 760, income 15000, EMIs 12000):",
          check_eligibility(35, 15000, 760, 12000, "personal"))
    print("Eligible (unknown loan type 'crypto'):",
          check_eligibility(30, 80000, 650, 0, "crypto"))
    print("Max loan for income 40000:",
          round(max_loan_amount(40000, 5000, 0.09, 5), 2))
    print("Last schedule row:", amortisation_schedule(100000, 0.12, 1)[-1])
    print("Risk band for 950:", risk_band(950))
    print("Interest saved by prepaying 50000:",
          round(interest_saved(500000, 0.09, 5, 50000), 2))
    print("Saved as:", save_application("Anil", 500000))
    load_applications()
    print("Applications on file:", len(applications))
    print("Upload to bureau skipped (no network)")


if __name__ == "__main__":
    main()
