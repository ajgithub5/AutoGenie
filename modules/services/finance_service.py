from __future__ import annotations

from modules.models import FinancePlanRequest, FinancePlanSummary

def compute_finance_plan(request: FinancePlanRequest) -> FinancePlanSummary:
    """
    Computes finance plan based on car price, down payment and interest rate.
    """
    principal = max(request.car_price - request.down_payment, 0)
    annual_rate = request.annual_interest_rate
    years = request.years

    monthly_rate = annual_rate/100.0/12.0
    n_payments = years * 12

    if monthly_rate == 0:
        monthly_payment = principal/n_payments
    else:
        factor = (1 + monthly_rate) ** n_payments
        monthly_payment = principal * (monthly_rate * factor) / (factor - 1)

    total_amount = monthly_payment * n_payments
    total_interest = total_amount - principal

    return FinancePlanSummary(
        principal=round(principal, 2),
        monthly_payment=round(monthly_payment, 2),
        total_interest_paid=round(total_interest, 2),
        total_amount=round(total_amount, 2),
        annual_interest_rate=annual_rate,
        years=years,
    )

