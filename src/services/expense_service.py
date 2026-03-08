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
) -> list[Expense]:
    """Register an expense. Returns a list of created expense records.

    If paid_by='petty_cash' and the balance is insufficient, the expense is
    split: one record for the petty_cash portion and one for the remainder
    (personal). If balance is zero, a single personal expense is created.
    """
    if amount <= 0:
        raise ValueError("Expense amount must be positive.")
    if paid_by not in ("personal", "petty_cash"):
        raise ValueError("paid_by must be 'personal' or 'petty_cash'.")

    today = expense_date or date.today()
    expenses: list[Expense] = []

    if paid_by == "petty_cash":
        petty_cash_spent, remainder = await spend(db, amount, description)

        if petty_cash_spent > 0:
            expenses.append(
                Expense(
                    date=today,
                    description=description,
                    amount=petty_cash_spent,
                    paid_by="petty_cash",
                )
            )

        if remainder > 0:
            expenses.append(
                Expense(
                    date=today,
                    description=description,
                    amount=remainder,
                    paid_by="personal",
                )
            )
    else:
        expenses.append(
            Expense(
                date=today,
                description=description,
                amount=amount,
                paid_by=paid_by,
            )
        )

    for exp in expenses:
        db.add(exp)
    await db.commit()
    for exp in expenses:
        await db.refresh(exp)

    return expenses


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
