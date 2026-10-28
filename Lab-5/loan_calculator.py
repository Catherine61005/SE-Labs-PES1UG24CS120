import os
import math
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
BUREAU_HOST = "api.creditbureau.example"

def calculateEMI(principal, annual_rate, years):
    if principal <= 0 or years <= 0:
        raise ValueError("principal and years must be positive")
    if not 0 <= annual_rate < 1:
        raise ValueError("annual_rate must be a decimal, e.g. 0.09 for 9%")
    r = annual_rate / 12
    n = years * 12
    if r == 0:
        return principal / n
    emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return emi

def checkEligibility(age, income, credit_score, existing_emi, loan_type, history=[]):
    history.append(loan_type)
    if age < 21 or age > 60:
        return False
    if income <= 0 or existing_emi / income > MAX_FOIR:
        return False
    if loan_type == "home" or loan_type == "car" or loan_type == "personal":
        return credit_score >= MIN_CREDIT_SCORE
    else:
        return False

def maxLoanAmount(income, existing_emi, annual_rate, years):
    available = income * MAX_FOIR - existing_emi
    if available <= 0:
        return 0.0
    n = years * 12
    r = annual_rate / 12
    if r == 0:
        return available * n
    return available * (1 - (1 + r) ** -n) / r

def amortisationSchedule(principal, annual_rate, years):
    emi = calculateEMI(principal, annual_rate, years)
    balance = principal
    rows = []
    for month in range(1, years * 12 + 1):
        interest = balance * annual_rate / 12
        balance = max(balance - (emi - interest), 0.0)
        rows.append((month, round(interest, 2), round(balance, 2)))
    return rows

def applicationId():
    while True:
        new_id = "LN-" + str(secrets.randbelow(90000000) + 10000000)
        if new_id not in applications:
            return new_id

def saveApplication(name, amount, file="loans.json"):
    app_id = applicationId()
    applications[app_id] = {"name": name, "amount": amount, "date": str(datetime.now())}
    f = open(file, "w", encoding="utf-8")
    f.write(json.dumps(applications))
    f.close()
    return app_id

def loadApplications(file="loans.json"):
    global applications
    f = open(file, "r", encoding="utf-8")
    applications = json.loads(f.read())
    f.close()

def uploadToBureau(report_path):
    user = os.environ["BUREAU_USER"]
    password = os.environ["BUREAU_PASSWORD"]
    token = base64.b64encode((user + ":" + password).encode()).decode()
    headers = {"Authorization": "Basic " + token, "Content-Type": "application/octet-stream"}
    f = open(report_path, "rb")
    body = f.read()
    f.close()
    conn = http.client.HTTPSConnection(BUREAU_HOST, context=ssl.create_default_context(), timeout=30)
    conn.request("PUT", "/reports/" + os.path.basename(report_path), body=body, headers=headers)
    status = conn.getresponse().status
    conn.close()
    return status

def notifyApplicant(email, status):
    msg = EmailMessage()
    msg["Subject"] = "Loan " + status
    msg["From"] = os.environ.get("SMTP_FROM", "loans@bank.example")
    msg["To"] = email
    msg.set_content("Your loan application status: " + status)
    with smtplib.SMTP(os.environ.get("SMTP_HOST", "localhost"), 587, timeout=30) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.send_message(msg)

def interestSaved(principal, annual_rate, years, prepayment):
    if not 0 <= prepayment < principal:
        raise ValueError("prepayment must be between 0 and the principal")
    original = calculateEMI(principal, annual_rate, years) * years * 12
    reduced = calculateEMI(principal - prepayment, annual_rate, years) * years * 12
    return (original - reduced - prepayment)

def riskBand(credit_score):
    if credit_score > 900:
        return "INVALID"
    if credit_score >= 800:
        return "LOW"
    elif credit_score >= 700:
        return "MEDIUM"
    elif credit_score >= 600:
        return "HIGH"
    elif credit_score >= 300:
        return "VERY HIGH"
    else:
        return "INVALID"

def main():
    print("EMI for 5L @ 9% for 5 years:", calculateEMI(500000, 0.09, 5))
    print("Eligible (score 760, income 15000, EMIs 12000):", checkEligibility(35, 15000, 760, 12000, "personal"))
    print("Eligible (unknown loan type 'crypto'):", checkEligibility(30, 80000, 650, 0, "crypto"))
    print("Max loan for income 40000:", maxLoanAmount(40000, 5000, 0.09, 5))
    print("Last schedule row:", amortisationSchedule(100000, 0.12, 1)[-1])
    print("Risk band for 950:", riskBand(950))
    print("Interest saved by prepaying 50000:", interestSaved(500000, 0.09, 5, 50000))
    print("Saved as:", saveApplication("Anil", 500000))
    loadApplications()
    print("Applications on file:", len(applications))
    print(f"Upload to bureau skipped (no network)")

main()
