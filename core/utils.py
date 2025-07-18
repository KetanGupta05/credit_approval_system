from math import pow
from .models import Loan
from datetime import date

def calculate_emi(principal, rate, tenure):
    r = rate / (12 * 100)
    emi = principal * r * pow(1 + r, tenure) / (pow(1 + r, tenure) - 1)
    return round(emi, 2)

def calculate_credit_score(customer):
    loans = Loan.objects.filter(customer=customer)
    score = 100

    if loans.exists():
        on_time = sum([loan.emis_paid_on_time for loan in loans])
        total_emi = sum([loan.monthly_installment for loan in loans])
        score -= (len(loans) * 2)
        score += (on_time * 1)

        current_year = date.today().year
        recent_loans = [loan for loan in loans if loan.start_date.year == current_year]
        score -= len(recent_loans) * 2

    if customer.current_debt > customer.approved_limit:
        score = 0

    return max(0, min(score, 100))