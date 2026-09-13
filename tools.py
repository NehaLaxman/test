import json
import uuid

from datetime import datetime, date
from langchain_core.tools import tool


DB_PATH =  "18th_july_wills_ai_engineering\\projects\\BFL_CHATBOT\\bajaj_db.json"

with open(DB_PATH) as f:
    db = json.load(f)


@tool
def get_loan_status(loan_id: str) -> dict:
    """Fetches current loan status from Bajaj Finance database.

    Returns EMI amount, remaining tenure, outstanding balance,
    and next due date for the given loan account.

    Use this when the customer asks about their loan details,
    EMI, balance, or tenure.

    Args:
        loan_id: The loan account number (e.g., 'BFL2024001')
    """
    loan_id = loan_id.strip().upper()

    if loan_id not in db["loans"]:
        return {"error": f"Loan {loan_id} not found in our system. Please check the loan account number."}

    loan = db["loans"][loan_id]
    return {
        "loan_id":           loan_id,
        "customer_name":     loan["customer_name"],
        "loan_type":         loan["loan_type"],
        "emi_amount":        loan["emi"],
        "remaining_months":  loan["remaining_months"],
        "outstanding_balance": loan["outstanding_balance"],
        "next_due_date":     loan["next_due_date"],
        "interest_rate":     loan["interest_rate"],
        "total_tenure":      loan["tenure_months"],
    }



@tool
def get_emi_schedule(loan_id: str) -> dict:
    """Returns the upcoming EMI schedule (next 6 months) for a loan.

    Use this when the customer asks about their payment schedule,
    upcoming EMI dates, or future dues.

    Args:  
        loan_id: The loan account number (e.g., 'BFL2024001')
    """
    loan_id = loan_id.strip().upper()

    if loan_id not in db["loans"]:
        return {"error": f"Loan {loan_id} not found."}

    loan = db["loans"][loan_id]
    emi = loan["emi_amount"]
    next_due = datetime.strptime(loan["next_due_date"], "%Y-%m-%d")

    schedule = []
    for i in range(min(6, loan["remaining_months"])):
        month = (next_due.month + i - 1) % 12 + 1
        year  = next_due.year + (next_due.month + i - 1) // 12
        due_date = date(year, month, next_due.day)
        schedule.append({
            "installment_no": loan["paid_months"] + i + 1,
            "due_date":       str(due_date),
            "amount":         emi,
        })

    return {
        "loan_id":          loan_id,
        "customer_name":    loan["customer_name"],
        "emi_amount":       emi,
        "remaining_months": loan["remaining_months"],
        "upcoming_schedule": schedule,
    }

