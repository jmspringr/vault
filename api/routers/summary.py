from fastapi import APIRouter, Depends
from sqlalchemy import case, extract, func
from sqlmodel import Session, select

from api.auth import get_current_user
from api.database import get_session
from api.models import Transaction, User

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/by-category")
def spending_by_category(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Total spending (expenses only) per category, largest first."""
    total = func.sum(-Transaction.amount)
    stmt = (
        select(Transaction.category, total)
        .where(Transaction.user_id == user.id, Transaction.amount < 0)
        .group_by(Transaction.category)
        .order_by(total.desc())
    )
    return [
        {"category": category, "total": round(float(amount), 2)}
        for category, amount in session.exec(stmt).all()
    ]


@router.get("/by-month")
def income_vs_expenses_by_month(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Income and expense totals per month, oldest first."""
    year = extract("year", Transaction.date)
    month = extract("month", Transaction.date)
    income = func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0))
    expenses = func.sum(case((Transaction.amount < 0, -Transaction.amount), else_=0))
    stmt = (
        select(year, month, income, expenses)
        .where(Transaction.user_id == user.id)
        .group_by(year, month)
        .order_by(year, month)
    )
    return [
        {
            "month": f"{int(y)}-{int(m):02d}",
            "income": round(float(inc), 2),
            "expenses": round(float(exp), 2),
        }
        for y, m, inc, exp in session.exec(stmt).all()
    ]
