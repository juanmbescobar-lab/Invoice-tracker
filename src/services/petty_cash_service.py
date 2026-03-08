from datetime import date, datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.petty_cash import PettyCash


async def get_current_balance(db: AsyncSession) -> float:
    """Get the latest petty cash balance."""
    query = select(PettyCash).order_by(desc(PettyCash.id)).limit(1)
    result = await db.execute(query)
    last = result.scalar_one_or_none()
    return last.balance_after if last else 0.0


async def topup(db: AsyncSession, amount: float, description: str = "") -> PettyCash:
    """Add funds to petty cash."""
    if amount <= 0:
        raise ValueError("Topup amount must be positive.")

    current = await get_current_balance(db)
    movement = PettyCash(
        movement_type="topup",
        amount=amount,
        balance_after=current + amount,
        description=description,
    )
    db.add(movement)
    await db.commit()
    await db.refresh(movement)
    return movement


async def spend(db: AsyncSession, amount: float, description: str) -> float:
    """Spend from petty cash. Returns the amount actually deducted.

    Only spends what is available (up to the current balance). If the balance
    is zero no movement is created and 0.0 is returned. Balance never goes
    below zero.
    """
    if amount <= 0:
        raise ValueError("Spend amount must be positive.")

    current = await get_current_balance(db)
    petty_cash_spent = round(min(amount, max(current, 0.0)), 2)

    if petty_cash_spent > 0:
        movement = PettyCash(
            movement_type="expense",
            amount=petty_cash_spent,
            balance_after=round(current - petty_cash_spent, 2),
            description=description,
        )
        db.add(movement)
        await db.commit()
        await db.refresh(movement)

    return petty_cash_spent


async def get_movements(db: AsyncSession) -> list[PettyCash]:
    """Get all petty cash movements."""
    query = select(PettyCash).order_by(PettyCash.id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_weekly_summary(db: AsyncSession, start: date, end: date) -> dict:
    """Return petty cash totals and movements for a date range.

    Returns a dict with topups_total, expenses_total, net_change,
    current_balance, and a list of individual movements within the range.
    """
    all_movements = await get_movements(db)

    def _to_date(dt: datetime) -> date:
        if dt.tzinfo is not None:
            return dt.astimezone(None).date()
        return dt.date()

    week_movements = [m for m in all_movements if start <= _to_date(m.date) <= end]

    topups_total = round(
        sum(m.amount for m in week_movements if m.movement_type == "topup"), 2
    )
    expenses_total = round(
        sum(m.amount for m in week_movements if m.movement_type == "expense"), 2
    )

    return {
        "topups_total": topups_total,
        "expenses_total": expenses_total,
        "net_change": round(topups_total - expenses_total, 2),
        "current_balance": await get_current_balance(db),
        "movements": [
            {
                "type": m.movement_type,
                "amount": m.amount,
                "description": m.description,
            }
            for m in week_movements
        ],
    }
