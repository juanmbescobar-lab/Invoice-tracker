from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.expense import Expense
from src.services.petty_cash_service import spend


async def add_expense(
    db: AsyncSession,
    description: str,
    amount: float,
    paid_by: str,
    expense_date: date | None = None,
) -> Expense:
    """Register an expense. Returns the created expense record.

    If paid_by='petty_cash', deducts available funds from the petty cash
    balance via spend(). The expense is always recorded with its full amount
    and original paid_by value — no splitting occurs.
    """
    if amount <= 0:
        raise ValueError("Expense amount must be positive.")
    if paid_by not in ("personal", "petty_cash"):
        raise ValueError("paid_by must be 'personal' or 'petty_cash'.")

    if paid_by == "petty_cash":
        await spend(db, amount, description)

    expense = Expense(
        date=expense_date or date.today(),
        description=description,
        amount=amount,
        paid_by=paid_by,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


async def get_expenses_by_date_range(
    db: AsyncSession, start: date, end: date
) -> list[Expense]:
    """Get expenses within a date range."""
    query = (
        select(Expense)
        .where(Expense.date >= start, Expense.date <= end)
        .order_by(Expense.date)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_week_totals(db: AsyncSession, start: date, end: date) -> dict:
    """Calculate expense totals for a week, separated by payment method."""
    expenses = await get_expenses_by_date_range(db, start, end)

    personal_total = sum(e.amount for e in expenses if e.paid_by == "personal")
    petty_cash_total = sum(e.amount for e in expenses if e.paid_by == "petty_cash")

    return {
        "personal_total": round(personal_total, 2),
        "petty_cash_total": round(petty_cash_total, 2),
        "net_total": round(personal_total, 2),
        "expense_count": len(expenses),
    }
